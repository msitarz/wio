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
| Key path | The dotted names that lead to a setting, such as `stages.define.session`. A list item adds its index, as in `stages.define.rules_include[0]`, and a key that contains a dot is quoted as in TOML, as `stages."a.b".goal`. |
| Check | A function from the `Config` and what it may read (`CheckInputs`) to diagnostics, with one concern, such as the references among stages. The checks are kept in `CHECKS`. |
| Check run | The loader's run of the shape and then every check, on a best-effort `Config` when the shape has errors. `wio config check` prints its diagnostics and `Settings.load` refuses on its errors. |
