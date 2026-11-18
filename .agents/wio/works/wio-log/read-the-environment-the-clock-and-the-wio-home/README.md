<!-- wio
id = "hnakzm"
template = "feature.leaf"
roots = ["wio"]
depends_on = []
-->

# Read the environment, the clock and the Wio home

## Purpose

The components of the event log read the variables of the process, the time and
the Wio home only through ports, and the engine has those ports but no working
adapter for them, since `ProcessEnvironment.get` raises `NotImplementedError`
and no `Clock` or `Directories` adapter exists; the engine needs the real ones
before a sink can write its first line.

## Goals

- A component reads a variable of the process through `Environment.get` and gets
  its value, or `None` when it is not set.
- A component reads the time through a `Clock` that gives seconds since the
  epoch.
- A component finds the Wio home through `Directories.wio_home`, by the rule of
  `docs/concepts.md`, without anything being created or tested.
- `ProcessDirectories.temp_dir`, which is not implemented yet, fails loudly and
  names itself.

## Non-Goals

- `Directories.temp_dir`, which the Work that first needs it gives its meaning.
- Creating the Wio home, which the first write does.
- A clock that can be set, which a test makes with a fake of the port.
- Reading the user's home directory for anything but the default Wio home.

## Assumptions

### A-1

`Path.home()` finds the user's home directory on Linux and macOS, and fails with
a `RuntimeError` when it cannot.

## Mechanisms

- **`ProcessEnvironment.get(name)`** — in `wio.env`, gives
  `os.environ.get(name)` as it is at the time of the call, so a value that is
  set to an empty string is returned as an empty string and the callers decide
  what an empty value means.
- **`SystemClock.now() -> float`** — in `wio.env`, gives `time.time()`.
- **`ProcessDirectories(environment: Environment)`** — in `wio.env`, the
  `Directories` adapter, whose `wio_home()` reads `WIO_HOME` through the
  environment it is given.
- **`ProcessDirectories.wio_home()`** — implements the rule of
  [The Wio home](../../../../../docs/concepts.md#the-wio-home) and of the
  `Directories.wio_home` docstring, and turns the `RuntimeError` of
  `Path.home()`, and a relative result of it, into an `OSError`.
- **The names** — the behaviors here are required, and the names of the new
  classes `SystemClock` and `ProcessDirectories` are provisional, so the
  architecture stage may rename them.
- **`ProcessDirectories.temp_dir()`** — raises a `NotImplementedError` that
  names `temp_dir`, until the Work that first needs it implements it.

## Constraints

### C-1

Only these adapters read the variables of the process, the clock and the
user's home directory, and a component outside `wio.env` gets them through the
ports. A reviewer's search for `os.environ`, `time.time` and `Path.home` outside
`wio.env` verifies it.

## Acceptance criteria

### **AC-1** A variable of the process is read as it is at the time of the call

A component that asks for a variable gets its value at that moment, so the
callers see what the process has.

#### Set, unset and empty

- **Given** a process with `WIO_TEST_VALUE=abc`, a name that is not set, and
  `WIO_TEST_EMPTY` set to an empty string.
- **When** `ProcessEnvironment.get` is asked for each.
- **Then** it gives `"abc"`, `None` and `""`.

#### A value that changes

- **Given** a process in which `WIO_TEST_VALUE` is set to `abc`.
- **When** a `ProcessEnvironment` reads it, the process sets it to `def`, and
  the same `ProcessEnvironment` reads it again.
- **Then** the two reads give `"abc"` and then `"def"`.

### **AC-2** The clock gives the time as seconds since the epoch

A component reads the current time as a float that a test can compare with the
system's.

#### A reading

- **Given** the times `before` and `after` that `time.time()` gives around the
  call.
- **When** `SystemClock().now()` runs.
- **Then** it gives a float `t` with `before <= t <= after`.

### **AC-3** The Wio home follows the rule of the design

A component finds the one directory where wio keeps its private state for the
user, and nothing is created or tested.

#### A home that `$WIO_HOME` names

- **Given** `$WIO_HOME` set to `wio-home-test` under a fresh temporary
  directory, a path that does not exist.
- **When** `wio_home()` runs.
- **Then** it gives that path, and the path still does not exist.

#### The environment it is given

- **Given** a `ProcessDirectories` built with a fake `Environment` whose
  `WIO_HOME` is `fake-home` under a fresh temporary directory, while the
  process's own `$WIO_HOME` is another path.
- **When** `wio_home()` runs.
- **Then** it gives the path of the fake `Environment`.

#### A home that changes

- **Given** one `ProcessDirectories` built with a fake `Environment` whose
  `WIO_HOME` is `a` under a fresh temporary directory.
- **When** `wio_home()` runs, the fake `Environment` is changed to give `b`
  under the same directory, and `wio_home()` runs again.
- **Then** the first gives `a` and the second `b`.

#### A home that cannot be written

- **Given** `$WIO_HOME` set to a path under a regular file.
- **When** `wio_home()` runs.
- **Then** it gives that path as it is and raises nothing.

#### The default home

- **Given** `$WIO_HOME` unset, then set to an empty string, and `Path.home()`
  patched to return `user-home-test` under a fresh temporary directory, a path
  that does not exist.
- **When** `wio_home()` runs for each.
- **Then** both give that path with `.agents/wio` below it, and `user-home-test`
  does not exist afterwards.

#### The user's home is read only when it is needed

- **Given** `$WIO_HOME` set to `wio-home-test` under a fresh temporary
  directory and a `Path.home()` that raises `RuntimeError`.
- **When** `wio_home()` runs.
- **Then** it gives that path.

#### A relative home

- **Given** `$WIO_HOME` set to `relative/dir`.
- **When** `wio_home()` runs.
- **Then** it raises a `ValueError` whose message names `WIO_HOME` and holds
  `absolute`.

#### A user home that cannot be found

- **Given** `$WIO_HOME` unset and a `Path.home()` that raises `RuntimeError`.
- **When** `wio_home()` runs.
- **Then** it raises an `OSError`.

#### A user home that is relative

- **Given** `$WIO_HOME` unset and a `Path.home()` that returns `Path("rel")`.
- **When** `wio_home()` runs.
- **Then** it raises an `OSError`.

### **AC-4** The other member of the port is left to the Work that needs it

An adapter that is wired where the port is expected tells a caller of the member
it does not implement, so a missing implementation is never silent.

#### The temporary directory

- **Given** a `ProcessDirectories`.
- **When** `temp_dir()` runs.
- **Then** it raises a `NotImplementedError` whose message holds `temp_dir`.
