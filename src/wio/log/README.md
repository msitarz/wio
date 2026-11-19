# `wio.log`

The component behind `wio log`: it records the sessions and reviews of one
clone in the [event log](../../../docs/concepts.md#the-event-log) and reads them
back. The terms Port and Adapter are defined in the
[glossary of `src/wio`](../GLOSSARY.md).

## Where the log is

[`locate.py`](locate.py) is the one place that knows where a clone's log is and
which files it holds, so the sink that writes events and the command that reads
them cannot disagree. Its docstrings say what each function takes, gives and
raises, and the [tests](../../../tests/unit/log/test_locate.py) say how each
case reads. These guarantees and their reasons are not in them:

- **One directory for each clone, under the
  [Wio home](../../../docs/concepts.md#the-wio-home).** A place keyed by the
  working directory would give each worktree its own log and hide a session's
  events from the other worktrees of the same clone, so the key is the clone's
  identity, which every worktree shares and no other clone has.
- **The digest identifies the clone and the name is only for a person.** Two
  clones that have the same directory name, in different places, still get two
  logs, because the digest is of the identity's whole path. The name lets a
  person who lists the Wio home tell which repository a log is for, and nothing
  reads it back.
- **Locating the log creates nothing.** The first write creates the directory,
  so a command that only reads a log, or fails before it writes, leaves the Wio
  home as it found it.
- **A failure to locate is the failure of the port that caused it.** Outside a
  repository, or with a `$WIO_HOME` that is relative, the caller gets the error
  of the repository or of the directories unchanged, so it can tell the person
  what it says.
- **A reader finds every lowercase `.jsonl` file of a log, in the order the
  file system port lists them.** The sink appends only to `events.jsonl`; a
  reader does not rely on that being the only file, and a missing directory is
  a log with no events and not an error.
- **The identity is taken as given.** A symlinked checkout and its target are
  one clone, because git prints the real path of its common directory, so
  `locate.py` neither resolves nor compares paths itself.

## Harness session

[Session identification](identify.py) supplies the fields that let a reader
join an event to its harness transcript. The
[session tests](../../../tests/unit/log/test_identify.py) specify how built-in
and custom mappings, preferences and diagnostics affect those fields.

A nested run can inherit session variables from several harnesses. The
preference describes which of those harnesses to use for this run. Keeping
unresolved matches and valid ids gives a reader evidence when the inherited
environment is ambiguous.

The [log settings](../config/README.md#log-settings) limit which environment
variables can supply ids. `wio config check` validates the configured names.
Project authors need to verify that the named variables hold ids, since a
secret can satisfy the same shape check. The shape check assumes that
supported harnesses emit ids in the accepted form. Identification takes a
well-shaped id as supplied, without looking up its transcript.

## Appending an event

[`LogSink`](sink.py) is the adapter of [`EventSink`](../ports.pyi) that stamps
and records both kinds of event. It uses the shared session identification and
[versioned line codec](../formats/README.md#event-log-lines) so every producer
writes the same envelope. A single append keeps concurrent writers from
interleaving event lines on the local filesystem.

Recording is best effort so a command can still give its result when storage
is unavailable. The diagnostic identifies the write destination once it is
known. The default-home hint helps users recognize that a harness restriction
can prevent writes to the default location. The `WIO_LOG` switch lets users
opt out before location, including when the home is unavailable.

The [sink tests](../../../tests/unit/log/test_sink.py) cover stamping, switch
values and diagnostics. The
[trailers integration tests](../../../tests/integration/trailers/test_write.py)
exercise the real log shared across worktrees and the command's standard
streams.
