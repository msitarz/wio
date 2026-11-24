# Glossary of `src/wio/rules`

Terms of selecting, listing and checking rules. They bind to this directory and
its descendants, and the nearest `GLOSSARY.md` wins. The terms of the
architecture are in the [glossary of `src/wio`](../GLOSSARY.md) and those of the
engine in the [repository glossary](../../../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Route | The chain of references from the outermost rule preset to the entry that named a rule, such as `backend`, `demo.recommended`, `demo.ARC`, which says how an expansion reached the rule. |
| Reach | A root reaches a ruleset when an include entry of its rule presets names a family, a code or a rule preset of that ruleset, even when excludes leave none of its rules selected, as [the concepts](../../../docs/concepts.md#how-a-rule-is-selected) say. |
| Origin | One way an include entry delivers a rule: the layer that holds the entry, the name of its root or stage, and the routes that led to the rule, which `wio rules list --explain` and `wio rules new` show as a chain. |
| Stray file | A marked rule file directly in `.agents/wio/rules/`, outside every ruleset, or a `ruleset.toml` below a ruleset's directory, which the discovery reports because no ruleset owns it. |
