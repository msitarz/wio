# Glossary of `src/wio/config`

Terms of the config's loader and its checks. They bind to this directory and its
descendants, and the nearest `GLOSSARY.md` wins. The terms of the architecture
are in the [glossary of `src/wio`](../GLOSSARY.md), and those of the engine,
Config, Diagnostic, Source, Shape, Key path, Check and Check run among them, in
the [repository glossary](../../../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Setting | One leaf of the config that has a value, with its key path, its source and the one-sentence description of its field. A list is one setting, a table is none, and an optional setting that is not set is not one. |
| Action cycle | Actions that come after one another, directly or through others, or one that comes after itself. The check reports one error for each such group. |
| Normalized path | A path relative to the repository root, with `/` as the separator and without a `.` or `..` segment, an empty segment, a trailing slash or a leading `/`; `.` alone is the whole repository. Every path the config names is one. |
| Reference | An entry of a root's `rule_presets`, of `rules_include`, `rules_exclude`, `rules_always_include` or `rules_always_exclude`: a bare name, which is a rule preset of the config, or `<ruleset>.<item>`. [The concepts](../../../docs/concepts.md#names-and-references) define its forms. |
