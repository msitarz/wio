# Glossary

Terms used by wio, the Work It Out engine. Use these names in code, docs and
commit messages.

| Term | Meaning |
| --- | --- |
| Work | One outcome with its behaviors, described by a contract. |
| Work contract | The markdown file with frontmatter that states a Work's intent. |
| Leaf | A Work executed directly. Touches exactly one root. |
| Parent | A Work delivered by its children. Its scope is derived. |
| Work type | A label (`feature`, `bugfix`, `investigation`, ...) that picks a template and a default preset. |
| Template | The skeleton and directives for one work type and level. |
| Config | The `.agents/wio/config.toml` file: roots, stages, presets, tags and work types. |
| Root | A named set of directories (its `paths`) bound to one toolchain and its rulesets. |
| Ruleset | A reusable bundle of rule files. Bound to roots by the repo. |
| Stage | A named step: a goal or a skill, tags, and optional approval and session policy. |
| Gate | A point where work stops for a decision. Built from an approval flag and/or a review stage. |
| Back-edge | Returning to an earlier stage (or the contract) because a later one exposed a gap. |
| Preset | A named, ordered list of stages. |
| Rule | One atomic do/don't instruction with a reason, identified by a code such as `ARC001`. |
| Rule code | The stable identifier of a rule: a family prefix and a number. |
| Family | The letters of a rule code. They group rules by topic and belong to a ruleset. |
| Tag | A label from the config vocabulary that links rules to stages. |
| Bundle | The text `wio context` prints for a session. |
| Driver | Whoever advances the Work: a human now, an orchestrator later. |
| Event log | Append-only record kept outside the repo for evaluation and cost analysis. |
