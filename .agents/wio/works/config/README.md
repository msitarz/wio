<!-- wio
id = "hwn995"
template = "feature.draft"
roots = []
depends_on = ["9wbqyb", "xxbge6"]
-->

# The wio config command

## Purpose

Every command needs the project's settings read from one file and checked, and
a person needs to see what they are and where each value comes from.

## Intent

From the interviews of 2026-11-03 and 2026-11-05. Decisions are made unless
marked open.

**Shape.** A parent with five leaves, after the cli Work (9wbqyb):

1. Ports and adapters in `wio.io`: a `FileSystem` adapter, and `Git` split in
   two by what each member asks. `Repository` is where the process is now
   (`root`, `identity`, `show_index`, `is_dirty`; `identity` is today's
   `common_dir`, described as the path shared by every checkout of one clone),
   with an adapter that runs `git rev-parse` in the working directory through a
   subprocess. `History` is revision-based reading (`rev_parse`, `history`,
   `first_parents`, `list_files`, `show`) and keeps its adapter for the trailers
   Work. The names carry no git word, so another VCS can be adapted behind the
   same ports. The rename reaches `wio.models.commits`, the trailers ports, the
   glossary and the architecture README. pygit2 has no Python 3.15 wheel
   (tested 2026-11-03) and `git` is needed anyway for the `git` trailer reader,
   so pygit2 may become another adapter later. No `Environment` adapter.
2. A TOML decoder in `wio.formats`: a function, with its own error type that
   carries line and column. Only `wio.formats` may import `tomllib` or
   `tomlkit`, enforced by a ruff banned-api rule that is verified first. The
   HTML-comment metadata reader belongs to the contracts Work.
3. The schema and the loader: frozen dataclasses replacing the
   `models/config.pyi` stub, `Diagnostic` in `wio.models`, the loader, the
   `Settings` adapter, discovery and errors.
4. `wio config` (help), `wio config list` and `wio config show`.
5. `wio config check`.

The parent also proves it end to end: `wio config check` passes on this
repository's `.agents/wio/config.toml`, its stale "Nothing reads this file yet"
header is updated, `wio config check` runs as a prek hook, and a PostToolUse
hook runs it after an agent edits the config. `docs/workflow.md` documents that
hook as a recipe, and this repository installs it. Integrations in the docs are
for third-party workflows such as superpowers, not for wio's own tools.

**Schema.** The shapes follow the rule selection in `docs/concepts.md` and the
tables of its config section: a top-level `results` array and the top-level
`rules_always_include` and `rules_always_exclude`; tables `[works]` (`dir`,
`hierarchy`, `defaults.actions`), `[templates]` (`dir`, `kinds`), `[trailers]`,
`[actions.<name>]`, `[stages.<name>]` (with `rules_include` and
`rules_exclude`), `[stage_presets]`, `[rule_presets.<name>]`,
`[rulesets.<name>]` (with `alias` and `root_independent`), `[roots.<name>]`
(with `rule_presets`), `[skills]` and `[bundle]`. There is no `tags` vocabulary,
no `[presets]` and no top-level `[kinds]`. This repository's own config already
has these shapes. **An unknown key is an error**, not a warning, so a mistyped
key name is caught the moment `wio config check` runs. A stage's session policy
is `session` (`"any"` by default, or `"fresh"`) and `continuable` (`true` by
default); wio does not read `continuable` yet, and it is in v0.1 so that people
and agents can read it. Defaults: `results` is `["pass", "fail", "unknown"]`,
`[trailers] reader` is `"scan"`, `[skills] paths` is empty, `[bundle] separator`
is a blank line (`"\n\n"`), and `[bundle] size_threshold` (characters) is
absent, meaning no warning. The other tables default to empty.

**Loading.** `Config` is a tree of plain frozen dataclasses in `wio.models`,
whose fields carry the defaults; a key the file does not set keeps its default.
It carries no provenance. One function in `wio.config` decodes the file, builds
`Config`, runs every check and returns `(config or None, diagnostics,
sources)`. `sources` maps every key path of the effective settings to `file` or
`default`, built by walking `Config`'s own fields and asking whether the decoded
file has that key, so it cannot drift from the schema; entries of the open
tables (`stages`, `actions`, `roots` and so on) are always `file`.
`Settings.load()` calls that function and returns only the `Config`: if any
diagnostic is an error it raises `ConfigurationError`, which carries all the
errors, not only the first. So no other component sees a config with errors,
and every error check runs on every command; error checks are therefore cheap
and local (paths, names, references), and none parses a template or a rule.
Only errors block; warnings and notes appear only in `wio config check`.

**Diagnostics.** `Diagnostic` is a frozen dataclass in `wio.models`, used by
every `check` command: a `severity` (`error`, `warning` or `note`), a `where`
(a free-form string: a key path for the config, an item id for a contract, a
file for a syntax error) and a `message`. It has no code in v0.1. One renderer
in `wio.formats` prints a sorted list as `error|warning|note: <where>:
<message>` lines or as `--json`, so every `check` prints the same.
`ConfigurationError` carries a `diagnostics` field, which needs `wio.models` to
import nothing from `wio` and `wio.errors` to import only `wio.models`; that is
PR #80, and a model never raises a `WioError` because parsing and validation
that can fail live in `wio.formats`. Semantic diagnostics name the key path,
for example `stages.review.rules_include[0]: unknown ruleset "docz"`, because
`tomllib` gives a position only for syntax errors, which are reported as
`<file>:<line>:<column>`.

**Discovery.** The config is `<git root>/.agents/wio/config.toml`, where the git
root is that of the working directory. There is no walk-up and no per-directory
override. Outside a git repository, or with no file, is a configuration error
(exit 2); an empty file is valid. The message for a missing file does not
mention `wio init`, which comes in v0.2.

**Commands.** Bare `wio config` shows the help of the component. `wio config
list` prints every setting as one line, `key.path = value  # file|default`,
with a long value shortened to one line. `wio config show [key.path]` prints one
setting or a subtree in full with its source; a table such as `stages` is a key
path, and without an argument it prints the whole config. `wio config check`
prints every diagnostic and exits 1 on any error. All three take `--json`;
output is sorted, with no timestamps. `list` and `show` refuse a config with
errors like any other command. There is no `--names` and no `list <kind>`: the
keys of a table are in `wio config show <table> --json`, and listing templates
and their kinds belongs to `wio templates`.

**Speed.** `wio config check` runs after every agent edit, so it imports only
what it needs: no `tomlkit`, and no `json` unless `--json` is given. Python
3.15's lazy imports are used wherever a module is not needed at start. The
criterion looks at `sys.modules` after a run, not at the clock.

**Checks.** Only what config can verify alone: the cross-references among
actions, stage presets, stages, results and roots; among config rule presets
(bare names), with their cycles; the forms of names and qualified references;
a preset in `rules_always_exclude`; a duplicate or clashing alias; a `rules_*`
key where none belongs; `after` cycles, `judge`, root paths (normalized, inside
the repo, no duplicates, a missing path is a warning), skill lookup, and the
shape of the `[templates]` table. `wio config check` reads no template and does
not check that a kind's entry template exists: `wio templates check` does.
Checks that parse a template or a rule (a template's kind, its directives, a
ruleset's manifest, codes, families and presets, whether a qualified reference
resolves, and whether a root reaches a root-independent ruleset) are deferred:
each is added by the contracts, templates or rules Work as part of its own
delivery, and the contracts of those Works must say how they add a check. The
exact list and the severity of each is open; it is settled next.

**Open.** The list of checks and their severities (leaf 5), and the criteria of
each leaf.
