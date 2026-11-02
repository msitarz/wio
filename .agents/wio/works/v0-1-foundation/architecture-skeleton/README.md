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
  a `.pyi` stub.
- The shared types that the ports mention are declared once, in `wio.models`.
- The `wio` command is installed and its entry point runs through the
  composition root.
- The documents and glossaries describe the architecture the stubs encode.

## Non-Goals

- Adapters other than the one for standard streams, which the entry point needs.
- Stubs for the `wio.formats` codecs, whose shapes the component Works settle.
- Lazy bindings for components, which each component's Work adds with its
  command.
- What `wio` does with arguments, which the Work of the `cli` package settles.
- The `tach` configuration, which the tach enforcement Work owns.
- Changing `docs/README.md` or `docs/concepts.md`.

## Assumptions

- **A-1**: The `hello()` placeholder, `src/wio/cli.py` and the unit test of
  `hello` have no user, so replacing them breaks nothing.
- **A-2**: The collaborators in the provisional table below are enough for the
  data flows of the scope document, including that `config` and `log` consume
  only the ports of `wio.io` and `wio.env`, and the architecture stage may
  rename, add or move them.
- **A-3**: The architecture review verifies the docstrings of the stubs, because
  `ruff check` applies no docstring rule to `.pyi` files.
- **A-4**: The real adapters for the ports of `wio.io` other than `Stdio`, and
  for those of `wio.env`, arrive with the Work of the first component that
  consumes the port, which also tests each against the port's docstring.

## Mechanisms

- `src/wio/<package>/__init__.py` makes each package importable; its content is
  a module docstring, and in `cli` also `main` and `console_main`.
- `src/wio/<package>/ports.pyi` holds the `typing.Protocol` classes that
  `<package>` consumes.
- `src/wio/io/ports.pyi` holds the ports of `wio.io`, and
  `src/wio/io/adapters.py` holds its adapters.
- `src/wio/env/ports.pyi` holds the ports of `wio.env`, and
  `src/wio/env/adapters.py` holds its adapters, none yet.
- `src/wio/models/*.pyi` hold the shared types as stubs, until the Work that
  implements a type replaces its stub.
- `[project.scripts]` in `pyproject.toml` installs the command with the line
  `wio = "wio.cli:console_main"`.
- `src/wio/GLOSSARY.md` and `src/wio/cli/GLOSSARY.md` hold the terms of the
  architecture, bound to their directory and its descendants.
- `wheel-exclude` in `[tool.uv.build-backend]` of `pyproject.toml` gains
  `GLOSSARY.md`, and a slow test in `tests/packaging/test_build.py` checks the
  wheel.

## Acceptance criteria

### **AC-1** The v0.1 packages exist and state their roles

Importing any package of v0.1 works, and its docstring says what the package is
for.

The packages are `wio.models`, `wio.formats`, `wio.io`, `wio.env`,
`wio.config`, `wio.contract`, `wio.rule`, `wio.trailers`, `wio.log`,
`wio.context` and `wio.cli`.

#### Every package imports

- **Given** a synchronized environment.
- **When** each package is imported.
- **Then** no import fails, and each package's docstring is one sentence that
  names its role.

### **AC-2** Each consumer declares what it needs as ports of its own

A package that calls collaborators other than `wio.io` and `wio.env` has a
`ports.pyi` with one `Protocol` per collaborator, and no other package outside
those two has one.

Provisional, as the architecture stage may rename the Protocols:

| Package | Protocols it declares | Satisfied by |
| --- | --- | --- |
| `contract` | `Settings` | `config` |
| `rule` | `Settings` | `config` |
| `trailers` | `Settings`, `Contracts`, `EventSink` | `config`, `contract`, `log` |
| `context` | `Settings`, `Contracts`, `RuleSelection`, `EventSink` | `config`, `contract`, `rule`, `log` |
| `cli` | `Command` | every component |

`config` and `log` consume only the ports of `wio.io` and `wio.env`, so they
declare none.

#### Ports are typed and documented

- **Given** the delivered tree.
- **When** `pyrefly check` runs and the architecture review reads the stubs.
- **Then** `pyrefly` passes, every `Protocol` and method in a `ports.pyi` has a
  docstring that says what it guarantees, and every name in a signature
  resolves to `wio.models`, `wio.io`, `wio.env` or the standard library.

#### No port names a neighbor

- **Given** a `ports.pyi` of a component.
- **When** its imports are read.
- **Then** none of them comes from another component's package.

### **AC-3** The outside world is reached through ports declared once

`wio.io` declares the ports for the filesystem, standard streams and git,
`wio.env` declares those for what the process knows about its surroundings, and
`wio.io` has the only real adapter, for standard streams.

