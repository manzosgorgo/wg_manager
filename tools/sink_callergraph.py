#!/usr/bin/env python3
"""
comm_callgraph.py - Passo 1: dove si comunica davvero e chi ci arriva.

1. Trova TUTTI E SOLI i file che importano socket, http.client, http.server.
2. In quei file trova le funzioni che usano le primitive di comunicazione
   (send, sendall, recv, request, wfile.write, send_header, ...).
3. Costruisce il caller graph su tutto il progetto e, per ogni funzione con
   primitive, risale i chiamanti fino alle radici (main, <module>, handler
   senza chiamanti, ...).

Solo analisi statica con `ast`: il codice analizzato non viene mai eseguito.
La risoluzione delle chiamate e' per nome (Python e' dinamico), quindi ogni
arco ha una confidenza: exact | import | ref | fuzzy.

Uso:
    python comm_callgraph.py [repo] [--json out.json] [--strict]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

EXCLUDES = {
    ".git", ".idea", ".venv", "venv", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build", "coverage", "site-packages",
    "login", "tests"
}

LIBS = ("socket", "http.client", "http.server")

# Espressioni che creano una risorsa di comunicazione.
CREATORS = {
    "socket.socket": "socket",
    "socket.create_connection": "socket",
    "socket.create_server": "socket",
    "socket.fromfd": "socket",
    "http.client.HTTPConnection": "http.client",
    "http.client.HTTPSConnection": "http.client",
    "http.server.HTTPServer": "http.server",
    "http.server.ThreadingHTTPServer": "http.server",
}
# Creano una tupla: (kind, quali elementi sono risorse)
TUPLE_CREATORS = {
    "socket.socketpair": ("socket", "all"),
}

# Primitive sugli oggetti-risorsa: nome metodo -> tipo
#   io = scambia dati / header ; lifecycle = chiusura/fine ; setup = apertura
PRIMS = {
    "socket": {
        "send": "io", "sendall": "io", "sendto": "io", "sendmsg": "io",
        "sendfile": "io", "recv": "io", "recv_into": "io", "recvfrom": "io",
        "recvmsg": "io", "makefile": "io",
        "close": "lifecycle", "shutdown": "lifecycle", "detach": "lifecycle",
        "connect": "setup", "connect_ex": "setup", "bind": "setup",
        "listen": "setup", "accept": "setup",
    },
    "http.client": {
        "request": "io", "putrequest": "io", "putheader": "io",
        "endheaders": "io", "send": "io", "getresponse": "io",
        "read": "io", "read1": "io", "readinto": "io",
        "getheader": "io", "getheaders": "io",
        "close": "lifecycle", "connect": "setup",
    },
    "http.server": {  # sull'oggetto server (HTTPServer)
        "serve_forever": "setup", "handle_request": "setup",
        "shutdown": "lifecycle", "server_close": "lifecycle",
    },
}

# Dentro una classe handler (BaseHTTPRequestHandler), su `self.<...>`
HANDLER_CALLS = {
    "wfile.write": "io", "rfile.read": "io", "rfile.readline": "io",
    "send_response": "io", "send_response_only": "io", "send_header": "io",
    "end_headers": "io", "send_error": "io",
}
HANDLER_ATTRS = {  # letture/scritture di attributi rilevanti per il protocollo
    "headers": "io", "path": "io", "command": "io",
    "close_connection": "lifecycle",
}

# Se non riusciamo a legare il ricevente a una risorsa (es. e' un parametro),
# accettiamo comunque questi nomi "forti" nei file che importano la libreria.
NAME_ONLY = {
    "socket": {"send", "sendall", "sendto", "recv", "recv_into", "recvfrom"},
    "http.client": {"request", "putrequest", "putheader", "endheaders",
                    "getresponse"},
}

# Nomi troppo generici per il matching "fuzzy" dei metodi.
COMMON_NOISE = {
    "get", "append", "extend", "items", "keys", "values", "update", "pop",
    "add", "join", "format", "encode", "decode", "strip", "split", "lower",
    "upper", "startswith", "endswith", "replace", "copy", "sort", "remove",
    "clear", "setdefault", "dumps", "loads", "load", "dump", "exists",
    "mkdir", "open", "print", "__init__",
}

RANK = {"exact": 0, "import": 1, "ref": 2, "fuzzy": 3}


# ---------------------------------------------------------------------------
# Utilita' AST
# ---------------------------------------------------------------------------

def dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def resolve(name: str, imports: dict[str, str]) -> str:
    head, _, rest = name.partition(".")
    if head in imports:
        return imports[head] + (f".{rest}" if rest else "")
    return name


def collect_imports(tree: ast.AST) -> dict[str, str]:
    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    imports[a.asname] = a.name
                else:
                    head = a.name.split(".")[0]
                    imports[head] = head
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for a in node.names:
                if a.name == "*":
                    continue
                imports[a.asname or a.name] = f"{mod}.{a.name}" if mod else a.name
    return imports


def libs_used(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in LIBS:
                    found.add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            mod = node.module or ""
            if mod in LIBS:
                found.add(mod)
            elif mod == "http":
                for a in node.names:
                    if f"http.{a.name}" in LIBS:
                        found.add(f"http.{a.name}")
    return found


def compute_bindings(tree: ast.AST, imports: dict[str, str]) -> dict[str, str]:
    """
    Quali variabili (anche `self.sock`) contengono una risorsa di comunicazione.
    Insensibile allo scope, per file; iterato a punto fisso per gestire
    catene tipo  s = socket.socket(); conn, _ = s.accept(); f = conn.makefile().
    """
    bindings: dict[str, str] = {}

    def kind_of(value):
        if isinstance(value, ast.Call):
            d = dotted(value.func)
            if not d:
                return None
            full = resolve(d, imports)
            if full in CREATORS:
                return CREATORS[full], None
            if full in TUPLE_CREATORS:
                return TUPLE_CREATORS[full]
            recv, _, attr = d.rpartition(".")
            if attr == "wrap_socket":
                return "socket", None
            lib = bindings.get(recv) if recv else None
            if lib == "socket" and attr == "accept":
                return "socket", "first"
            if lib == "socket" and attr in ("makefile", "dup"):
                return "socket", None
            if lib == "http.client" and attr == "getresponse":
                return "http.client", None
            return None
        d = dotted(value)
        if d and d in bindings:
            return bindings[d], None
        return None

    def bind(target, kind) -> bool:
        d = dotted(target)
        if d and bindings.get(d) != kind:
            bindings[d] = kind
            return True
        return False

    for _ in range(6):
        changed = False
        for node in ast.walk(tree):
            pairs = []
            if isinstance(node, ast.Assign):
                pairs = [(t, node.value) for t in node.targets]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                pairs = [(node.target, node.value)]
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                pairs = [(i.optional_vars, i.context_expr)
                         for i in node.items if i.optional_vars is not None]
            for target, value in pairs:
                res = kind_of(value)
                if not res:
                    continue
                kind, mode = res
                if isinstance(target, (ast.Tuple, ast.List)):
                    if mode == "first":
                        elts = target.elts[:1]
                    elif mode == "all":
                        elts = target.elts
                    else:
                        continue
                    for e in elts:
                        changed |= bind(e, kind)
                elif mode is None:
                    changed |= bind(target, kind)
        if not changed:
            break
    return bindings


# ---------------------------------------------------------------------------
# Strutture dati
# ---------------------------------------------------------------------------

@dataclass
class FuncInfo:
    id: str
    rel: str
    qual: str
    name: str
    cls: str | None
    lineno: int
    node: object = None  # ast.FunctionDef (usato dal passo 2)


@dataclass
class ClassInfo:
    rel: str
    name: str
    bases: list = field(default_factory=list)
    methods: dict = field(default_factory=dict)  # nome -> func id


@dataclass
class CallSite:
    caller: str
    rel: str
    cls: str | None
    node: ast.Call


@dataclass
class PrimUse:
    func: str
    rel: str
    lib: str
    prim: str
    kind: str
    line: int
    conf: str  # bound | name-only
    node: object = None  # ast.Call / ast.Attribute (usato dal passo 2)


# ---------------------------------------------------------------------------
# Raccolta per file
# ---------------------------------------------------------------------------

class Collector(ast.NodeVisitor):
    def __init__(self, rel, imports, bindings, libs):
        self.rel = rel
        self.imports = imports
        self.bindings = bindings
        self.libs = libs
        self.stack: list[tuple] = []  # ("class", nome, is_handler) | ("func", nome, False)
        self.funcs: dict[str, FuncInfo] = {}
        self.classes: list[ClassInfo] = []
        self.calls: list[CallSite] = []
        self.prims: list[PrimUse] = []

    # -- contesto ---------------------------------------------------------
    def current_id(self) -> str:
        idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == "func":
                idx = i
                break
        if idx is None:
            fid = f"{self.rel}:<module>"
            if fid not in self.funcs:
                self.funcs[fid] = FuncInfo(fid, self.rel, "<module>",
                                           "<module>", None, 1)
            return fid
        qual = ".".join(s[1] for s in self.stack[: idx + 1])
        return f"{self.rel}:{qual}"

    def enclosing_class(self):
        for s in reversed(self.stack):
            if s[0] == "class":
                return s
        return None

    # -- definizioni ------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [dotted(b) or "" for b in node.bases]
        is_handler = "Handler" in node.name or any(
            "Handler" in b or resolve(b, self.imports).startswith("http.server")
            for b in bases if b
        )
        self.classes.append(ClassInfo(self.rel, node.name, bases))
        self.stack.append(("class", node.name, is_handler))
        self.generic_visit(node)
        self.stack.pop()

    def _func(self, node):
        self.stack.append(("func", node.name, False))
        qual = ".".join(s[1] for s in self.stack)
        fid = f"{self.rel}:{qual}"
        parent = self.stack[-2] if len(self.stack) >= 2 else None
        cls = parent[1] if parent and parent[0] == "class" else None
        self.funcs[fid] = FuncInfo(fid, self.rel, qual, node.name, cls,
                                   node.lineno, node)
        if cls:
            for ci in reversed(self.classes):
                if ci.name == cls and ci.rel == self.rel:
                    ci.methods[node.name] = fid
                    break
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = _func
    visit_AsyncFunctionDef = _func

    # -- primitive --------------------------------------------------------
    def _add(self, lib, prim, kind, node, conf):
        self.prims.append(PrimUse(self.current_id(), self.rel, lib, prim,
                                  kind, getattr(node, "lineno", 0), conf, node))

    def visit_Call(self, node: ast.Call):
        cls = self.enclosing_class()
        self.calls.append(CallSite(self.current_id(), self.rel,
                                   cls[1] if cls else None, node))
        d = dotted(node.func)
        if d and self.libs:
            self._check_prim(d, node, cls)
        self.generic_visit(node)

    def _check_prim(self, d, node, cls):
        full = resolve(d, self.imports)
        if full in CREATORS:
            self._add(CREATORS[full], f"<create {full}>", "setup", node, "bound")
            return
        if full in TUPLE_CREATORS:
            self._add(TUPLE_CREATORS[full][0], f"<create {full}>", "setup",
                      node, "bound")
            return
        recv, _, attr = d.rpartition(".")
        if attr == "wrap_socket":
            self._add("socket", "wrap_socket", "setup", node, "bound")
            return
        if (cls and cls[2] and "http.server" in self.libs
                and d.startswith("self.") and d[5:] in HANDLER_CALLS):
            self._add("http.server", d[5:], HANDLER_CALLS[d[5:]], node, "bound")
            return
        lib = self.bindings.get(recv) if recv else None
        if lib:
            kind = PRIMS.get(lib, {}).get(attr)
            if kind:
                self._add(lib, attr, kind, node, "bound")
                return
        if recv:
            for l in sorted(self.libs):
                if attr in NAME_ONLY.get(l, ()):
                    self._add(l, attr, PRIMS[l][attr], node, "name-only")
                    return

    def visit_Attribute(self, node: ast.Attribute):
        cls = self.enclosing_class()
        if cls and cls[2] and "http.server" in self.libs:
            d = dotted(node)
            if d and d.startswith("self.") and d[5:] in HANDLER_ATTRS:
                self._add("http.server", d[5:], HANDLER_ATTRS[d[5:]], node, "bound")
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# Progetto: indice, risoluzione chiamate, caller graph
# ---------------------------------------------------------------------------

class Project:
    def __init__(self, max_fuzzy: int):
        self.max_fuzzy = max_fuzzy
        self.funcs: dict[str, FuncInfo] = {}
        self.by_name: dict[str, list] = defaultdict(list)
        self.classes: dict[str, list] = defaultdict(list)
        self.imports: dict[str, dict] = {}
        self.module_of: dict[str, str] = {}
        self.comm_files: dict[str, set] = {}
        self.callsites: list[CallSite] = []
        self.prims: list[PrimUse] = []
        # callee -> caller -> (conf, line)
        self.callers: dict[str, dict] = defaultdict(dict)
        self.trees: dict[str, ast.AST] = {}
        # callee id -> [(CallSite, conf)]  (solo chiamate, non callback)
        self.sites_to: dict[str, list] = defaultdict(list)
        self.skipped_fuzzy: dict[str, int] = defaultdict(int)
        self._mod_cache: dict[str, set] = {}

    # -- indicizzazione ---------------------------------------------------
    def add_file(self, repo: Path, path: Path):
        rel = path.relative_to(repo).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError, OSError) as exc:
            print(f"warning: salto {rel}: {exc}", file=sys.stderr)
            return
        imports = collect_imports(tree)
        libs = libs_used(tree)
        bindings = compute_bindings(tree, imports) if libs else {}
        col = Collector(rel, imports, bindings, libs)
        col.visit(tree)

        self.imports[rel] = imports
        self.trees[rel] = tree
        parts = list(Path(rel).with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts.pop()
        self.module_of[rel] = ".".join(parts)
        if libs:
            self.comm_files[rel] = libs
        for fid, fi in col.funcs.items():
            self.funcs[fid] = fi
            if fi.name != "<module>":
                self.by_name[fi.name].append(fi)
        for ci in col.classes:
            self.classes[ci.name].append(ci)
        self.callsites.extend(col.calls)
        self.prims.extend(col.prims)

    def files_for_module(self, mod: str) -> set:
        if not mod:
            return set()
        if mod not in self._mod_cache:
            self._mod_cache[mod] = {
                rel for rel, m in self.module_of.items()
                if m == mod or m.endswith("." + mod)
            }
        return self._mod_cache[mod]

    # -- lookup -----------------------------------------------------------
    def find_top(self, name, rels=None):
        return [f for f in self.by_name.get(name, [])
                if f.qual == name and (rels is None or f.rel in rels)]

    def _lookup_in_class(self, ci, attr, seen):
        key = (ci.rel, ci.name)
        if key in seen:
            return []
        seen.add(key)
        if attr in ci.methods:
            return [self.funcs[ci.methods[attr]]]
        hits = []
        for b in ci.bases:
            bname = b.rsplit(".", 1)[-1]
            for bci in self.classes.get(bname, []):
                hits += self._lookup_in_class(bci, attr, seen)
        return hits

    def method_lookup(self, cls_name, attr, prefer_rel):
        infos = self.classes.get(cls_name, [])
        pref = [c for c in infos if c.rel == prefer_rel]
        hits = []
        for ci in (pref or infos):
            hits += self._lookup_in_class(ci, attr, set())
        return hits

    def class_init(self, name, prefer_rel, rels=None):
        infos = self.classes.get(name, [])
        if rels is not None:
            infos = [c for c in infos if c.rel in rels]
        elif prefer_rel is not None:
            infos = [c for c in infos if c.rel == prefer_rel]
        hits = []
        for ci in infos:
            hits += self._lookup_in_class(ci, "__init__", set())
        return hits

    # -- risoluzione ------------------------------------------------------
    def resolve_target(self, expr, rel, cls, fuzzy):
        imports = self.imports[rel]

        if isinstance(expr, ast.Name):
            name = expr.id
            local = [f for f in self.by_name.get(name, [])
                     if f.rel == rel and f.qual == name]
            if local:
                return [(f, "exact") for f in local]
            ctor = self.class_init(name, rel)
            if ctor:
                return [(f, "exact") for f in ctor]
            target = imports.get(name)
            if target:
                mod, _, sym = target.rpartition(".")
                rels = self.files_for_module(mod)
                if rels:
                    hits = self.find_top(sym, rels) or self.class_init(sym, None, rels)
                    if hits:
                        return [(f, "import") for f in hits]
            if fuzzy:
                hits = self.find_top(name) or self.class_init(name, None)
                if 0 < len(hits) <= self.max_fuzzy:
                    return [(f, "fuzzy") for f in hits]
            return []

        if isinstance(expr, ast.Attribute):
            attr, base = expr.attr, expr.value
            recv = dotted(base)
            if recv in ("self", "cls") and cls:
                hits = self.method_lookup(cls, attr, rel)
                if hits:
                    return [(f, "exact") for f in hits]
            elif (isinstance(base, ast.Call) and dotted(base.func) == "super"
                  and cls):
                hits = []
                for ci in self.classes.get(cls, []):
                    if ci.rel == rel:
                        for b in ci.bases:
                            hits += self.method_lookup(b.rsplit(".", 1)[-1], attr, rel)
                if hits:
                    return [(f, "exact") for f in hits]
            elif recv:
                head = recv.split(".")[0]
                if head in imports:
                    full = resolve(recv, imports)
                    rels = self.files_for_module(full)
                    if rels:
                        hits = (self.find_top(attr, rels)
                                or self.class_init(attr, None, rels))
                        if hits:
                            return [(f, "import") for f in hits]
                    else:  # from mod import Class ; Class.metodo()
                        hits = self.method_lookup(full.rsplit(".", 1)[-1], attr, None)
                        if hits:
                            return [(f, "import") for f in hits]
                elif recv in self.classes:
                    hits = self.method_lookup(recv, attr, rel)
                    if hits:
                        return [(f, "exact") for f in hits]
            if fuzzy and attr not in COMMON_NOISE:
                hits = [f for f in self.by_name.get(attr, []) if f.cls is not None]
                if 0 < len(hits) <= self.max_fuzzy:
                    return [(f, "fuzzy") for f in hits]
                if len(hits) > self.max_fuzzy:
                    self.skipped_fuzzy[attr] += 1
        return []

    def _add_edge(self, caller, callee, conf, line):
        if callee == "":
            return
        cur = self.callers[callee].get(caller)
        if cur is None or RANK[conf] < RANK[cur[0]]:
            self.callers[callee][caller] = (conf, line)

    def build_edges(self):
        for cs in self.callsites:
            line = getattr(cs.node, "lineno", 0)
            for fi, conf in self.resolve_target(cs.node.func, cs.rel, cs.cls, True):
                self._add_edge(cs.caller, fi.id, conf, line)
                self.sites_to[fi.id].append((cs, conf))
            # funzioni passate come callback: Thread(target=self.worker), ...
            values = list(cs.node.args) + [k.value for k in cs.node.keywords]
            for v in values:
                if isinstance(v, (ast.Name, ast.Attribute)):
                    for fi, _ in self.resolve_target(v, cs.rel, cs.cls, False):
                        self._add_edge(cs.caller, fi.id, "ref", line)

    # -- report -----------------------------------------------------------
    def label(self, fid):
        return fid

    def reachable_roots(self, start):
        seen, stack, roots = {start}, [start], set()
        while stack:
            cur = stack.pop()
            parents = self.callers.get(cur)
            if not parents:
                roots.add(cur)
                continue
            for p in parents:
                if p not in seen:
                    seen.add(p)
                    stack.append(p)
        return sorted(roots)

    def caller_tree(self, sink, max_depth):
        out: list[str] = []
        expanded: set = {sink}

        def walk(fid, prefix, path, depth):
            parents = sorted(
                self.callers.get(fid, {}).items(),
                key=lambda kv: (RANK[kv[1][0]], kv[0]),
            )
            for i, (cid, (conf, line)) in enumerate(parents):
                last = i == len(parents) - 1
                branch = "└─ " if last else "├─ "
                ext = "   " if last else "│  "
                tag = "" if conf == "exact" else f" <{conf}>"
                where = f" @L{line}" if line else ""
                name = f"{self.label(cid)}{tag}{where}"
                if cid in path:
                    out.append(f"{prefix}{branch}{name} (ciclo)")
                    continue
                if cid in expanded:
                    out.append(f"{prefix}{branch}{name} (gia' espanso sopra)")
                    continue
                is_root = not self.callers.get(cid)
                out.append(f"{prefix}{branch}{name}{' [ROOT]' if is_root else ''}")
                expanded.add(cid)
                if depth + 1 >= max_depth:
                    if not is_root:
                        out.append(f"{prefix}{ext}└─ ... (max depth)")
                    continue
                walk(cid, prefix + ext, path + (cid,), depth + 1)

        walk(sink, "", (sink,), 0)
        return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def is_test(rel: str) -> bool:
    p = Path(rel)
    return "tests" in p.parts or p.name.startswith("test_")


def build_project(repo: Path, excludes: set, no_tests: bool,
                  max_fuzzy: int) -> Project:
    project = Project(max_fuzzy)
    for path in sorted(repo.rglob("*.py")):
        rel_parts = path.relative_to(repo).parts
        if any(part in excludes for part in rel_parts):
            continue
        if no_tests and is_test(path.relative_to(repo).as_posix()):
            continue
        project.add_file(repo, path)
    project.build_edges()
    return project


def main():
    ap = argparse.ArgumentParser(
        description="Passo 1: file/funzioni di comunicazione e caller graph."
    )
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--kinds", default="io,lifecycle",
                    help="io,lifecycle,setup (default: io,lifecycle)")
    ap.add_argument("--strict", action="store_true",
                    help="solo primitive legate a una risorsa nota (no name-only)")
    ap.add_argument("--no-tests", action="store_true", help="ignora i test")
    ap.add_argument("--max-depth", type=int, default=40)
    ap.add_argument("--max-fuzzy", type=int, default=6,
                    help="oltre N candidati un arco fuzzy viene scartato")
    ap.add_argument("--exclude", action="append", default=[],
                    help="directory extra da escludere (ripetibile)")
    ap.add_argument("--json", metavar="PATH", help="scrive anche un dump JSON")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        raise SystemExit(f"error: non esiste: {repo}")
    excludes = EXCLUDES | set(args.exclude)
    wanted = {k.strip() for k in args.kinds.split(",") if k.strip()}

    project = build_project(repo, excludes, args.no_tests, args.max_fuzzy)

    prims = [p for p in project.prims
             if p.kind in wanted and (not args.strict or p.conf == "bound")]
    by_func: dict[str, list] = defaultdict(list)
    for p in prims:
        by_func[p.func].append(p)

    out: list[str] = []
    out.append("# Comunicazione a basso livello")
    out.append("")
    out.append(f"## File che importano {', '.join(LIBS)} ({len(project.comm_files)})")
    out.append("")
    for rel in sorted(project.comm_files):
        t = " (test)" if is_test(rel) else ""
        out.append(f"- `{rel}` [{', '.join(sorted(project.comm_files[rel]))}]{t}")
    out.append("")

    out.append(f"## Funzioni che usano primitive ({len(by_func)})")
    out.append("")
    for fid in sorted(by_func):
        uses = sorted(by_func[fid], key=lambda p: p.line)
        desc = "; ".join(
            f"L{u.line} {u.lib}.{u.prim} ({u.kind}{'' if u.conf == 'bound' else ', name-only'})"
            for u in uses
        )
        out.append(f"- `{fid}`: {desc}")
    out.append("")

    out.append("## Caller graph (dalla funzione con primitiva verso le radici)")
    out.append("")
    for fid in sorted(by_func):
        out.append(f"### {fid}")
        out.append("```")
        out.append(fid)
        tree = project.caller_tree(fid, args.max_depth)
        out.extend(tree if tree else ["└─ (nessun chiamante: e' gia' una radice)"])
        out.append("```")
        out.append("")

    out.append("## Riepilogo: entry point che raggiungono ogni funzione")
    out.append("")
    for fid in sorted(by_func):
        roots = project.reachable_roots(fid)
        out.append(f"- `{fid}` <- " + ", ".join(f"`{r}`" for r in roots))
    out.append("")

    n_edges = sum(len(v) for v in project.callers.values())
    by_conf: dict[str, int] = defaultdict(int)
    for parents in project.callers.values():
        for conf, _ in parents.values():
            by_conf[conf] += 1
    out.append("## Statistiche")
    out.append("")
    out.append(f"- Funzioni indicizzate: {len(project.funcs)}")
    out.append(f"- Archi del call graph: {n_edges} "
               + ", ".join(f"{k}={v}" for k, v in sorted(by_conf.items())))
    if project.skipped_fuzzy:
        top = sorted(project.skipped_fuzzy.items(), key=lambda kv: -kv[1])[:10]
        out.append("- Chiamate fuzzy scartate (troppi candidati): "
                   + ", ".join(f"{n}x{c}" for n, c in top))
    out.append("- Limiti: risoluzione per nome, niente tipi; callback dinamici, "
               "getattr e chiamate via dict non sono seguiti.")
    print("\n".join(out))

    if args.json:
        dump = {
            "comm_files": {k: sorted(v) for k, v in project.comm_files.items()},
            "prims": [{k: v for k, v in p.__dict__.items() if k != "node"}
                      for p in prims],
            "funcs": {k: {"rel": f.rel, "qual": f.qual, "cls": f.cls,
                          "line": f.lineno}
                      for k, f in project.funcs.items()},
            "edges": [
                {"caller": caller, "callee": callee, "conf": conf, "line": line}
                for callee, parents in project.callers.items()
                for caller, (conf, line) in parents.items()
            ],
        }
        Path(args.json).write_text(json.dumps(dump, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()