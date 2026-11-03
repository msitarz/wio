<!-- wio
id = "41wfqk"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = []
-->

# The command table and port

## Purpose

A subcommand can join the command line only through a table whose entries the
type checker restricts to the components of wio and whose commands describe
themselves apart from running, so the table and its port come before the
dispatch that uses them.

## Goals

- A subcommand is added with one entry in a table, and a package name that is
  not a component of wio is rejected by the type checker.
- A component's command can be described without wiring it and without loading
  its implementation.
- A check says when the package of a command loads its implementation only to
  be described.

## Non-Goals

- Dispatching to the entries, which the dispatch leaf does.
- Any real subcommand: the table is empty until the Work of the first component
  adds its entry.
- The platform parameter of the wiring, which the first platform-dependent
  adapter adds.
- Committing a test that proves `pyrefly` rejects an unknown component; the
  reviewer tries one locally instead.

## Assumptions

- **A-1**: Importing a module that uses `lazy import` loads none of the modules
  it imports lazily (checked on Python 3.15.2 on 2026-11-03).
- **A-2**: The packages directly under `src/wio` that are not components are the
  layers `models`, `formats`, `io`, `env` and `ports`, the composition root
  `cli`, and `errors`, as `src/wio/GLOSSARY.md` and the errors leaf say.

## Mechanisms

- `typing.Literal` for the names of the components, and a frozen dataclass for
  the entry.
- `importlib.import_module` of `wio.<package>` for a real entry, then its
  `describe()`.
- A subprocess that imports a package and lists `sys.modules`, for the
  import-light check.

## Acceptance criteria

### **AC-1** An entry names a real component

An entry holds a component name that the type checker restricts, a way to
describe the command that needs no wiring, and a way to wire it.

```python
Component = Literal["config", "contracts", "rules", "trailers", "log", "context"]


@dataclass(frozen=True)
class Entry:
    package: Component
    describe: Callable[[], CommandSpec]
    wire: Callable[[], Command]


def component_entry(package: Component, wire: Callable[[], Command]) -> Entry: ...
```

`Component`, `Entry` and `component_entry` are required as written. The name of
the table, `COMMANDS: Final[Sequence[Entry]]`, is provisional. The `describe` of
an entry from `component_entry` imports `wio.<package>` and returns its
`describe()`, a function every component's package provides.

#### An unknown component

- **Given** a call `component_entry("nonexistent", wire)` added locally by the
  reviewer and not committed.
- **When** `uv run pyrefly check` runs.
- **Then** it exits non-zero and names the call.

#### Describing without wiring

- **Given** a stand-in module installed as `wio.config` whose `describe()`
  returns a spec, and an entry from `component_entry("config", wire)`.
- **When** the entry's `describe()` is called.
- **Then** it returns that spec and `wire` was not called.

### **AC-2** The table names only real components

The names in `Component` equal the components of `wio`, and every entry of the
real table has one of them.

#### The names match the packages

- **Given** the packages directly under `src/wio` and the packages that are not
  components, listed in the unit test (assumption A-2).
- **When** a unit test compares the first without the second to the names in
  `Component`.
- **Then** the two are equal, so a new package fails the test until the driver
  decides whether it is a component.

#### The real table

- **Given** the real table of commands.
- **When** a unit test reads each entry's `package`.
- **Then** each is a name in `Component`, which holds vacuously until the first
  component adds its entry.

### **AC-3** The command port is split and documented

`src/wio/cli/ports.pyi` declares `CommandSpec` and `Command`, each with a
docstring: `CommandSpec` has read-only `name` and `help` properties and
`configure(parser: ArgumentParser) -> None`, and `Command` has
`run(args: Namespace, stdio: Stdio) -> int`. Its module docstring no longer says
that one invocation loads only the command it runs. The glossary of
`src/wio/cli` defines Command, command spec and entry in place of its single
definition of Command.

### **AC-4** The import-light rule can fail

A check fails for a package whose import, or whose `describe()` and the
`configure` of its description, loads a module under that package other than its
`__init__`, and passes for a package that loads none.

#### A fixture package

- **Given** two fixture packages under `tests`, one whose `__init__` imports an
  implementation module eagerly and one that imports it lazily, each with a
  `describe`.
- **When** the check runs for each, in a fresh interpreter.
- **Then** it fails for the first and names the implementation module, and
  passes for the second.

#### The real table

- **Given** the real table of commands.
- **When** the check runs for each entry's package.
- **Then** it passes, which holds vacuously until the first component adds its
  entry.

## Additional context

- [Glossary of `src/wio`](../../../../../src/wio/GLOSSARY.md) lists the
  components and the layers that are not.
