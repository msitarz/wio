# `wio.log`

The component behind `wio log` (`show`, `review`) and the append-only event
sink used by `wio context` and `wio trailers --result`.

## Where the log is

Events live in JSON-lines files under the Wio home (`$WIO_HOME` or
`~/.agents/wio`), keyed by repository so worktrees of one clone share a log.
See [`wio.env`](../env/README.md) for home-directory resolution.

## Harness session

[`identify.py`](identify.py) identifies the active harness and session id from
the environment variables configured in
[log settings](../config/README.md#log-settings), falling back to time window
and working directory when unavailable.

## Appending an event

[`sink.py`](sink.py) writes one JSON line per event in a single append using
the [versioned line codec](../formats/README.md#event-log-lines). A write
failure never blocks the calling command: it emits a warning naming the path
(and advises configuring a harness write exception for `~/.agents/wio`).

## Showing recorded events

[`show.py`](show.py) reads the repository's event log and reports when each
stage of a Work was last entered and its recorded reviews.

## Recording a gate review without commit records

[`review.py`](review.py) implements `wio log review` for workflows that record
gate results only in the event log rather than in commit trailers.

## Modules

- Entry, ports & tests: [`command.py`](command.py), [`ports.pyi`](ports.pyi),
  [unit tests](../../../tests/unit/log/).
