<!-- wio
id = "h4my0j"
template = "feature.leaf"
roots = ["wio", "repo"]
depends_on = ["ew60gw"]
-->

# The wio.errors module

## Purpose

A condition the user can fix must reach the command line as an error that every
package can raise and one place can catch, so `wio.errors` gives the packages a
shared base before any component raises its own.

## Goals

- Any package can raise an error that the command line reports as the user's to
  fix.
- A package with errors of its own can extend the same base without importing
  another package.
- The configuration error that several components share has one definition.

## Non-Goals

- Catching the errors, which the command-line leaf does.
- The errors of any component, each of which its package adds in its own
  `errors.py` when it has one.
- An exit code per error class: every `WioError` means exit 2.
- Changing the other ports that declare exceptions, such as `Environment` for a
  relative `$WIO_HOME`: the Work of each component decides that.
- Committing a test that proves `tach` rejects a forbidden import; the reviewer
  tries one locally instead.

## Assumptions

- **A-1**: Nothing raises `ValueError` for the settings yet: only the docstring
  of `Settings.load` in `src/wio/ports.pyi` mentions it, at commit
  `16dbe2d636c984a42cb976ec50c272d790f10233`.
- **A-2**: The promote-architecture Work (`ew60gw`) creates `src/wio/README.md`
  with the dependency direction of the packages of `src/wio`, which this Work
  extends with `wio.errors`.

## Mechanisms

- `src/wio/errors.py`, a plain module of exception classes.
- A `wio.errors` module in `tach.toml` with no dependencies, which every other
  module of `src/wio` and the unit tests list among theirs.
- A unit test that reads `tach.toml` with `tomllib`.

## Acceptance criteria

### **AC-1** Packages share one base error

Any package can raise `WioError`, or `ConfigurationError` for a problem with the
settings, and a caller can catch both as `WioError`.

```python
class WioError(Exception): ...


class ConfigurationError(WioError): ...
```

Neither is a `ValueError`, so a handler of `ValueError` never swallows them, and
`str` of either is the message it was raised with.

#### A configuration error is a wio error

- **Given** `ConfigurationError("no config at /x")` raised.
- **When** it is caught as `WioError`.
- **Then** it is caught, `str` of it is `no config at /x`, and neither it nor
  `WioError` is an instance of `ValueError`.

### **AC-2** `tach.toml` lets every package use `wio.errors`

`tach.toml` declares `wio.errors` with no dependencies, and every other module
of `wio` there, and `tests.unit`, lists it among its dependencies.

#### The table

- **Given** `tach.toml` of the delivered tree.
- **When** a unit test reads it.
- **Then** `wio.errors` has an empty `depends_on`, and every other `wio.*`
  module and `tests.unit` list `wio.errors`.

### **AC-3** `wio.errors` cannot import another package

An import from `wio.errors` of any other package of `wio` fails `tach check` and
names both modules.

#### A forbidden import

- **Given** a `.py` module in `wio.errors` that imports `wio.config`, added
  locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.errors` and
  `wio.config`.

### **AC-4** The settings port names the shared error

`Settings.load` in `src/wio/ports.pyi` documents that it raises
`ConfigurationError` where it said `ValueError`.

### **AC-5** The architecture documents state the rule

The `README.md` of `src/wio` states, in its dependency direction, that
`wio.errors` imports nothing from `wio`, that every package may import it, that
errors several packages share live there, and that a package adds an
`errors.py` extending `WioError` only when it has an error of its own. It names
`wio.errors` as the one `wio` module that `wio.models` and `wio.env` may import.

## Additional context

- [Settings port](../../../../../src/wio/ports.pyi) declares `Settings.load`,
  whose docstring AC-4 changes.
