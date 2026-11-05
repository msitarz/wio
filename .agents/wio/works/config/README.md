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

**Shape.** A parent, after the cli Work (9wbqyb), with six leaves and a nested
parent for the checks. A leaf is cut at a behavioral boundary, so each has
criteria a reviewer can judge alone.

```text
config (parent)
├─ ports      Repository, History, LocalFileSystem, GitRepository
├─ decoder    decode_toml, TomlSyntaxError, the tomllib ban
├─ model      Config, Diagnostic, the renderer, ConfigurationError.diagnostics
├─ loader     discovery, shape diagnostics, sources, Settings
├─ show       bare help, wio config list, wio config show
└─ checks (parent)
   ├─ command          wio config check on the shape diagnostics, the prek
   │                   hook, the PostToolUse hook, the recipe
   ├─ pipelines        actions, stage presets, stages, results, roots,
   │                   works.defaults.actions, goal or skill
   ├─ rule selection   name forms, rule presets and cycles, always fields,
   │                   rulesets, aliases and their directories
   └─ paths and skills root paths, skill lookup, the [templates] shape
```

Ports, decoder and model are independent. The loader needs all three; `show`
and `command` need the loader; the three check leaves need `command` and are
independent of each other. `command` comes first among the checks as a walking
skeleton: it prints the shape diagnostics, so every later check is seen working
through `wio config check`, and the hooks exist from the start. The `checks`
parent's criteria are system-level: one pass reports every diagnostic, sorted,
every error check is also enforced by `Settings.load`, and `wio config check`
passes on this repository's config.

1. Ports and adapters in `wio.io`: `LocalFileSystem` for the `FileSystem` port,
   and `Git` split in two by what each member asks. `Repository` is where the
   process is now (`root`, `identity`, `show_index`, `is_dirty`; `identity` is
   today's `common_dir`, described as the path shared by every checkout of one
   clone), with the adapter `GitRepository` that runs `git rev-parse` in the
   working directory through a subprocess; this Work implements only `root` and
   `identity`, and the other two stay declared until the trailers Work needs
   them. `History` is revision-based reading (`rev_parse`, `history`,
   `first_parents`, `list_files`, `show`), and its adapter is the trailers
   Work's. The names carry no git word, so another VCS can be adapted behind the
   same ports. The rename reaches `wio.models.commits`, the trailers ports, the
   glossary and the architecture README. pygit2 has no Python 3.15 wheel
   (tested 2026-11-03) and `git` is needed anyway for the `git` trailer reader,
   so pygit2 may become another adapter later. No `Environment` adapter.
2. A TOML decoder in `wio.formats`: `decode_toml(text) -> dict[str, object]`,
   which imports `tomllib` lazily. A syntax error, a duplicate key and an
   invalid value raise `TomlSyntaxError(WioError)`, declared in
   `wio.formats.errors`, with `message`, `line` and `column` and no file name:
   the caller adds the file, and the contracts Work offsets the position for a
   metadata block. The exception, not a result, because `check` stops at a
   syntax error. A ruff banned-api rule (TID251, which also flags the `lazy`
   forms) bans `tomllib` outside `src/wio/formats/**`; `tomlkit` is banned
   when the first writer needs it. The HTML-comment metadata reader belongs to
   the contracts Work.
3. The schema as plain frozen dataclasses in `wio.models.config` replacing the
   `models/config.pyi` stub, with `Diagnostic` in `wio.models`, the renderer
   in `wio.formats` and `ConfigurationError.diagnostics`. The open tables are
   `frozendict` (Python 3.15's built-in), lists are tuples, and one helper in
   `wio.models` builds every `frozendict` under a single narrow pyrefly
   suppression ([known issues](../../../../docs/known-issues.md)).
4. The loader: discovery, shape diagnostics, `sources` and the `Settings`
   adapter.
5. `wio config` (help), `wio config list` and `wio config show`.
6. The `checks` parent and its four leaves.

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

**Messages.** A diagnostic is written so that an agent can correct its edit in
one step. An unknown key names the valid sibling keys and the closest match
(`difflib`, imported only when a diagnostic needs it). A wrong type or value
names the key path, the received value, the expected type or the allowed
values, and a one-sentence description of the key. A stage with both or neither
of `goal` and `skill` says what each is. No value is coerced: an integer where
a string belongs is an error, and a TOML date or time is always an error. Each
`Config` field carries its description in `dataclasses.field(metadata=...)`,
which the loader reads from the schema it already walks; `docs/concepts.md`
stays the canonical meaning, and the descriptions are one short sentence each.

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

**Checks.** Only what config can verify alone, reading the config and listing
directories. Errors: a TOML syntax error (`file:line:column`), an unknown key, a
wrong type, a value outside its vocabulary (`hierarchy`, `reader`, `session`,
`judge`), the shape of the `[templates]` table; the cross-references among
actions, stage presets, `[works.defaults.actions]`, stages, results and roots,
with no stage twice in a pipeline and no `after` cycle; among config rule
presets (bare names), with their cycles; the forms of names and qualified
references; a preset in `rules_always_exclude`; a `rules_*` key where none
belongs; a reference, a `[rulesets.<name>]` entry or an alias whose ruleset has
no directory, a directory without `ruleset.toml`, and a duplicate or clashing
alias (the part before the dot of a reference is a directory name or an alias,
both resolved from the config and the directory listing; the item after it waits
for the rules Work); root paths that are not normalized, leave the repo or
repeat in one root; a stage with both or neither of `goal` and `skill`; and a
stage's skill found nowhere in `[skills] paths`, `.agents/skills` or
`.claude/skills`. The user's home is never searched: a skill belongs to the
repo. Warning: a root path that does not exist yet. Notes: an `invalidated_by`
entry with another `@` prefix, which v0.2 reserves, and `rules_always_include`.
Nothing reports an unused stage, root or preset, because templates and contracts
also name them, which config cannot see. `wio config check` reads no template
and does not check that a kind's entry template exists: `wio templates check`
does. Checks that parse a template or a rule (a template's kind, its directives,
a ruleset's manifest, codes, families and presets, whether a qualified reference
resolves, and whether a root reaches a root-independent ruleset) are deferred:
each is added by the contracts, templates or rules Work as part of its own
delivery, and the contracts of those Works must say how they add a check.

**Open.** The criteria of each leaf.
