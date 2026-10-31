# Glossary

Terms used by wio, the Work It Out engine. Use these names in code, docs and
commit messages.

| Term | Meaning |
| --- | --- |
| Work | One outcome with its behaviors, described by a contract. |
| Work contract | The markdown file, with a metadata block, that states a Work's intent. It follows a template. |
| Leaf | A Work without child Works. It has exactly one root. |
| Parent | A Work with child Works. It has no root of its own: its scope is derived from its children. |
| Template | A markdown file that shapes a contract: sections, directives and a metadata block with the template's name, type and default actions. |
| Type | A kind of outcome, such as `feature`, declared in the config. A type groups templates. |
| Metadata block | The TOML at the top of a contract, template or rule, in a hidden comment or between `+++` lines. |
| Directive | A `wio:` instruction in an HTML comment on a template heading, such as `required` or `inherit`. |
| Dependency | A Work id in `depends_on`: that Work must be delivered first. |
| Action | A named kind of work done on a Work: `define` or `deliver`. Its pipeline is a preset or a list of stages. |
| Config | The `.agents/wio/config.toml` file: roots, stages, presets, tags and template types. |
| Root | A named set of directories (its `paths`) bound to one toolchain and its rulesets. Contracts refer to it by name. |
| Ruleset | A reusable bundle of rule files. Bound to roots by the repo. |
| Stage | A named step: a goal or a skill, tags, and optional approval and session policy. |
| Skill | A packaged procedure, with references, templates or scripts, that a stage can hand its work to. |
| Gate | A point where work stops for a decision. Built from an approval flag and/or a review stage. |
| Back-edge | Returning to an earlier stage (or the contract) because a later one exposed a gap. |
| Preset | A named, ordered list of stages. It can be the pipeline of an action. |
| Rule | One atomic do/don't instruction with a reason, identified by a code such as `ARC001`. |
| Rule code | The stable identifier of a rule: a family prefix and a number. |
| Family | The letters of a rule code. They group rules by topic and belong to a ruleset. |
| Tag | A label from the config vocabulary that links rules to stages. |
| Bundle | The text `wio context` prints for a session. |
| Driver | Whoever advances the Work: a human now, an orchestrator later. It chooses the action and the stage; wio only proposes. |
| Event log | Append-only record kept outside the repo for evaluation and cost analysis. |
