#!/usr/bin/env python3
"""
protocol_flow.py - Passo 2: da dove arrivano i dati che finiscono nelle primitive.

Per ogni funzione con primitive di comunicazione (passo 1) prende TUTTI gli
argomenti delle chiamate (piu' il ricevente, che descrive il "canale") e li
segue all'indietro:

  - dentro la funzione: assegnazioni, dict literal, f-string, subscript, ...
    (regola unica e indipendente dalle librerie: il risultato di una chiamata
    dipende dai suoi argomenti; json.dumps, .encode(), struct.pack... sono
    "trasparenti" e vengono solo annotati);
  - verso l'alto: un parametro dipende dagli argomenti di TUTTI i suoi
    chiamanti (usa il caller graph del passo 1), fino alle radici;
  - verso il basso: se il valore viene da una funzione del progetto, entra
    nei suoi `return` legando i parametri agli argomenti di QUELLA chiamata;
  - attributi (`self.x`): assegnazioni nella classe (e nelle basi);
  - costanti di modulo e simboli importati.

Estremita' del grafo (le foglie): costanti, valori esterni (socket.AF_UNIX,
time.time...), dati in ingresso dalla rete, parametri aperti alle radici.
Il report tiene solo estremita' e intersezioni:
  - forme dei messaggi (dict literal con i loro campi)
  - insiemi di valori assunti dai parametri (cosa "accettano" i metodi)
  - canali (gruppi di sink con lo stesso ricevente)
  - nodi e costanti condivisi da piu' sink

Uso:
    python protocol_flow.py [repo] [--json out.json] [--only SOTTOSTRINGA]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

import sink_callergraph as cg
from sink_callergraph import dotted, resolve

sys.setrecursionlimit(20000)

# Sorgenti di dati in ingresso dalla rete (prim gia' individuate al passo 1)
INBOUND = {
    "recv", "recv_into", "recvfrom", "recvmsg", "read", "read1", "readline",
    "readinto", "getresponse", "getheader", "getheaders",
    "rfile.read", "rfile.readline",
}

# Chiamate di builtin che non dicono nulla sul formato
XF_NOISE = {
    "len", "isinstance", "list", "dict", "tuple", "set", "sorted", "range",
    "min", "max", "sum", "abs", "print", "enumerate", "zip", "repr", "str",
    "bool", "float", "int", "getattr", "hasattr", "type", "super",
}

NAMED = ("param", "var", "attr")


# ---------------------------------------------------------------------------
# Fatti sintattici per funzione
# ---------------------------------------------------------------------------

def sub_slice(node: ast.Subscript):
    s = node.slice
    if type(s).__name__ == "Index":  # Python < 3.9
        return s.value
    return s


def field_name(k) -> str:
    if isinstance(k, ast.Constant):
        v = k.value
        if isinstance(v, bytes):
            v = v.decode("utf-8", "replace")
        return str(v)
    try:
        return "<" + ast.unparse(k)[:20] + ">"
    except Exception:
        return "<dyn>"


def shallow(body):
    """Nodi di un corpo, senza scendere in def/class/lambda annidate."""
    skip = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
    stack = [n for n in body if not isinstance(n, skip)]
    while stack:
        n = stack.pop()
        yield n
        for c in ast.iter_child_nodes(n):
            if not isinstance(c, skip):
                stack.append(c)


def is_self_attr(t) -> bool:
    return (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
            and t.value.id in ("self", "cls"))


class Facts:
    def __init__(self):
        self.pos_params: list = []
        self.kwonly: list = []
        self.vararg = None
        self.kwarg = None
        self.defaults: dict = {}
        self.defs: dict = defaultdict(list)       # nome -> [item]
        self.self_defs: dict = defaultdict(list)  # attributo -> [item]
        self.returns: list = []
        self.all_params: set = set()

    def target(self, t, value):
        if isinstance(t, ast.Name):
            self.defs[t.id].append(("expr", value))
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                self.target(e, value)
        elif isinstance(t, ast.Starred):
            self.target(t.value, value)
        elif isinstance(t, ast.Subscript):
            item = ("set", sub_slice(t), value)
            if isinstance(t.value, ast.Name):
                self.defs[t.value.id].append(item)
            elif is_self_attr(t.value):
                self.self_defs[t.value.attr].append(item)
        elif isinstance(t, ast.Attribute):
            if is_self_attr(t):
                self.self_defs[t.attr].append(("expr", value))
            elif isinstance(t.value, ast.Name):
                self.defs[t.value.id].append(("expr", value))


def build_facts(node) -> Facts:
    f = Facts()
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = node.args
        f.pos_params = [x.arg for x in list(a.posonlyargs) + list(a.args)]
        f.kwonly = [x.arg for x in a.kwonlyargs]
        f.vararg = a.vararg.arg if a.vararg else None
        f.kwarg = a.kwarg.arg if a.kwarg else None
        for name, d in zip(reversed(f.pos_params), reversed(a.defaults)):
            f.defaults[name] = d
        for name, d in zip(f.kwonly, a.kw_defaults):
            if d is not None:
                f.defaults[name] = d
        f.all_params = set(f.pos_params) | set(f.kwonly)
        if f.vararg:
            f.all_params.add(f.vararg)
        if f.kwarg:
            f.all_params.add(f.kwarg)
    for n in shallow(node.body):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                f.target(t, n.value)
        elif isinstance(n, ast.AnnAssign) and n.value is not None:
            f.target(n.target, n.value)
        elif isinstance(n, ast.AugAssign):
            f.target(n.target, n.value)
        elif isinstance(n, (ast.For, ast.AsyncFor)):
            f.target(n.target, n.iter)
        elif isinstance(n, (ast.With, ast.AsyncWith)):
            for it in n.items:
                if it.optional_vars is not None:
                    f.target(it.optional_vars, it.context_expr)
        elif isinstance(n, ast.NamedExpr):
            f.target(n.target, n.value)
        elif isinstance(n, ast.comprehension):
            f.target(n.target, n.iter)
        elif isinstance(n, ast.Return) and n.value is not None:
            f.returns.append(n.value)
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "update"
              and isinstance(n.func.value, ast.Name)):
            # d.update(x) / d.update(k=v) / h.update(data): l'oggetto dipende da x
            base = n.func.value.id
            for arg in n.args:
                f.defs[base].append(("update", arg))
            for kw in n.keywords:
                if kw.arg is None:
                    f.defs[base].append(("update", kw.value))
                else:
                    f.defs[base].append(("set", ast.Constant(kw.arg), kw.value))
    return f


class Frame:
    """Contesto di valutazione: funzione + catena di chiamate + ambiente.

    env is None  -> "modo salita": i parametri risalgono ai chiamanti.
    env is dict  -> "modo discesa": i parametri sono legati agli argomenti
                    di una chiamata precisa (nessun mescolamento tra chiamanti).
    """
    __slots__ = ("fid", "ctx", "env")

    def __init__(self, fid, ctx=(), env=None):
        self.fid = fid
        self.ctx = ctx
        self.env = env


# ---------------------------------------------------------------------------
# Analisi
# ---------------------------------------------------------------------------

def short(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def fid_short(fid: str) -> str:
    rel, _, qual = fid.partition(":")
    return f"{Path(rel).name}:{qual}"


class FlowAnalyzer:
    def __init__(self, project, kinds, strict, max_ctx, descend_fuzzy,
                 fuzzy_sites, max_nodes, only):
        self.p = project
        self.kinds = kinds
        self.strict = strict
        self.max_ctx = max_ctx
        self.descend_fuzzy = descend_fuzzy
        self.fuzzy_sites = fuzzy_sites
        self.max_nodes = max_nodes
        self.only = only

        self.nodes: dict = {}
        self.edges: dict = defaultdict(set)
        self.fields: dict = defaultdict(lambda: defaultdict(set))
        self.chan: dict = {}
        self.sink_prims: dict = {}
        self.truncated = False

        self._facts: dict = {}
        self.memo: dict = {}
        self.active: set = set()
        self._rc: dict = {}

        self.prim_by_node = {id(x.node): x for x in project.prims
                             if x.node is not None}
        self.site_by_node = {id(cs.node): cs for cs in project.callsites}
        self.self_defs = defaultdict(lambda: defaultdict(list))
        self.class_defs = defaultdict(lambda: defaultdict(list))
        self._index_classes()

    # -- indici -----------------------------------------------------------
    def _index_classes(self):
        for fi in self.p.funcs.values():
            if fi.cls and fi.node is not None:
                for attr, items in self.facts(fi.id).self_defs.items():
                    for it in items:
                        self.self_defs[(fi.rel, fi.cls)][attr].append((fi.id, it))
        for rel, tree in self.p.trees.items():
            for n in ast.walk(tree):
                if not isinstance(n, ast.ClassDef):
                    continue
                for st in n.body:
                    pairs = []
                    if isinstance(st, ast.Assign):
                        pairs = [(t, st.value) for t in st.targets]
                    elif isinstance(st, ast.AnnAssign) and st.value is not None:
                        pairs = [(st.target, st.value)]
                    for t, v in pairs:
                        if isinstance(t, ast.Name):
                            self.class_defs[(rel, n.name)][t.id].append(
                                (f"{rel}:<module>", ("expr", v)))

    def facts(self, fid) -> Facts:
        f = self._facts.get(fid)
        if f is None:
            fi = self.p.funcs.get(fid)
            node = fi.node if fi is not None else None
            if node is None and fid.endswith(":<module>"):
                node = self.p.trees.get(self.rel_of(fid))
            f = build_facts(node) if node is not None else Facts()
            self._facts[fid] = f
        return f

    @staticmethod
    def rel_of(fid):
        return fid.partition(":")[0]

    def enclosing(self, fid):
        rel, _, qual = fid.partition(":")
        out = []
        while "." in qual:
            qual = qual.rpartition(".")[0]
            f = f"{rel}:{qual}"
            if f in self.p.funcs:
                out.append(f)
        return out

    def class_of(self, fid):
        fi = self.p.funcs.get(fid)
        if fi and fi.cls:
            return fi.cls
        for outer in self.enclosing(fid):
            fo = self.p.funcs.get(outer)
            if fo and fo.cls:
                return fo.cls
        return None

    # -- nodi -------------------------------------------------------------
    def node(self, nid, kind, label, loc=None):
        if nid not in self.nodes:
            self.nodes[nid] = {"kind": kind, "label": label, "loc": loc}
        return nid

    def const(self, value):
        if value is None or value is Ellipsis:
            return None
        if isinstance(value, (str, bytes)) and len(value) == 0:
            return None
        r = repr(value)
        return self.node(f"const:{type(value).__name__}:{r}", "const", short(r, 48))

    def too_big(self):
        if len(self.nodes) > self.max_nodes:
            self.truncated = True
            return True
        return False

    @staticmethod
    def ctx_suffix(fr):
        return ("#" + ">".join(fr.ctx)) if fr.ctx else ""

    # -- slicing ----------------------------------------------------------
    def slice(self, e, fr) -> set:
        if e is None:
            return set()
        if isinstance(e, ast.Constant):
            c = self.const(e.value)
            return {c} if c else set()
        if isinstance(e, ast.Name):
            return self.slice_name(e.id, fr)
        if isinstance(e, ast.Attribute):
            return self.slice_attr(e, fr)
        if isinstance(e, ast.Subscript):
            return self.slice(e.value, fr) | self.slice(sub_slice(e), fr)
        if isinstance(e, ast.Call):
            return self.slice_call(e, fr)
        if isinstance(e, ast.Dict):
            return self.slice_dict(e, fr)
        if isinstance(e, ast.Lambda):
            return set()
        out: set = set()
        for ch in ast.iter_child_nodes(e):
            if isinstance(ch, ast.expr):
                out |= self.slice(ch, fr)
            elif isinstance(ch, ast.comprehension):
                out |= self.slice(ch.iter, fr)
        return out

    def slice_dict(self, e, fr):
        rel = self.rel_of(fr.fid)
        sid = f"shape:{rel}:{e.lineno}:{e.col_offset}{self.ctx_suffix(fr)}"
        if sid in self.nodes:
            return {sid}
        self.node(sid, "shape", "{…}", loc=f"{Path(rel).name}:{e.lineno}")
        fields = self.fields[sid]
        for k, v in zip(e.keys, e.values):
            name = "**" if k is None else field_name(k)
            fields[name] |= self.slice(v, fr)
        for deps in fields.values():
            self.edges[sid] |= deps
        return {sid}

    def eval_defs(self, items, fr, key):
        """Unisce le definizioni di una variabile/attributo.

        d = {...}; d["k"] = v; d.update(x)  ->  i campi finiscono nella stessa
        forma, cosi' il messaggio resta un unico oggetto.
        """
        deps: set = set()
        upd: set = set()
        sets = []
        for it in items:
            if it[0] == "expr":
                deps |= self.slice(it[1], fr)
            elif it[0] == "update":
                upd |= self.slice(it[1], fr)
            else:
                sets.append(it)
        targets = [d for d in deps
                   if self.kind(d) == "shape" and not d.startswith("shape:mut:")]
        shape_upd = [u for u in upd if self.kind(u) == "shape"]
        if not targets and (sets or shape_upd):
            msid = f"shape:mut:{key}{self.ctx_suffix(fr)}"
            self.node(msid, "shape", "{…}",
                      loc=f"{Path(self.rel_of(fr.fid)).name}:{key.split(':', 1)[-1]}")
            deps.add(msid)
            targets = [msid]
        for t in targets:
            for u in shape_upd:
                for f, ds in self.fields[u].items():
                    self.fields[t][f] |= ds
            for it in sets:
                self.fields[t][field_name(it[1])] |= self.slice(it[2], fr)
            for ds in self.fields[t].values():
                self.edges[t] |= ds
        deps |= {u for u in upd if self.kind(u) != "shape"}
        return deps

    def slice_name(self, name, fr):
        if name in ("self", "cls"):
            return set()
        facts = self.facts(fr.fid)
        if name in facts.all_params:
            return self.slice_param(name, fr)
        if name in facts.defs:
            return self.slice_var(name, fr)
        rel = self.rel_of(fr.fid)
        for outer in self.enclosing(fr.fid):
            of = self.facts(outer)
            if name in of.all_params or name in of.defs:
                return self.slice_name(name, Frame(outer))
        mf = f"{rel}:<module>"
        if fr.fid != mf and name in self.facts(mf).defs:
            return self.slice_var(name, Frame(mf))
        target = self.p.imports.get(rel, {}).get(name)
        if target and "." in target:
            return self.slice_imported(target)
        return set()

    def slice_imported(self, full):
        mod, _, sym = full.rpartition(".")
        if mod:
            rels = self.p.files_for_module(mod)
            for r in sorted(rels):
                mf = f"{r}:<module>"
                if sym in self.facts(mf).defs:
                    return self.slice_var(sym, Frame(mf))
            if rels and (self.p.find_top(sym, rels) or sym in self.p.classes):
                return set()  # funzione/classe del progetto, non un valore
        return {self.node(f"ext:{full}", "ext", full)}

    def slice_var(self, name, fr):
        items = self.facts(fr.fid).defs[name]
        key = f"{fr.fid}:{name}"
        if fr.env is None:
            nid = f"var:{key}"
            if nid in self.nodes:
                return {nid}
            if self.too_big():
                return set()
            qual = fr.fid.partition(":")[2]
            fname = Path(self.rel_of(fr.fid)).name
            self.node(nid, "var", f"{fname}:{name}" if qual == "<module>"
                      else f"{fname}:{qual}.{name}")
            self.edges[nid] |= self.eval_defs(items, fr, key)
            return {nid}
        mkey = ("var", fr.fid, fr.ctx, name)
        if mkey in self.memo:
            return self.memo[mkey]
        if mkey in self.active:
            return set()
        self.active.add(mkey)
        res = self.eval_defs(items, fr, key)
        self.active.discard(mkey)
        self.memo[mkey] = res
        return res

    def bind_args(self, fi, facts, call):
        params = list(facts.pos_params)
        if fi.cls is not None and params and params[0] in ("self", "cls"):
            params = params[1:]
        allkw = set(params) | set(facts.kwonly)
        mapping = defaultdict(list)
        pos = [a.value if isinstance(a, ast.Starred) else a for a in call.args]
        for i, a in enumerate(pos):
            if i < len(params):
                mapping[params[i]].append(a)
            elif facts.vararg:
                mapping[facts.vararg].append(a)
        kwextra = []
        for kw in call.keywords:
            if kw.arg is not None and kw.arg in allkw:
                mapping[kw.arg].append(kw.value)
            elif facts.kwarg:
                kwextra.append((kw.arg, kw.value))
        return mapping, kwextra

    def kwargs_shape(self, kwextra, fr, key):
        """**kwargs di una chiamata come forma {nome: valore}."""
        sid = f"shape:kw:{key}{self.ctx_suffix(fr)}"
        if sid not in self.nodes:
            self.node(sid, "shape", "{…}", loc=key)
            for name, ex in kwextra:
                self.fields[sid]["**" if name is None else name] |= self.slice(ex, fr)
            for ds in self.fields[sid].values():
                self.edges[sid] |= ds
        return {sid}

    def slice_param(self, name, fr):
        facts = self.facts(fr.fid)
        d = facts.defaults.get(name)
        if fr.env is not None:  # discesa: legato agli argomenti della chiamata
            if name in fr.env:
                return fr.env[name]
            return self.slice(d, Frame(fr.fid, fr.ctx, fr.env)) if d is not None else set()
        nid = f"param:{fr.fid}:{name}"
        if nid in self.nodes:
            return {nid}
        if self.too_big():
            return set()
        qual = fr.fid.partition(":")[2]
        self.node(nid, "param", f"{Path(self.rel_of(fr.fid)).name}:{qual}({name})")
        fi = self.p.funcs.get(fr.fid)
        sites = [(cs, conf) for cs, conf in self.p.sites_to.get(fr.fid, [])
                 if self.fuzzy_sites or conf != "fuzzy"]
        deps: set = set()
        if fi is not None:
            for cs, _ in sites:
                mapping, kwextra = self.bind_args(fi, facts, cs.node)
                cf = Frame(cs.caller)
                if name == facts.kwarg:
                    if kwextra:
                        key = f"{Path(cs.rel).name}:{cs.node.lineno}:{cs.node.col_offset}"
                        deps |= self.kwargs_shape(kwextra, cf, key)
                    continue
                for ex in mapping.get(name, ()):
                    deps |= self.slice(ex, cf)
        if d is not None:
            deps |= self.slice(d, Frame(fr.fid))
        if not sites:
            deps.add(self.node(f"open:{fr.fid}:{name}", "open",
                               f"input {fid_short(fr.fid)}({name})"))
        self.edges[nid] |= deps
        return {nid}

    def attr_defs(self, cls, rel, attr, seen=None):
        seen = seen if seen is not None else set()
        if (rel, cls) in seen:
            return []
        seen.add((rel, cls))
        out = list(self.self_defs[(rel, cls)].get(attr, []))
        out += self.class_defs[(rel, cls)].get(attr, [])
        for ci in self.p.classes.get(cls, []):
            if ci.rel != rel:
                continue
            for b in ci.bases:
                bname = b.rsplit(".", 1)[-1]
                for bci in self.p.classes.get(bname, []):
                    out += self.attr_defs(bci.name, bci.rel, attr, seen)
        return out

    def slice_self_attr(self, cls, rel, attr):
        nid = f"attr:{rel}:{cls}.{attr}"
        if nid in self.nodes:
            return {nid}
        defs = self.attr_defs(cls, rel, attr)
        if not defs or self.too_big():
            return set()
        self.node(nid, "attr", f"{Path(rel).name}:{cls}.{attr}")
        by_owner = defaultdict(list)
        for owner, it in defs:
            by_owner[owner].append(it)
        for owner, items in by_owner.items():
            self.edges[nid] |= self.eval_defs(items, Frame(owner), f"{rel}:{cls}.{attr}")
        return {nid}

    def slice_attr(self, e, fr):
        pm = self.prim_by_node.get(id(e))
        if pm is not None and pm.kind == "io":
            return {self.node(f"in:{pm.lib}.{pm.prim}", "in", f"{pm.lib}.{pm.prim}")}
        rel = self.rel_of(fr.fid)
        d = dotted(e)
        base = e.value
        if isinstance(base, ast.Name) and base.id in ("self", "cls"):
            cls = self.class_of(fr.fid)
            return self.slice_self_attr(cls, rel, e.attr) if cls else set()
        if d:
            head = d.split(".")[0]
            facts = self.facts(fr.fid)
            local = head in facts.all_params or head in facts.defs
            imports = self.p.imports.get(rel, {})
            if head in imports and not local:
                return self.slice_imported(resolve(d, imports))
        return self.slice(base, fr)

    def xform(self, call, fr):
        d = dotted(call.func)
        rel = self.rel_of(fr.fid)
        imports = self.p.imports.get(rel, {})
        facts = self.facts(fr.fid)
        if d:
            head = d.split(".")[0]
            if head in imports and head not in facts.all_params and head not in facts.defs:
                label = resolve(d, imports)
            elif "." in d:
                attr = d.rsplit(".", 1)[-1]
                if attr in cg.COMMON_NOISE:
                    return None
                label = "." + attr
            else:
                if d in XF_NOISE:
                    return None
                label = d
        elif isinstance(call.func, ast.Attribute):
            if call.func.attr in cg.COMMON_NOISE:
                return None
            label = "." + call.func.attr
        else:
            return None
        return self.node(f"xf:{label}", "xf", label)

    def slice_call(self, call, fr):
        pm = self.prim_by_node.get(id(call))
        if pm is not None and pm.kind == "io" and pm.prim in INBOUND:
            return {self.node(f"in:{pm.lib}.{pm.prim}", "in", f"{pm.lib}.{pm.prim}")}
        rel = self.rel_of(fr.fid)
        cs = self.site_by_node.get(id(call))
        cls = cs.cls if cs else self.class_of(fr.fid)
        d = dotted(call.func)

        if d == "dict" and call.keywords and not call.args:
            sid = f"shape:{rel}:{call.lineno}:{call.col_offset}{self.ctx_suffix(fr)}"
            if sid not in self.nodes:
                self.node(sid, "shape", "{…}", loc=f"{Path(rel).name}:{call.lineno}")
                for kw in call.keywords:
                    name = "**" if kw.arg is None else kw.arg
                    self.fields[sid][name] |= self.slice(kw.value, fr)
                for deps in self.fields[sid].values():
                    self.edges[sid] |= deps
            return {sid}

        allowed = ("exact", "import") + (("fuzzy",) if self.descend_fuzzy else ())
        targets = [f for f, conf in
                   self.p.resolve_target(call.func, rel, cls, self.descend_fuzzy)
                   if conf in allowed]
        out: set = set()
        used = False
        if targets and len(fr.ctx) < self.max_ctx:
            site = f"{Path(rel).name}:{call.lineno}:{call.col_offset}"
            if site not in fr.ctx:
                for t in targets:
                    res = self.descend(t, call, fr, site)
                    if res:
                        out |= res
                        used = True
        if not used:
            for a in call.args:
                out |= self.slice(a.value if isinstance(a, ast.Starred) else a, fr)
            for kw in call.keywords:
                out |= self.slice(kw.value, fr)
            if isinstance(call.func, ast.Attribute):
                out |= self.slice(call.func.value, fr)
            if not targets:
                xf = self.xform(call, fr)
                if xf:
                    out.add(xf)
        return out

    def descend(self, t, call, fr, site):
        key = ("ret", t.id, fr.ctx + (site,))
        if key in self.memo:
            return self.memo[key]
        if key in self.active:
            return set()
        facts = self.facts(t.id)
        mapping, kwextra = self.bind_args(t, facts, call)
        env = {}
        for name, exprs in mapping.items():
            s: set = set()
            for x in exprs:
                s |= self.slice(x, fr)
            env[name] = s
        if facts.kwarg:
            env[facts.kwarg] = (self.kwargs_shape(kwextra, fr, site)
                                if kwextra else set())
        nf = Frame(t.id, fr.ctx + (site,), env)
        self.active.add(key)
        res: set = set()
        for r in facts.returns:
            res |= self.slice(r, nf)
        self.active.discard(key)
        self.memo[key] = res
        return res

    # -- sink -------------------------------------------------------------
    def run(self):
        by_func = defaultdict(list)
        for pm in self.p.prims:
            if pm.kind not in self.kinds:
                continue
            if self.strict and pm.conf != "bound":
                continue
            if self.only and not any(o in pm.func for o in self.only):
                continue
            by_func[pm.func].append(pm)
        for fid, prims in sorted(by_func.items()):
            sid = f"sink:{fid}"
            self.node(sid, "sink", fid)
            fr = Frame(fid)
            data: set = set()
            chan: set = set()
            for pm in prims:
                call = pm.node
                if not isinstance(call, ast.Call):
                    continue
                exprs = [a.value if isinstance(a, ast.Starred) else a for a in call.args]
                exprs += [k.value for k in call.keywords]
                for ex in exprs:
                    data |= self.slice(ex, fr)
                if not pm.prim.startswith("<create") and isinstance(call.func, ast.Attribute):
                    chan |= self.slice(call.func.value, fr)
            self.edges[sid] |= data
            self.chan[sid] = chan
            self.sink_prims[sid] = prims

    # -- analisi del grafo -------------------------------------------------
    def kind(self, nid):
        return self.nodes[nid]["kind"]

    def label(self, nid):
        return self.nodes[nid]["label"]

    def cone(self, starts, into_shapes=False):
        """Nodi raggiungibili; le forme sono terminali salvo into_shapes."""
        seen: set = set()
        stack = list(starts)
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            if self.kind(n) == "shape" and not into_shapes:
                continue
            stack.extend(self.edges.get(n, ()))
        return seen

    def reach_consts(self, nid):
        r = self._rc.get(nid)
        if r is None:
            r = {n for n in self.cone(self.edges.get(nid, ())) if self.kind(n) == "const"}
            self._rc[nid] = r
        return r

    def summarize(self, deps, depth=0):
        order = {"const": 0, "ext": 1, "in": 2, "open": 3, "param": 4,
                 "var": 4, "attr": 4, "shape": 5}
        items = []
        for d in sorted((x for x in deps if self.kind(x) != "xf"),
                        key=lambda x: (order.get(self.kind(x), 9), self.label(x))):
            k, lab = self.kind(d), self.label(d)
            if k == "const":
                items.append(lab)
            elif k == "shape":
                items.append(self.shape_sig(d, depth + 1) if depth < 1 else "{…}")
            elif k in ("ext", "in", "open"):
                items.append(f"‹{lab}›")
            else:
                cs = sorted(self.label(c) for c in self.reach_consts(d))
                ins = sorted({self.label(n) for n in self.cone([d])
                              if self.kind(n) == "in"})
                if ins:
                    items.append("‹in " + ",".join(ins) + "›"
                                 + (f"({'|'.join(cs[:3])})" if cs else ""))
                elif 1 <= len(cs) <= 6:
                    items.append(f"‹{lab}›∈{{{'|'.join(cs)}}}")
                else:
                    items.append(f"‹{lab}›")
        if len(items) > 5:
            items = items[:5] + [f"+{len(items) - 5}"]
        return " | ".join(items) if items else "?"

    def shape_sig(self, sid, depth=0):
        fields = self.fields.get(sid, {})
        parts = [f"{k}: {self.summarize(fields[k], depth)}" for k in sorted(fields)]
        return "{" + ", ".join(parts) + "}"

    def analyze(self):
        sinks = sorted(self.sink_prims)
        S = defaultdict(set)
        cones = {}
        for s in sinks:
            c = self.cone(self.edges.get(s, ()))
            cones[s] = c
            for n in self.cone(self.edges.get(s, ()), into_shapes=True):
                S[n].add(s)
        rev = defaultdict(set)
        for a, bs in self.edges.items():
            for b in bs:
                rev[b].add(a)
        self.S, self.cones, self.rev = S, cones, rev

    def joins(self):
        out = []
        for n, ss in self.S.items():
            if len(ss) < 2:
                continue
            if any(self.S.get(p) == ss for p in self.rev[n]):
                continue
            out.append(n)
        return out

    def channels(self):
        groups = defaultdict(list)
        for sid in self.sink_prims:
            named = sorted(n for n in self.chan.get(sid, ()) if self.kind(n) in NAMED)
            if named:
                key = tuple(named)
            else:
                fi = self.p.funcs.get(sid[len("sink:"):])
                if any(x.lib == "http.server" for x in self.sink_prims[sid]) and fi:
                    key = (f"handler:{fi.rel}:{fi.cls or '?'}",)
                else:
                    key = ("<senza ricevente>",)
            groups[key].append(sid)
        return groups

    # -- report -------------------------------------------------------------
    def render(self, limit):
        L: list = []

        def cap(items, n=limit):
            items = list(items)
            return items[:n], max(0, len(items) - n)

        kinds = defaultdict(int)
        for nd in self.nodes.values():
            kinds[nd["kind"]] += 1
        n_edges = sum(len(v) for v in self.edges.values())
        L += ["# Snapshot del protocollo (passo 2)", ""]
        L.append(f"- Sink analizzati: {len(self.sink_prims)}")
        L.append("- Nodi: " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
                 + f" · archi: {n_edges}")
        if self.truncated:
            L.append(f"- ATTENZIONE: troncato a {self.max_nodes} nodi (--max-nodes)")
        L.append("")

        # Canali
        L += ["## Canali (sink con lo stesso ricevente)", ""]
        for i, (key, sinks) in enumerate(sorted(self.channels().items()), 1):
            names = []
            desc = set()
            for k in key:
                if k in self.nodes:
                    names.append(self.label(k))
                    for n in self.cone([k]):
                        if self.kind(n) in ("const", "ext"):
                            desc.add(self.label(n))
                        elif self.kind(n) == "xf":
                            desc.add(self.label(n) + "()")
                else:
                    names.append(k)
            L.append(f"- **C{i}** `{' + '.join(names)}`"
                     + (f" — {', '.join(sorted(desc))}" if desc else ""))
            shown, more = cap(sinks)
            for s in shown:
                ps = sorted({f"{x.lib}.{x.prim}" for x in self.sink_prims[s]})
                L.append(f"  - `{fid_short(self.label(s))}` ({', '.join(ps)})")
            if more:
                L.append(f"  - … +{more}")
        L.append("")

        # Forme dei messaggi
        sig_sinks = defaultdict(set)
        sig_locs = defaultdict(set)
        for s in sorted(self.sink_prims):
            for n in self.cones[s]:
                if self.kind(n) == "shape":
                    sig = self.shape_sig(n)
                    sig_sinks[sig].add(s)
                    if self.nodes[n]["loc"]:
                        sig_locs[sig].add(self.nodes[n]["loc"])
        L += ["## Forme dei messaggi (dict che arrivano ai sink)", ""]
        shown, more = cap(sorted(sig_sinks, key=lambda g: (-len(sig_sinks[g]), g)), limit * 3)
        for sig in shown:
            locs = ", ".join(sorted(sig_locs[sig])[:3])
            sk = ", ".join(f"`{fid_short(self.label(s))}`" for s in sorted(sig_sinks[sig])[:3])
            L.append(f"- `{short(sig, 200)}` — {sk}" + (f" — {locs}" if locs else ""))
        if more:
            L.append(f"- … +{more}")
        if not sig_sinks:
            L.append("_nessuna_")
        L.append("")

        # Insiemi di valori dei parametri
        L += ["## Cosa accettano i parametri (valori costanti che possono assumere)", ""]
        rows = []
        for nid, nd in self.nodes.items():
            if nd["kind"] != "param" or nid not in self.S:
                continue
            cs = sorted(self.label(c) for c in self.reach_consts(nid))
            if len(cs) >= 2:
                rows.append((nd["label"], cs, len(self.S[nid])))
        rows.sort(key=lambda r: (-len(r[1]), r[0]))
        shown, more = cap(rows, limit * 2)
        for lab, cs, _ in shown:
            vals, extra = cs[:8], max(0, len(cs) - 8)
            L.append(f"- `{lab}` ∈ {{{' | '.join(vals)}{f' | +{extra}' if extra else ''}}}")
        if more:
            L.append(f"- … +{more}")
        if not rows:
            L.append("_nessuno_")
        L.append("")

        # Dettaglio per sink
        L += ["## Sink", ""]
        for s in sorted(self.sink_prims):
            fid = s[len("sink:"):]
            ps = sorted({f"{x.lib}.{x.prim}@L{x.line}" for x in self.sink_prims[s]})
            L.append(f"### `{fid_short(fid)}` — {', '.join(ps[:6])}")
            cone = self.cones[s]
            by = defaultdict(list)
            for n in cone:
                by[self.kind(n)].append(n)
            xf = sorted(self.label(n) for n in by["xf"])
            if xf:
                L.append(f"- via: {', '.join(xf)}")
            loose = sorted(self.label(n) for n in by["const"]
                           if self.label(n) not in ("True", "False"))
            if loose:
                v, extra = loose[:limit], max(0, len(loose) - limit)
                L.append(f"- costanti dirette: {', '.join(v)}" + (f" (+{extra})" if extra else ""))
            ext = sorted(self.label(n) for n in by["ext"])
            if ext:
                L.append(f"- esterni: {', '.join(ext[:limit])}")
            ins = sorted(self.label(n) for n in by["in"])
            if ins:
                L.append(f"- dalla rete: {', '.join(ins)}")
            ops = sorted(self.label(n) for n in by["open"])
            if ops:
                v, extra = ops[:limit], max(0, len(ops) - limit)
                L.append(f"- input aperti alle radici: {', '.join(v)}" + (f" (+{extra})" if extra else ""))
            sh = len(by["shape"])
            if sh:
                L.append(f"- forme: {sh} (vedi sopra)")
            L.append("")

        # Intersezioni
        js = self.joins()
        named = [n for n in js if self.kind(n) in NAMED or self.kind(n) == "shape"]
        leaves = [n for n in js if self.kind(n) in ("const", "ext", "in", "open")
                  and self.label(n) not in ("True", "False")]
        L += ["## Intersezioni (nodi condivisi da piu' sink)", ""]
        named.sort(key=lambda n: (-len(self.S[n]), self.label(n)))
        shown, more = cap(named)
        for n in shown:
            sk = ", ".join(f"`{fid_short(self.label(x))}`" for x in sorted(self.S[n])[:4])
            what = self.label(n) if self.kind(n) != "shape" else short(self.shape_sig(n), 120)
            L.append(f"- {self.kind(n)} `{what}` → {len(self.S[n])} sink: {sk}")
        if more:
            L.append(f"- … +{more}")
        if not named:
            L.append("_nessun nodo con nome condiviso_")
        L.append("")
        L += ["### Valori condivisi", ""]
        leaves.sort(key=lambda n: (-len(self.S[n]), self.label(n)))
        shown, more = cap(leaves, limit * 2)
        for n in shown:
            sk = ", ".join(f"`{fid_short(self.label(x))}`" for x in sorted(self.S[n])[:4])
            L.append(f"- {self.kind(n)} {self.label(n)} → {len(self.S[n])} sink: {sk}")
        if more:
            L.append(f"- … +{more}")
        if not leaves:
            L.append("_nessuno_")
        L.append("")
        return L

    def dump(self):
        return {
            "nodes": self.nodes,
            "edges": {k: sorted(v) for k, v in self.edges.items()},
            "fields": {k: {f: sorted(v) for f, v in fs.items()}
                       for k, fs in self.fields.items()},
            "sinks": {s: [{k: v for k, v in x.__dict__.items() if k != "node"}
                          for x in ps] for s, ps in self.sink_prims.items()},
            "channel": {s: sorted(c) for s, c in self.chan.items()},
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Passo 2: flusso dei dati verso le primitive.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--kinds", default="io,lifecycle,setup")
    ap.add_argument("--strict", action="store_true",
                    help="solo primitive legate a una risorsa nota")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--only", action="append", default=[],
                    help="analizza solo i sink il cui id contiene la stringa")
    ap.add_argument("--max-ctx", type=int, default=3,
                    help="profondita' massima di discesa nei return (default 3)")
    ap.add_argument("--descend-fuzzy", action="store_true",
                    help="scendi nei return anche per chiamate risolte 'fuzzy'")
    ap.add_argument("--no-fuzzy-sites", action="store_true",
                    help="i parametri risalgono solo ai chiamanti exact/import")
    ap.add_argument("--max-fuzzy", type=int, default=6)
    ap.add_argument("--max-nodes", type=int, default=50000)
    ap.add_argument("--limit", type=int, default=12, help="voci per lista nel report")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        raise SystemExit(f"error: non esiste: {repo}")
    project = cg.build_project(repo, cg.EXCLUDES | set(args.exclude),
                               args.no_tests, args.max_fuzzy)
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    fa = FlowAnalyzer(project, kinds, args.strict, args.max_ctx,
                      args.descend_fuzzy, not args.no_fuzzy_sites,
                      args.max_nodes, args.only)
    fa.run()
    fa.analyze()
    print("\n".join(fa.render(args.limit)))
    if args.json:
        Path(args.json).write_text(json.dumps(fa.dump(), indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()