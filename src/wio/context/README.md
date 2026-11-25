# `wio.context`

The component behind `wio context`, which prints what an agent session reads
before it starts a stage of a Work.
[The context compiler](../../../docs/concepts.md#11-the-context-compiler) says
what a [bundle](../../../GLOSSARY.md) holds and which properties it keeps.

Today the directory holds the shell of the command: it has no check of its
inputs and no composition of the bundle, so a run is refused, as
[`wio.cli`](../cli/README.md#the-table-of-commands) describes. Its terms are
those of the [repository glossary](../../../GLOSSARY.md).

## The shell of the command

The docstrings of [the package](__init__.py),
[the command](command.py), [the compiler](compiler.py) and
[the ports](ports.pyi) say what each guarantees, and the
[tests](../../../tests/unit/context) show each case.

- **The compiler and the command are apart.** The compiler judges the inputs
  and then composes, and the command writes what it returns. So the command is
  tested with a fake compiler, and a Work that adds a check or a way to deliver
  the bundle changes one of the two.
- **Every check runs before the composition,** so a refused input is never
  answered with a bundle, which would look like success.
- **The warnings are reported before the bundle is written,** so a delivery
  that fails does not hide them.
- **The command catches no error.** The
  [dispatch of `wio.cli`](../cli/README.md#failures-and-exit-codes) already
  tells a mistake of the user from a bug.
- **There is no `--json`,** because a session reads the printed text as it is.
- **The finished bundle is a [shared type](../models/bundle.py),** because the
  composition port names it and a
  [ports stub](../README.md#ports) imports nothing from its own package.
