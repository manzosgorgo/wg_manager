# wg-manager documentation

Automatically generated documentation for the `wg_manager` project.

> This repository contains generated documentation and analysis artifacts.
> It is observational documentation of the current project tree, not a
> normative architecture specification.

## Project analysis

- [AI index](ai/README.md)
- [Project tree](ai/TREE.md)
- [Modules](ai/MODULES.md)
- [Dependencies](ai/DEPENDENCIES.md)
- [Symbols](ai/SYMBOLS.md)
- [Connections](ai/CONNECTIONS.md)

## Protocol snapshots

- [wg-auth protocol](ai/wg_auth_proto.md)
- [wg-client protocol](ai/wg_client_proto.md)
- [wg-manager protocol](ai/wg_manager_proto.md)
- [wg-all protocol](ai/wg_all_proto.md)

## Python API documentation

- [pydoc API index](ai/pydoc/index.html)

Generate or refresh it from the repository root with:

```bash
python3 tools/build_pydoc.py
```

The generator discovers Python modules under `src/wg_auth`, `src/wg_client`
and `src/wg_manager`, writes the HTML under `docs/ai/pydoc/`, and reports
modules that pydoc could not import.

## Source documentation

The [`ai/files/`](ai/files/) directory contains generated documentation
for the individual source files discovered by the project indexer.

## Generation

The documentation is generated mechanically from the `wg_manager` source
tree using the analysis tools in the project.

The protocol snapshots are generated independently for:

- `src/wg_auth`
- `src/wg_client`
- `src/wg_manager`
