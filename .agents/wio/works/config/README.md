<!-- wio
id = "hwn995"
template = "feature.draft"
roots = []
depends_on = ["9wbqyb"]
-->

# The wio config command

## Purpose

Every command needs the project's settings read from one file and checked, and
a person needs to see what they are and where each value comes from.

## Intent

From the interview of 2026-11-03. Decisions are made unless marked open.

**Shape.** A parent with five leaves, after the cli Work (9wbqyb):

1. Adapters: a `FileSystem` adapter in `wio.io`, and a `Repository` port in
   `wio.io` (split from `Git`: `root` and `common_dir`; the history members stay
   in `Git` for the trailers Work) with an adapter that runs `git rev-parse` in
   the working directory through a subprocess. pygit2 has no Python 3.15 wheel
   (tested 2026-11-03) and `git` is needed anyway for the `git` trailer reader,
   so it may become a second adapter behind the same port later. No
   `Environment` adapter.
2. A TOML decoder in `wio.formats`: a function, with its own error type that
   carries line and column. Only `wio.formats` may import `tomllib` or
   `tomlkit`, enforced by a ruff banned-api rule that is verified first. The
   HTML-comment metadata reader belongs to the contracts Work.
3. The schema and the loader: frozen dataclasses replacing the
   `models/config.pyi` stub, the `Settings` adapter, discovery and errors.
4. `wio config` and `wio config list <kind>`.
5. `wio config check`.

The parent also proves it end to end: `wio config check` passes on this
repository's `.agents/wio/config.toml`, its stale "Nothing reads this file yet"
header is updated, and `wio config check` runs as a prek hook.

**Schema.** The shapes of this repository's config are ratified: top-level
`tags` and `results` arrays, tables `[types]`, `[trailers]`, `[actions.<name>]`,
`[stages.<name>]` and `[presets]`, and `[[roots]]`. Unknown keys are an error
when loading. A stage's session policy is `session` (`"any"` by default, or
`"fresh"`) and `continuable` (`true` by default). Defaults: `results` is
`["pass", "fail", "unknown"]`, `[trailers] reader` is `"scan"`, `[skills] paths`
is empty, `[bundle] separator` is a blank line (`"\n\n"`), and `[bundle]
size_threshold` (characters) is absent, meaning no warning. The other tables
default to empty.

**Discovery.** The config is `<git root>/.agents/wio/config.toml`, where the git
root is that of the working directory. There is no walk-up and no per-directory
override. Outside a git repository, or with no file, is a configuration error
(exit 2); an empty file is valid. The message for a missing file does not
mention `wio init`, which comes in v0.2.

**Commands.** `wio config` shows the effective settings, each value labelled
`file` or `default`; `wio config list <kind>` prints the names of types,
actions, roots, stages, presets, tags or results; `wio config check` prints one
line per finding, `error|warning|note: <where>: <message>`, sorted, and exits 1
on any error. All three take `--json`; output is sorted, with no timestamps. The
bare `wio config` does not run the checks.

**Checks.** Only what config can verify alone: the cross-references among
actions, presets, stages, tags, results and roots, `after` cycles, `judge`,
root paths (normalized, inside the repo, no duplicates, a missing path is a
warning), skill lookup, and that each type's entry template file exists, taking
the template's name to be its file name (an assumption for the contracts Work
to settle). Checks that parse a template or a rule (a template's type, its
directives, a ruleset's manifest and codes, rule tags and types) are deferred:
each is added by the contracts or rules Work as part of its own delivery, and
the contracts of those Works must say how they add a check.

**Open.** Nothing yet; the criteria of each leaf are next.
