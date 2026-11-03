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
- A package with errors of its own extends the same base without importing
  another package.
- The configuration error that several components share has one definition.

## Non-Goals

- Catching the errors, which the command-line leaf does.
- The errors of any component, each of which its package adds in its own
  `errors.py` when it has one.
- An exit code per error class: every `WioError` means exit 2.

## Assumptions

- **A-1**: Nothing raises `ValueError` for the settings yet: only the docstring
  of `Settings.load` in `src/wio/ports.pyi` mentions it, at commit
  `16dbe2d636c984a42cb976ec50c272d790f10233`.

## Mechanisms

- `src/wio/errors.py`, a plain module of exception classes.
- A `wio.errors` module in `tach.toml` with no dependencies, which every other
  module of `src/wio` and the unit tests list among theirs.

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
- **Then** it is caught, `str` of it is `no config at /x`, and it is not an
  instance of `ValueError`.

### **AC-2** `wio.errors` depends on nothing and every package may use it

`tach.toml` declares `wio.errors` with no dependencies and lists it among the
dependencies of every other module of `src/wio` and of `tests.unit`.

#### A clean tree and an allowed import

- **Given** the delivered tree, and a `.py` module in `wio.models` that imports
  `wio.errors`, added locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits 0.

#### A forbidden import

- **Given** a `.py` module in `wio.errors` that imports `wio.config`, added
  locally by the reviewer and not committed.
- **When** `uv run tach check` runs.
- **Then** it exits non-zero and its output names `wio.errors` and
  `wio.config`.

### **AC-3** The settings port names the shared error

`Settings.load` in `src/wio/ports.pyi` documents that it raises
`ConfigurationError` where it said `ValueError`.

### **AC-4** The architecture documents state the rule

The `README.md` of `src/wio` states that `wio.errors` imports nothing from
`wio`, that every package may import it, that errors several packages share live
there, and that a package adds an `errors.py` extending `WioError` only when it
has an error of its own. Its dependency table lists `wio.errors`.
