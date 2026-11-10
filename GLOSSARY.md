# Glossary

Terms used by wio, the Work It Out engine. Use these names in code, docs and
commit messages.

| Term | Meaning |
| --- | --- |
| Work | The unit wio runs actions on: a marked file under the Works directory, its contract. |
| Work contract | A Work's marked file: a metadata block that wio reads, and a Markdown body in the sections of the template it follows, if it names one. What the body states is the workflow's. |
| Marked file | A `.md` file under the Works directory whose `wio` metadata block, a `<!-- wio` comment or `+++` front matter that holds the marker, starts on its first line. |
| Marker | The key `wio = 1` in a contract's metadata, whose value is the version of the metadata format. |
| Leaf | A Work without child Works. Under the `flat` hierarchy mode every Work is a leaf ([Parent and leaf](docs/concepts.md#parent-and-leaf)). |
| Parent | A Work with child Works, which only the `nesting` hierarchy mode gives. Its roots are the ones it lists; `@descendants` among them adds the union of its descendants' roots. |
| Hierarchy mode | The setting `[works] hierarchy`, `flat` or `nesting`, which says whether directories give Works parents and children. |
| Sibling split | Splitting a Work into sibling Works, ordered by `depends_on`, instead of into its children; both hierarchy modes allow it, and it is not the `flat` mode. |
| Template | A markdown file that shapes a contract that names it: sections, directives and a metadata block with the template's kind, optional shape (leaf or parent) and default actions. |
| Kind | A sort of Work, such as `feature`, declared in the config's `[templates.kinds]` with its entry template. A kind groups templates. |
| Template name | The name of a template's file without `.md`, which `[templates.kinds]`, a contract's `template` key and `wio templates show` refer to. A template has no `name` key. |
| Entry template | The template of a kind that new Works of that kind start from. Declared in `[templates.kinds]`. |
| Metadata block | The TOML at the top of a contract, template or rule, in a hidden comment or between `+++` lines. |
| Directive | A `wio:` instruction in an HTML comment on a template heading, such as `required` or `inherit`. |
| Dependency | A Work id in `depends_on`: that Work must be delivered first. |
| Action | A named kind of work done on a Work, such as `define` or `deliver`. Declared in the config with a description, the actions it comes after, what invalidates its work, and whether it is on demand; none are built in. Its pipeline is a stage preset or a list of stages. |
| Config | The `.agents/wio/config.toml` file: kinds, actions, roots, stages, stage presets, rule presets, ruleset aliases, the always fields, gate results, skill directories, the trailer reader, and bundle settings. In memory it is the immutable `Config` that the loader builds from the file. |
| Diagnostic | One finding of a check: a severity, a place and a message, in one order wherever it is printed, shared by every `check` command. |
| Source | Whether a setting's value comes from the config file or is the default. `wio config list` and `show` print it beside each value. |
| Shape | Whether the config file's keys, types and values fit the schema. Whether the names a value refers to exist is a check, not the shape. It is not a template's `shape`, which is `leaf` or `parent`. |
| Key path | The dotted names that lead to a setting, such as `stages.define.session`. A list item adds its index, as in `stages.define.rules_include[0]`, and a key that contains a dot is quoted as in TOML, as `stages."a.b".goal`. |
| Check | Of the config: a function from the `Config` and what it may read to diagnostics, with one concern, such as the names that stages use for one another. |
| Check run | The loader's run of the shape and then every check, which `wio config check` prints and `Settings.load` refuses on. |
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
| Record | A paragraph of `Wio-*` git trailers in a commit message that says the commit is work on a stage of one or more Works, with the item ids it addresses and, for a gate, its result and who judged it. |
| Promote | To carry what a contract guarantees, with its reasons and diagrams, into the documents next to the code. |
| Retire | To delete a contract, which git history keeps, once what it guarantees was promoted. |
| Driver | Whoever advances the Work: a human now, an orchestrator later. It chooses the action and the stage; wio only proposes. |
| Fold | Merging the records of a pull request body: each Work's consecutive records of a stage become one, then neighbors that differ only in the Work become one list. The commits keep every record. |
| Event log | Append-only record kept outside the repo, personal to one machine, for evaluation and cost analysis. |
| Repository | The working tree the process runs in and the state of its index and changes, as the `Repository` port tells it. |
| History | The revisions of a repository, read by revision and never changed, as the `History` port gives them. |
| Identity | The path that every checkout of one clone shares, so that worktrees of one clone are one repository. |
| Wio home | The directory where wio keeps its private state for one user: the one `$WIO_HOME` names when it is set to a non-empty absolute path, otherwise `~/.agents/wio`. In v0.1 it holds the event log. |
