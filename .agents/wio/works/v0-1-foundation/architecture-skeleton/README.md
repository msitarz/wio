<!-- wio
id = "jsk0yt"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = []
-->

# Architecture skeleton

## Purpose

Each v0.1 component needs a place in `src/wio` and typed boundaries to its
neighbors, so that it can be built alone against their stubs.

## Goals

- The v0.1 packages exist under `src/wio`, each stating its role.
- Every interaction between a package and the outside is declared as a port in
  a `.pyi` stub, owned by the package that consumes it.
- The shared types that the ports mention are declared once, in `wio.models`.
- The `wio` command is installed and dispatches through the composition root.
- The documents describe the architecture the stubs encode.

## Non-Goals

- Adapters other than the one for standard streams, which the entry point needs.
- Stubs for the `wio.formats` codecs, whose shapes the component Works settle.
- Lazy bindings for components, which each component's Work adds with its
  command.
- The `tach` configuration, which the tach enforcement Work owns.
- Changing `docs/README.md` or `docs/concepts.md`.

## Assumptions

- **A-1**: The `hello()` placeholder and its unit test have no user, so
  replacing them breaks nothing.
- **A-2**: The collaborators in the provisional table below are enough for the
  data flows of the scope document, and the architecture stage may rename them.

## Mechanisms

- `src/wio/<package>/__init__.py`, with only a module docstring, makes each
  package importable.
- `src/wio/<package>/ports.pyi` holds the `typing.Protocol` classes that
  `<package>` consumes.
- `src/wio/models/*.pyi` hold the shared types as stubs, until the Work that
  implements a type replaces its stub.
- `wio.cli.console_main` is the console script, and `wio.cli.main` is the
  function that tests call.
- `[project.scripts]` in `pyproject.toml` installs the `wio` command.

## Acceptance criteria

### **AC-1** The v0.1 packages exist and state their roles

Importing any package of v0.1 works, and its docstring says what the package is
for.

The packages are `wio.models`, `wio.formats`, `wio.io`, `wio.config`,
`wio.contract`, `wio.rule`, `wio.trailers`, `wio.log`, `wio.context` and
`wio.cli`.

#### Every package imports

- **Given** a synchronized environment.
- **When** each package is imported.
- **Then** no import fails, and each package's docstring is one sentence that
  names its role.

### **AC-2** Each consumer declares what it needs as ports of its own

A package that calls collaborators has a `ports.pyi` with one `Protocol` per
collaborator, and no package that consumes nothing has one.

Provisional, as the architecture stage may rename the Protocols:

| Package | Protocols it declares | Satisfied by |
| --- | --- | --- |
| `contract` | `Settings` | `config` |
| `rule` | `Settings` | `config` |
| `trailers` | `Settings`, `Contracts`, `EventSink` | `config`, `contract`, `log` |
| `context` | `Settings`, `Contracts`, `RuleSelection`, `EventSink` | `config`, `contract`, `rule`, `log` |
| `cli` | `Command` | every component |

`config` and `log` consume only the ports of `wio.io`, so they declare none.

#### Ports are typed and documented

- **Given** the delivered tree.
- **When** `pyrefly check` and `ruff check` run.
- **Then** both pass, every `Protocol` and method in a `ports.pyi` has a
  docstring that says what it guarantees, and every name in a signature
  resolves to `wio.models`, `wio.io` or the standard library.

#### No port names a neighbor

- **Given** a `ports.pyi` of a component.
- **When** its imports are read.
- **Then** none of them comes from another component's package.

### **AC-3** The outside world is reached through ports declared once

`wio.io` declares the ports for the filesystem, standard streams, git and the
environment, and has one real adapter, for standard streams.

```python
class Stdio(Protocol):
    stdin: TextIO
    stdout: TextIO
    stderr: TextIO
```

#### The standard-streams adapter

- **Given** the adapter for standard streams.
- **When** it is created.
- **Then** its `stdin`, `stdout` and `stderr` are `sys.stdin`, `sys.stdout` and
  `sys.stderr`.

#### No other adapter

- **Given** the delivered tree.
- **When** `wio.io` is listed.
- **Then** its `FileSystem`, `Git` and `Environment` ports have no adapter.

### **AC-4** The shared types are declared as far as the ports need them

`wio.models` has a stub for each type that a port signature names, and a field
appears only when a port signature or a criterion of this Work reads it.

#### Types follow the ports

- **Given** the delivered tree.
- **When** the types named in every `ports.pyi` are compared with the stubs in
  `wio.models`.
- **Then** every type that a port names has a stub with a docstring, and no stub
  is unused by a port.

### **AC-5** The `wio` command is installed and runs through the composition root

After synchronizing, `wio` runs the entry point and exits 0 without output,
until the `cli` component makes it print its description.

```python
def main(argv: Sequence[str], stdio: Stdio) -> int: ...
def console_main() -> int: ...
```

`console_main` builds the adapter for standard streams and returns
`main(sys.argv[1:], stdio)`. `Command` in `cli/ports.pyi` has the provisional
members `name: str`, `help: str`, `configure(parser: ArgumentParser) -> None`
and `run(args: Namespace, stdio: Stdio) -> int`.

#### The installed command

- **Given** a synchronized environment.
- **When** `wio` runs with no arguments.
- **Then** it exits 0 and writes nothing to standard output or standard error.

#### The testable core

- **Given** in-memory streams in place of standard streams.
- **When** `main([], stdio)` is called.
- **Then** it returns 0 and the streams hold nothing.

#### The placeholder is gone

- **Given** the delivered tree.
- **When** `hello` and `tests/unit/test_cli.py::test_hello` are searched for.
- **Then** neither exists.

### **AC-6** The documents describe the architecture the stubs encode

`docs/v0.1-scope.md` names `wio.formats` and `wio.io` where it named the
foundation, and `GLOSSARY.md` defines the terms the architecture introduces.

#### The scope document

- **Given** the delivered documents.
- **When** `docs/v0.1-scope.md` is read.
- **Then** it has no "Foundation (internal)" heading, has one for `wio.formats`
  and one for `wio.io`, links to the parent Work for the dependency direction
  instead of copying it, and its order of work lists the skeleton, the tach
  enforcement and the test DSL before the components.

#### The glossary

- **Given** the delivered documents.
- **When** `GLOSSARY.md` is read.
- **Then** it has a row each for Component, Port, Adapter and Command, and
  `rumdl check` passes on both files.

## Additional context

- The [parent Work](../README.md) states the dependency direction, the port
  ownership and the stub lifecycle that this Work applies.
