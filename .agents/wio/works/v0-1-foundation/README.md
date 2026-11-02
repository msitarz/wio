<!-- wio
id = "zpnbj3"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# v0.1 foundation

## Purpose

Every v0.1 component needs a fixed place, a typed boundary to the others and a
test setup before any of them is built, so that each can be delivered alone.

## Goals

- The repository's own checks reject a change that breaks the dependency
  direction between the packages of `src/wio`.
- The place of every v0.1 component and the boundaries it must honor can be read
  from `src/wio` and its stubs.
- Each component can be built against the typed ports it consumes, with an
  acceptance test setup that already runs the `wio` command.

## Glossary

These definitions are the source until the skeleton leaf moves them to
`src/wio/GLOSSARY.md` and `src/wio/cli/GLOSSARY.md`, which bind them to that
directory and its descendants; a ratify then replaces this section with links.

- **Component**: the package under `src/wio` of one v0.1 subcommand, which is
  `config`, `contract`, `rule`, `trailers`, `log` or `context`; `cli` is the
  composition root and `models`, `formats` and `io` are shared layers, so none
  of them is a component.
- **Port**: a `typing.Protocol` declared in a `.pyi` stub, saying what a package
  needs from the outside.
- **Adapter**: the implementation of a port, one per port for now; real
  adapters are imported only by `cli`, and fakes live in the tests.
- **Command**: the object a component exposes to the command line, with a name,
  a help text, a function that configures its argparse subparser and a function
  that runs it.

## Non-Goals

- Implementing any component's behavior, formats or model fields beyond what a
  port signature needs.
- Fixing the config schema, the directive grammar or the rule metadata, which
  the Works of the components settle.
- Writing the `wio-define` skill.
- Committing a test that proves tach rejects a forbidden import; the reviewer
  tries one locally instead.
- Making the bare `wio` command print its description, which the Work of the
  `cli` package does.

## Assumptions

- **A-1**: Tach 0.35.3 reads no imports inside `.pyi` files, so the imports of
  the stubs follow the dependency direction by convention and review.
- **A-2**: Ruff, pyrefly and tach, at the locked versions, accept the Python
  3.15 `lazy import` syntax, and tach counts a lazy import as a dependency.
- **A-3**: The scope document's six components are all of v0.1, and
  `wio-define` lives outside `src`.
- **A-4**: A component's package has the name of its subcommand.

## Mechanisms

- `tach check`, configured in `tach.toml`, enforces the dependency table
  between the `.py` code of the packages of `src/wio`.
- A `prek` hook runs `tach check`, so `make lint`, `make check` and the
  continuous integration cover it.
- `typing.Protocol` classes in `.pyi` stubs declare the ports, and `pyrefly
  check` verifies that their names and signatures resolve.
- `argparse` subparsers, one per command, and Python 3.15 `lazy from ... import`
  in `wio.cli`, which each component's Work adds with its command.
- `pytest.mark.xfail(strict=True)` marks the scenario that waits for the `cli`
  package.

## Constraints

- **Dependency direction**: `wio.models` imports nothing else from `wio`;
  `wio.formats` and `wio.io` import only `wio.models`; a component imports only
  `wio.models`, `wio.formats` and the ports of `wio.io`; `wio.cli` is the only
  package that imports the commands of the components and the adapters in
  `wio.io.adapters`.
- **No component imports another component.** They meet only in `wio.cli`, which
  gives each the implementation of the ports it consumes.
- **Ports are owned by their consumer**, declared in `<package>/ports.pyi`,
  imported only under `TYPE_CHECKING`, and satisfied structurally, so a provider
  never imports the stub of its consumer. The exception is `wio.io`, whose ports
  for the filesystem, standard streams, git and the environment are shared
  infrastructure that `wio.io` owns in `io/ports.pyi`.
- **A shared-type stub is the spec until the Work that implements the type
  replaces it**: that Work writes a `.py` with the same annotations and
  docstrings and deletes the stub, while a port stays a `.pyi` for good.
- **One adapter per port.** An extra adapter needs a reason that the contract of
  the Work that adds it states.
- **Components reach the filesystem, standard streams, git and the environment
  only through the ports of `wio.io`.** The architecture review of each Work
  verifies it, because no tool checks it yet.
- **A dependency that exists only for a type is still a dependency**, so tach is
  set to count `TYPE_CHECKING` imports.

## Visuals

The before state is drawn from `main` at commit `125ea3e` and checked against
`src/wio`, `tests`, `scripts`, `pyproject.toml` and `prek.toml` at that commit.
The after state is provisional, and the packages and their edges are required
while the names inside each `ports.pyi` are not.

Before: one placeholder module, and `tach` installed but not configured.

```mermaid
flowchart LR
    subgraph src_wio["src/wio"]
        init["__init__.py"]
        cli["cli.py: hello()"]:::replaced
    end
    subgraph tests
        unit["unit/test_cli.py"]:::replaced
        pack["packaging/"]
        tscr["tests/scripts/"]
    end
    rec["scripts/records.py"]
    unit --> cli
    pack -. "builds" .-> src_wio
    tscr --> rec
    tach["tach: dev dependency only"]:::absent
    classDef absent stroke-dasharray: 4 3
    classDef replaced stroke-width: 3px
```

After: layers with one direction, one hook that checks them, and the test
setup that drives the command. The bold boxes replace `cli.py` and its test.

```mermaid
flowchart LR
    subgraph src_wio["src/wio"]
        cli["wio.cli (composition root)"]:::new
        subgraph components
            config
            contract
            rule
            trailers
            log
            context
        end
        adapters["wio.io.adapters"]:::new
        io["wio.io (ports)"]:::new
        formats["wio.formats (codecs)"]:::new
        models["wio.models (shared types)"]:::new
        cli -- "lazy import of commands" --> components
        cli --> adapters
        cli --> io
        cli --> formats
        cli --> models
        adapters --> io
        components -- "ports" --> io
        components --> formats
        components --> models
        formats --> models
        io --> models
    end
    hook["prek hook: tach check"]:::new -. "checks the .py edges" .-> src_wio
    acc["tests/acceptance: DSL and drivers"]:::new -- "drives" --> cli
    classDef new stroke-width: 3px
```

## Acceptance criteria

### **AC-1** The delivered foundation passes every check

With every child Work delivered, `make check` and `make slow` pass, the
dependency check and the type check are among the hooks they run, and the
scenario for the bare `wio` command is reported as expected to fail.

#### The whole tree

- **Given** the tree with every child Work delivered.
- **When** `make check` runs, and then `make slow`.
- **Then** both exit 0, the output lists the `tach check` and `pyrefly check`
  hooks as passed, and the bare-`wio` scenario is reported as xfailed, once in
  each run.

### **AC-2** The layout and the dependency rules describe the same packages

Every package directly under `src/wio` is a module in `tach.toml`, and the only
other module there is `wio.io.adapters`, so the checked graph is the one the
constraints state.

#### Same packages

- **Given** the delivered tree.
- **When** the packages under `src/wio` are compared with the modules in
  `tach.toml`.
- **Then** the lists are equal apart from `wio.io.adapters`, and each module's
  allowed dependencies are those of the dependency direction constraint.

## Additional context

- [v0.1 scope](../../../../docs/v0.1-scope.md) names the components and their
  order of work; the skeleton leaf updates it to match this Work.
- [Test strategy](../../../../tests/README.md) describes the DSL that the test
  leaf builds.
