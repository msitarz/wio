# `wio.contracts`

The component behind `wio contracts`: the group of subcommands that create,
list, check and show Work contracts. This directory holds the group and what
every subcommand shares, and each subcommand lives in a module of its own.
[`src/wio/README.md`](../README.md) is the architecture, and the
[glossary](../../../GLOSSARY.md) defines the terms.

## The group

[`__init__.py`](__init__.py) holds `ContractsSpec` and the table of subcommands,
`SUBCOMMANDS`, and [`command.py`](command.py) holds `ContractsCommand`, which
runs the subcommand that the arguments chose. Their docstrings say what each
takes and returns, and the
[tests](../../../tests/unit/contracts/test_command.py) say how each case reads.

- **A subcommand is one entry of the table.** The group knows nothing else of a
  subcommand, so adding one does not edit another, and the group is built once
  so that two subcommands delivered together do not both create it.
- **The table is in the package module, with its `configure` and its handler.**
  Describing a command loads no module of its package besides `__init__`
  ([import-light packages](../cli/README.md#import-light-packages)), and
  `configure` runs while `wio --help` is described. So an entry's `configure` is
  defined in `__init__.py`, and its handler is a function there that imports the
  subcommand's own module when it runs. A `lazy from` in the tuple would defer
  nothing, because the names are used as the tuple is built.
- **Bare `wio contracts` reads nothing.** It writes its help without a
  repository, a config or a command of git, so it works anywhere, even when the
  config has an error.
- **What a subcommand needs comes in `Services`.** The settings, the repository,
  the file system and the catalog are built in `wio.cli`, the one place where
  they meet the group, and a subcommand that needs another port adds a field.
- **A mistake the user must fix is a `ContractsError`.** It is a `WioError`, so
  the command line prints its message and exits 2, while a handler returns 0, or
  1 for a failed check, and never another code.

## The template catalog

`TemplateCatalog` in [`ports.pyi`](ports.pyi) is how `wio.contracts` asks for
the templates, so it never imports `wio.templates`, which satisfies the port
with [`TemplatesCatalog`](../templates/catalog.py) and which `wio.cli` hands to
the group. Its docstrings say what `find` and `is_rejected` return.

- **A rejected template is not a missing one.** A contract that follows a
  template `wio templates check` rejects is told so, and one that names a
  template that does not exist is told that, so the catalog gives both answers,
  and a template that discovery could not build is rejected and not found.
- **The templates are read once for each question.** The catalog discovers once
  for `find` and checks once for `is_rejected`, and loads the config once, so a
  command that asks about many contracts pays for one walk and one check.
