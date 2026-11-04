# Glossary

Terms used by wio, the Work It Out engine. Use these names in code, docs and
commit messages.

| Term | Meaning |
| --- | --- |
| Work | The unit wio runs actions on: a directory whose `README.md`, its contract, has a `wio` metadata block. |
| Work contract | A Work's `README.md`: a metadata block that wio reads, and a Markdown body in the sections of the template it follows. What the body states is the workflow's. |
| Leaf | A Work without child Works. |
| Parent | A Work with child Works. Its roots are the ones it lists; `@descendants` among them adds the union of its descendants' roots. |
| Template | A markdown file that shapes a contract: sections, directives and a metadata block with the template's name, type, optional shape (leaf or parent) and default actions. |
| Type | A kind of Work, such as `feature`, declared in the config with its entry template. A type groups templates. |
| Entry template | The template of a type that new Works of that type start from. Declared in the config. |
| Metadata block | The TOML at the top of a contract, template or rule, in a hidden comment or between `+++` lines. |
| Directive | A `wio:` instruction in an HTML comment on a template heading, such as `required` or `inherit`. |
| Dependency | A Work id in `depends_on`: that Work must be delivered first. |
| Action | A named kind of work done on a Work, such as `define` or `deliver`. Declared in the config with a description, the actions it comes after, what invalidates its work, and whether it is on demand; none are built in. Its pipeline is a stage preset or a list of stages. |
| Config | The `.agents/wio/config.toml` file: types, actions, roots, stages, stage presets, rule presets, ruleset aliases, the always fields, results, skill directories, the trailer reader, and bundle settings. |
| Root | A named set of directories (its `paths`) with one toolchain, whose rule presets select the rules for its code. Works and stages refer to it by name. |
| Ruleset | A reusable collection of rule files with a `ruleset.toml` manifest, which may declare rule presets, named by its directory under `.agents/wio/rules/`. Bound to a root when the root's presets name it, or marked root-independent; the config may give it one alias. |
| Stage | A named step: a goal or a skill, optional roots, the rules it includes and excludes, and a session policy. |
| Skill | A packaged procedure, with references, templates or scripts, that a stage can hand its work to. A directory with a `SKILL.md`, found in the config's skill directories or in those harnesses read. |
| Gate | A stage marked `gate = true`, which judges the previous stage's artifact; each of its records carries a result. A human approval is a gate too. |
| Result | A gate's decision, such as `pass` or `fail`, from the vocabulary the config declares. |
| Back-edge | Returning to an earlier stage (or the contract) because a later one exposed a gap. |
| Preset | A named, reusable selection, of two kinds: a stage preset or a rule preset. |
| Stage preset | A named, ordered list of stages. It can be the pipeline of an action. |
| Rule preset | A named selection of rules, with `rules_include` and `rules_exclude`, declared in the config or in a `ruleset.toml`. |
| Layer | One source of a rule selection, applied in order: the rule presets of the roots a stage selects, the stage, `rules_always_include`, then `rules_always_exclude`. |
| Rule | One atomic do/don't instruction with a reason, identified by a code such as `ARC001`. |
| Rule code | The stable identifier of a rule: a family prefix and a number. |
| Family | The letters of a rule code. They group rules by topic and belong to a ruleset. |
| Bundle | The text `wio context` prints for a session. |
| Record | A paragraph of `Wio-*` git trailers in a commit message that says the commit is work on a stage of one or more Works, with its criteria and, for a gate, its result and who judged it. |
| Promote | To carry what a contract guarantees, with its reasons and diagrams, into the documents next to the code. |
| Retire | To delete a contract, which git history keeps, once what it guarantees was promoted. |
| Driver | Whoever advances the Work: a human now, an orchestrator later. It chooses the action and the stage; wio only proposes. |
| Fold | Merging the records of a pull request body: each Work's consecutive records of a stage become one, then neighbors that differ only in the Work become one list. The commits keep every record. |
| Event log | Append-only record kept outside the repo, personal to one machine, for evaluation and cost analysis. |
| Wio home | The directory where wio keeps its private state for one user: the one `$WIO_HOME` names when it is set to a non-empty absolute path, otherwise `~/.agents/wio`. In v0.1 it holds the event log. |
