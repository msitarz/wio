# Glossary

Terms used by wio, the Work It Out engine. Use these names in code, docs and
commit messages.

| Term | Meaning |
| --- | --- |
| Work | One outcome with its behaviors, described by a contract. A directory whose `README.md` has a `wio` metadata block. |
| Work contract | The markdown file, with a metadata block, that states a Work's intent. It follows a template. |
| Leaf | A Work without child Works. |
| Parent | A Work with child Works. Its roots are the ones it lists; `@descendants` among them adds the union of its descendants' roots. |
| Template | A markdown file that shapes a contract: sections, directives and a metadata block with the template's name, type, optional shape (leaf or parent) and default actions. |
| Type | A kind of outcome, such as `feature`, declared in the config with its entry template. A type groups templates. |
| Entry template | The template of a type that new Works of that type start from. Declared in the config. |
| Metadata block | The TOML at the top of a contract, template or rule, in a hidden comment or between `+++` lines. |
| Directive | A `wio:` instruction in an HTML comment on a template heading, such as `required` or `inherit`. |
| Dependency | A Work id in `depends_on`: that Work must be delivered first. |
| Action | A named kind of work done on a Work, such as `define` or `deliver`. Declared in the config with a description, the actions it comes after, what invalidates its work, and whether it is on demand; none are built in. Its pipeline is a preset or a list of stages. |
| Config | The `.agents/wio/config.toml` file: types, actions, roots, stages, presets, tags, results, the rules chosen from each ruleset, skill directories, the trailer reader, and bundle settings. |
| Root | A named set of directories (its `paths`) bound to one toolchain and its rulesets. Works and stages refer to it by name. |
| Ruleset | A reusable collection of rule files with a `ruleset.toml` manifest. Bound to roots, and its rules chosen, by the repo's config. |
| Stage | A named step: a goal or a skill, tags, optional roots and a session policy. |
| Skill | A packaged procedure, with references, templates or scripts, that a stage can hand its work to. A directory with a `SKILL.md`, found in the config's skill directories or in those harnesses read. |
| Gate | A stage marked `gate = true`, which judges the previous stage's artifact; each of its records carries a result. A human approval is a gate too. |
| Result | A gate's decision, such as `pass` or `fail`, from the vocabulary the config declares. |
| Back-edge | Returning to an earlier stage (or the contract) because a later one exposed a gap. |
| Preset | A named, ordered list of stages. It can be the pipeline of an action. |
| Rule | One atomic do/don't instruction with a reason, identified by a code such as `ARC001`. |
| Rule code | The stable identifier of a rule: a family prefix and a number. |
| Family | The letters of a rule code. They group rules by topic and belong to a ruleset. |
| Tag | A label from the config vocabulary that links rules to stages. A rule's effective tags are its own, unless the config overrides them. A rule without tags applies to every stage that selects its roots. |
| Bundle | The text `wio context` prints for a session. |
| Record | A paragraph of `Wio-*` git trailers in a commit message that says the commit is work on a stage of a Work, with its criteria and, for a gate, its result. |
| Driver | Whoever advances the Work: a human now, an orchestrator later. It chooses the action and the stage; wio only proposes. |
| Event log | Append-only record kept outside the repo, personal to one machine, for evaluation and cost analysis. |