Provisional: `Stdio` is as below. `FileSystem` and `Git` of `wio.io`, and
`Environment`, `Clock`, `Entropy` and `Directories` of `wio.env`, may start as
documented Protocols with the members that the architecture stage finds the
scope document needs. `Environment` reads variables and the working directory,
`Clock` the time, `Entropy` secure random bytes, and `Directories` the
well-known directories, starting with the temporary directory. The adapter is
`SystemStdio` in `wio.io.adapters`.

```python
class Stdio(Protocol):
    stdin: TextIO
    stdout: TextIO
    stderr: TextIO
```

#### The standard-streams adapter

- **Given** the adapter `SystemStdio`.
- **When** it is created.
- **Then** its `stdin`, `stdout` and `stderr` are `sys.stdin`, `sys.stdout` and
  `sys.stderr`.

#### No other adapter

- **Given** the delivered tree.
- **When** `wio.io.adapters` and `wio.env.adapters` are listed.
- **Then** the first holds only `SystemStdio` and the second holds none, so the
  other ports have no adapter.

#### The temporary directory

- **Given** the delivered stubs.
- **When** the architecture review reads the docstring of the `Directories`
  member that returns the temporary directory.
- **Then** it states that the result is the directory `$TMPDIR` names, as it is,
  when `$TMPDIR` is set to a non-empty value; otherwise `/tmp` on Linux or
  `/private/tmp` on macOS, when a small test file can be written there; and
  that it raises an error when it cannot be.

### **AC-4** The shared types are declared as far as the ports need them

`wio.models` has a stub for each type that a port signature names, and a field
appears only when a port signature or a criterion of this Work reads it.

#### Types follow the ports

- **Given** the delivered tree.
- **When** the types named in every `ports.pyi` are compared with the stubs in
  `wio.models`, and the architecture review reads the stubs.
- **Then** every type that a port names has one stub with a docstring, and no
  stub is unused by a port.

### **AC-5** The `wio` command is installed and runs through the composition root

After synchronizing, `wio` runs the entry point and exits 0 without output,
until the Work of the `cli` package makes it print its description. What it does
with arguments is undefined until then.

```python
def main(argv: Sequence[str], stdio: Stdio) -> int: ...
def console_main() -> int: ...
```

`console_main` builds `SystemStdio` and returns `main(sys.argv[1:], stdio)`.
The two signatures are required; `main` ignores its arguments until then, and
how the implementation satisfies the unused-argument lint is its own choice.
`Command` in `cli/ports.pyi` has the provisional members `name: str`,
`help: str`, `configure(parser: ArgumentParser) -> None` and
`run(args: Namespace, stdio: Stdio) -> int`.

#### The installed command

- **Given** a synchronized environment.
- **When** `wio` runs with no arguments.
- **Then** it exits 0 and writes nothing to standard output or standard error.

#### The testable core

- **Given** in-memory streams in place of standard streams.
- **When** `main([], stdio)` is called.
- **Then** it returns 0 and the streams hold nothing.

#### The console function

- **Given** `sys.argv` set to `["wio"]`.
- **When** `console_main()` is called in a fast unit test.
- **Then** it returns 0 and nothing is captured on standard output or standard
  error.

#### The placeholder is gone

- **Given** the delivered tree.
- **When** `src/wio/cli.py`, `hello` and `tests/unit/test_cli.py::test_hello`
  are searched for.
- **Then** none of them exists.

### **AC-6** The documents and glossaries describe the architecture

`docs/v0.1-scope.md` names `wio.formats`, `wio.io` and `wio.env` where it named
the foundation, and the terms of the architecture are defined in glossaries
bound to the directories that use them.

#### The scope document

- **Given** the delivered documents.
- **When** `docs/v0.1-scope.md` is read.
- **Then** its Overview table and its sections have no "Foundation" row or
  heading, have one each for `wio.formats`, `wio.io` and `wio.env`, the Overview
  table's first column is not headed "Component", it links to the parent Work
  for the dependency direction instead of copying it, and its order of work
  lists the skeleton, the tach enforcement and the test DSL before the
  components.

#### Scoped glossaries

- **Given** the delivered tree.
- **When** `src/wio/GLOSSARY.md`, `src/wio/cli/GLOSSARY.md` and `AGENTS.md` are
  read.
- **Then** the first defines Component, Port and Adapter, the second defines
  Command and says that `cli` is the composition root and no component, and
  `AGENTS.md` says that a `GLOSSARY.md` binds its terms to its directory and
  descendants and that the nearest one wins.

#### Glossaries stay out of the wheel

- **Given** the wheel built from the delivered tree.
- **When** the slow packaging test lists its files.
- **Then** no `GLOSSARY.md` is in it, and `rumdl check` passes on every file
  this Work changed.

## Additional context

- The [parent Work](../README.md) states the dependency direction, the port
  ownership and the stub lifecycle that this Work applies, and the definitions
  that this Work moves into the glossaries.
