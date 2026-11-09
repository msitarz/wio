# Glossary of `src/wio/config`

Terms of the config's loader and its checks. They bind to this directory and its
descendants, and the nearest `GLOSSARY.md` wins. The terms of the architecture
are in the [glossary of `src/wio`](../GLOSSARY.md), and those of the engine,
Config and Diagnostic among them, in the
[repository glossary](../../../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Source | Whether a setting's value comes from the `file` or is the `default`. `Loaded.sources` gives it for each key path, and `Config` does not carry it. |
| Shape | Whether the file's keys, types and values fit the schema. Whether the names a value refers to exist is a check, not the shape. |
| Setting | One leaf of the config that has a value, with its key path, its source and the one-sentence description of its field. A list is one setting, a table is none, and an optional setting that is not set is not one. |
| Key path | The dotted names that lead to a setting, such as `stages.define.session`. A list item adds its index, as in `stages.define.rules_include[0]`, and a key that contains a dot is quoted as in TOML, as `stages."a.b".goal`. |
| Check | A function from the `Config` and what it may read (`CheckInputs`) to diagnostics, with one concern, such as the names that stages use for one another. The checks are kept in `CHECKS`. |
| Check run | The loader's run of the shape and then every check, on a best-effort `Config` when the shape has errors. `wio config check` prints its diagnostics and `Settings.load` refuses on its errors. |
| Action cycle | Actions that come after one another, directly or through others, or one that comes after itself. The check reports one error for each such group. |
| Normalized path | A path relative to the repository root, with `/` as the separator and without a `.` or `..` segment, an empty segment, a trailing slash or a leading `/`; `.` alone is the whole repository. Every path the config names is one. |
| Reference | An entry of a root's `rule_presets`, of `rules_include`, `rules_exclude`, `rules_always_include` or `rules_always_exclude`: a bare name, which is a rule preset of the config, or `<ruleset>.<item>`. [The concepts](../../../docs/concepts.md#names-and-references) define its forms. |
