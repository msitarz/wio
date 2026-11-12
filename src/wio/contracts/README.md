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

## Finding the Works

Every command that reads Works takes them from one value, `WorkDiscovery` in
[`discovery.py`](discovery.py), which one walk of the Works directory builds, so
no command walks the directory on its own and the commands cannot disagree about
which files are Works. The docstrings there say what each field holds and what
each function takes and returns, and the
[tests](../../../tests/unit/contracts/test_discovery.py) say how each case
reads. [Which files are Works](../../../docs/concepts.md#which-files-are-works)
defines what a Work is.

- **A problem with one Work hides no other, and none is raised.** Discovery
  reports every problem as a diagnostic, and the Works directory that cannot be
  walked is one error and no Work. Only a file that cannot be identified is left
  out. A Work with a wrong optional field stays in the tree
  with that field empty, so its children and dependents are not orphaned and a
  later command still sees them. A shared id keeps every Work that has it.
- **The errors say what they leave.** `incomplete` holds the errors that leave
  the tree incomplete, and `ambiguous` the errors of a shared id, because a
  command that needs the whole tree refuses on either, while one that looks a
  Work up refuses only the lookup of a shared id, through `find_work`. A command
  tests those two fields and never reads a message to decide.
- **A reason is computed from what was read.** `explain_not_a_work` walks the
  tree again and names the files of a collision, or the error of a file that was
  left out, from the files it read and the nesting rules, and never from the
  text of a diagnostic, so a file name that holds a colon or a comma has its
  reason. A path has a reason exactly when it is not among the Works found, and
  the reasons come in the order that the docstring lists.
- **Discovery reads and never writes.** It reaches files only through the
  `FileSystem` port, and its output is in a fixed order: the Works by the
  string of their paths and the diagnostics as the shared ordering puts them.
- **`Work` is in [`wio.models.works`](../models/works.py).** Its docstring holds
  its fields and the rule that the title is the first heading, at any level. It
  sits beside the stub `work.pyi`, which a later Work replaces, so that a stub
  and its implementation never share a module name.

The walk, the refusal of a Works directory and the ordering of diagnostics are
the [shared helpers](../io/walk.py) that the templates discovery also uses, so
the two read their directories the same way.

## The hierarchy of the Works

The parent, children, ancestors, descendants, resolved roots, dependencies and
dependents of a Work, and the errors of the dependency graph, come from one
value, `Hierarchy` in [`hierarchy.py`](hierarchy.py), that `build_hierarchy`
makes from the Works that discovery found. So every command gets the same
answer and none computes a relation from the files on its own. The docstrings
there say what each table holds, how it is ordered and what each error reads,
and the [tests](../../../tests/unit/contracts/test_hierarchy.py) say how each
case reads. [Parent and leaf](../../../docs/concepts.md#parent-and-leaf),
[roots of a Work](../../../docs/concepts.md#roots-of-a-work) and
[dependencies](../../../docs/concepts.md#dependencies) define the relations.

- **It is computed on each run from what it is given.** It reads no file and
  writes none, because the Works come from discovery, and nothing is kept
  between runs that could drift from the files.
- **The tables are keyed by path, not by id.** Two Works may share an id, and
  discovery keeps both, so an id would hide one of them. A dependency on a
  shared id is an edge to each Work that has it, and the duplicate itself is
  reported once, by discovery.
- **The parent comes from the layout alone.** A plain directory between two
  Works, or a directory whose Work was left out, is passed over, so a Work is
  never orphaned by a problem that discovery already reports. Under `flat` no
  Work has a relative, and `@descendants` resolves to nothing.
- **A child passes up what its own roots resolve to.** So a middle parent
  decides what reaches the top, and a parent that does not list
  `@descendants` hides the roots of its children from the Work above.
- **A parent's wait for its children is an edge of the graph and is not a
  dependency.** It counts when a cycle is searched for, so a child that lists
  its parent is found, but it adds no id to `dependencies` and makes no parent a
  dependent of its child. Where a pair has both a listed and an implicit edge,
  the edge is called listed, because that is the one a person can remove.
- **A group of Works that wait on each other is one error.** It is placed at the
  Work of the group with the smallest path and shows the shortest cycle from
  it, with ties taken by the smallest path, so one mistake gives one message
  that does not change with the order in which the Works were found.
- **The roots are not judged here.** Warnings about a root's name or about
  `@descendants` on a leaf belong to the command that checks Works, which reads
  the tables.

## The id and the place of a new Work

A new Work needs an id that no Work in the tree has and a place that cannot
clash with another Work or hide the new one from every command. Both are decided
in [`location.py`](location.py), apart from writing the contract, so that the
rules are stated and tested once. The docstrings there say what each function
takes, returns and refuses, and the
[tests](../../../tests/unit/contracts/test_location.py) say how each case
reads. [Identity and location](../../../docs/concepts.md#identity-and-location)
defines the rules for ids, the default place and `--path`.

- **Deciding writes nothing, and one guard writes.** `decide_place` only asks
  the file system what exists, and `write_new` is the one function that
  creates a file and refuses one that exists, so a contract is never
  overwritten. Two creators racing for one path are not handled, because the
  check and the write are two calls.
- **The id generator is a seam.** `IdGenerator` is the interface and `RandomIds`
  the one implementation, which reads bytes only from the `Entropy` port, so a
  test fixes every id. The loop that draws again until the id is free and gives
  up after 100 draws is `new_id`, and it knows nothing of where candidates come
  from. The tree is the only record it checks: an id that a deleted Work had is
  not avoided, because that needs the history, which `wio trailers` reads.
- **The alphabet has no `i`, `l`, `o` or `u`.** So an id is never mistaken for a
  digit when it is read aloud or typed.
- **A slug cannot hide the Work.** A slug that is given must be lowercase
  letters and digits joined by single `-`, so it cannot start with `.`, hold `/`
  or `..`, or leave the Works directory, and one that is derived from a title
  follows the same form. An empty `--slug` counts as given, so a typo is
  reported and not silently replaced by the title.
- **A path is judged as discovery would judge it.** A new file is accepted only
  when the next walk of the Works directory would find it as a Work, so it is
  under the Works directory, below no hidden directory, through no symbolic link
  and, under `nesting`, in a directory that holds no marked file, one that
  discovery left out or excluded included, because that file would make the
  directory a collision. The rules are repeated here from
  [`explain_not_a_work`](discovery.py)'s list and not shared with it, because
  here the file does not exist yet.
- **One call gives one error, the first that applies.** The order runs from the
  options, through the slug, the parent and the path, to what already exists, so
  a mistake in the arguments is reported before the file system is asked.
