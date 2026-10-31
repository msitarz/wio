# wio core concepts

This document explains the engine of wio: the few concepts everything else is
built from. It does not describe a particular process. The contract-to-
implementation flow (typed architecture, wired skeleton, implementation) is one
preset that can run on this engine, and it appears only as an example at the
end. Terms are defined in the [glossary](../GLOSSARY.md). Open points are
listed in section 14.

## 1. What the engine is for

A coding agent produces better work when three things are true:

1. It knows what outcome is wanted, and the human has confirmed that
   understanding before expensive work starts.
2. At each step it sees only the guidance that applies to that step, not every
   rule the project has.
3. A human or a fresh reviewer can stop the work at a chosen point and look at a
   small artifact, not at a finished 800-line diff.

wio's engine provides exactly these three things, through a handful of
concepts:

| Need | Concept |
| --- | --- |
| Know the intended outcome | **Work contract**, written from a **template** |
| Break big outcomes into small ones | **Nesting** (parent and leaf Works) |
| Name the kinds of work done on an outcome | **Action** (define, deliver) |
| Do an action in separate steps | **Stage** |
| Stop and decide between steps | **Gate** |
| Give each step only its own guidance | **Rules**, selected by tags and compiled into context |

In one sentence: wio runs **actions** on an **outcome**. An action is a
**preset**, an ordered list of stages, some of them gates. A **template** binds
a type of outcome to its actions, rules are selected for every stage, and every
step is logged. Everything else (skills, presets, rulesets, the event log)
plugs into these.

The engine prepares and describes the work; it does not move it forward. That is
the job of a **driver**: whoever advances a Work through its stages. Today the
driver is a human, later it can be an orchestrator. The driver names the action
and the stage, honors the gates and decides what happens after a back-edge. The
engine never decides these things itself. It can propose the next step, and it
warns about inconsistencies, but it never blocks a choice.

```mermaid
flowchart LR
    T[Template] --> C[Work contract]
    C --> A[Action]
    A --> S[Stage]
    S --> G[Gate]
    G -->|approved| S2[Next stage]
    G -->|gap found| S
    G -->|intent wrong| C
    R[Rules] -->|selected by tags and root| X[wio context]
    C --> X
    S --> X
    X --> AG[Agent session]
```

## 2. Work contract

### What it is

A Work contract is a markdown file that states one outcome and the behaviors
that show it has been achieved. It records **intent**: what should become true,
and why.

It is deliberately not a plan, a task list or a progress report. The reason is
mechanical. Intent changes rarely and by deliberate decision. Progress changes
constantly. If both live in one file, every stage edits the same lines and the
file turns into a conflict magnet. So the contract holds intent, and progress
lives elsewhere (see section 11).

### Anatomy

A contract has a small block of metadata for scripts and markdown sections for
people and agents.

The metadata is TOML. It sits inside an HTML comment at the top of the file, so
it is hidden when the contract is rendered and readable in the source:

```markdown
<!-- wio
id = "k3m9xq"
template = "feature.leaf"
root = "api"
depends_on = ["a7b2c4"]

[actions]
deliver = ["implementation"]
-->

# Short outcome title
```

- `id`: a short random id.
- `template`: the name of the template this contract follows. The template
  carries the type and the default actions.
- `root`: the name of the root the Work touches (see section 4). Only a Work
  without children has one.
- `depends_on`: an optional array of Work ids that must be delivered first (see
  section 4).
- `[actions]`: optional. When present it replaces, in full, the actions the
  template defines (see section 5).

Contract metadata carries no comments. Explanations belong to the template.

The title is the first heading and is stored nowhere else. There is no `parent`
field, because the directory layout gives the hierarchy (see section 4).

The body is prose. A typical contract has a purpose, goals and non-goals, an
explicit list of assumptions, and acceptance criteria (the behaviors).
Assumptions and criteria carry ids (`A-1`, `AC-1`) so that a later amendment can
say precisely what changed.

Why prose and not a strict schema? Because the reader is mostly an agent, and an
agent reads prose well. Scripts only need the metadata and a few required
sections, so only those are machine-checked.

### Metadata forms

wio also reads the same TOML as front matter between `+++` lines. A template
picks the form, and contracts made from it use the same form. The templates in
this repository use the comment form because GitHub shows `+++` front matter as
plain text, while other forges, GitLab for example, render it. A setting for the
form, and a command that rewrites it, may come later.

TOML was chosen over YAML, for now, for simplicity: it needs only the standard
library for reading, and strings are always quoted, so an id such as `234567` is
never read as a number. The choice is cheap to change: add a YAML reader and
writer (using a safe load) and change the templates.

### Identity and location

- The `id` is random and short (6 to 8 base32 characters). It is generated, not
  written by a model, because models invent or duplicate ids. It is not a UUID
  (too long, untypeable) and not a ticket key (that would tie wio to one
  tracker).
- Each Work is a directory named for its slug, with the contract inside:
  `.agents/wio/works/<slug>/README.md`. The path is the default and will be
  configurable. Humans navigate by slug and scripts key on the id.

### Changing a contract

Later stages can reveal that the contract was wrong or incomplete. That is
normal, not a failure. The rule is that a downstream stage **proposes** a change
and the human decides. The decision has three outcomes:

- **Abandon**: stop this Work.
- **Amend**: change the acceptance criteria or assumptions, then rework whatever
  depended on them.
- **Ratify**: update the contract to match what was built, without reworking
  anything.

Ratify is the cheap option and the one to watch. Used too often, it turns the
contract from a statement of intent into a log of what happened.

Changes to the contract file, including the step where a definition is finished
and the contract becomes complete, are changes of intent. They are made in the
repository and reviewed like any other change.

## 3. Templates and types

### What a template is

A template is a markdown file that shapes a contract: instructional comments,
directives and a metadata block. Its metadata describes the template itself and
what the contracts made from it look like:

```markdown
<!-- wio
name = "feature.leaf"
type = "feature"
description = "A capability delivered directly as one coherent outcome."

[actions]
deliver = "typed-boundary"

[contract]
root = ""
depends_on = []
-->
```

- `name` is the template's unique name. Two templates cannot share a name, and
  the file name does not matter.
- `type` is the template's type, one of the types the config declares.
- `description` is what tools show when they list templates.
- `[actions]` holds the default actions of every contract that follows the
  template (see section 5).
- `[contract]` is the metadata of the contracts the template produces.

### From template to contract

When wio creates a contract from a template, or injects a template into a
session, it prepares the template as a contract skeleton. The `[contract]` table
is promoted to the top level (`[contract.foo]` becomes `[foo]`), and the
template's own keys (`name`, `type`, `description` and `[actions]`) are dropped.
wio always sets `id` and `template` itself, even if the template specifies them,
and it removes comments from the metadata, because they belong to the template
author.

Because `[contract.actions]` is promoted like everything else, a template can
decide how new contracts start. A template for drafts puts `[contract.actions]`
with a `define` pipeline in, so every new contract begins with definition only.
A template without it makes new contracts inherit its own actions.

The agent that defines a Work therefore sees the template in the shape of the
contract it is about to write, and a contract created from the template has
exactly that shape.

### Types

The config declares the valid template types:

```toml
[templates]
types = ["feature", "bugfix"]
```

A type groups templates that serve one kind of outcome. A type can have any
number of templates (a draft, a leaf, a parent, or seven others), each with its
own actions. wio gives them no level or shape: which template a contract
follows is the contract's `template` field, and that decides its actions.

Exactly one template per type declares a `define` action in its `[actions]`.
Creating a contract from a type uses that template, and a template can also be
chosen by name. `wio config check` fails when a declared type has no such
template, when two templates of a type declare one, and when a template or a
rule names a type that is not declared.

Anyone can add a template, and with it a type, and that is the main extension
point for projects. Files in the templates directory without a `wio` metadata
block are ignored.

### Directives

Directives tell `wio contract check` what is mandatory. They live in HTML
comments on the heading they govern, for example
`## Goals <!-- wio: required, items>=1 -->`. They are invisible when the
contract is rendered, readable in the source, and parseable by a markdown
parser. The grammar is small: `required`, `items` and `pattern`, and `inherit`.
Sections are **optional until marked required**, so the agent can choose
sections based on the intent it gathered.

Authoring comments and directives are removed when a contract is written. The
`wio` metadata block stays.

## 4. Nesting

### Parent and leaf

A Work either is a **leaf** (one coherent outcome, executed directly) or a
**parent** (an outcome that is delivered by its children). A child's directory
sits inside its parent's directory, so the hierarchy is the directory tree.
There is no `parent` field and no `children` list, because both are
**computed** from the layout. Stored lists drift; computed ones cannot. Which of
the two a Work is follows from the tree: a Work with child directories is a
parent.

### When to split

For any outcome, ask one question: does it need decomposition?

- **Yes**: it contains independently useful, independently deliverable
  outcomes. Split them into child Works.
- **No**: it is one coherent outcome. Keep it as a leaf.
- **Unknown**: you cannot tell yet. Resolve the uncertainty with the smallest
  exploration that answers it, within the authorized outcome. Exploration can
  inform a split. It never authorizes building the feature.

The Work tree describes outcomes. It does not have to mirror the module tree or
the directory tree of the code.

How a split is carried out, and whether the pieces become nested children or
flat siblings, is a procedure that a stage and its skill own. wio only reads the
result: the directory layout and the metadata.

### One root per leaf

A **root** is a set of directories bound to one toolchain and one set of
rulesets (section 8). A Work without children has exactly one root, written as
`root` in its metadata, using the name the config gives that root. If an outcome
spans two roots, for example a FastAPI backend and a Next.js frontend, it
becomes a parent with one leaf per root. This keeps the guidance for each leaf
deterministic: a leaf has exactly one rule stack. A parent has no root field:
its scope is derived as the union of its children.

If a leaf discovers it needs to change a root outside its declared scope, that
is a signal to split, not to widen the scope.

### Inheritance, computed

A child often needs constraints that its parent states. Instead of copying them
into each child, a parent's template marks sections as **inheritable** with the
`inherit` directive: its Glossary and its Constraints. `wio contract show` can
then print the leaf together with the inheritable sections of its ancestors. The
agent reads one resolved view and never needs to open whole parent contracts.

A leaf's own Constraints section holds only the constraints the leaf adds. The
inherited ones are not restated, so they cannot drift.

Marking individual acceptance criteria as inheritable is possible later.

### Dependencies

A Work can depend on other Works. Its metadata has an optional `depends_on`, an
array of Work ids:

```toml
depends_on = ["a7b2c4", "k3m9xq"]
```

- Dependencies are ids, never paths, so moving or renaming a Work's directory
  breaks nothing. The tree gives the hierarchy, and `depends_on` adds an
  ordering graph on top of it. Nesting only decides what is inherited;
  `depends_on` works the same for nested and flat Works.
- `wio contract check` verifies that every id exists and that there are no
  cycles, counting the implicit edge from each child to its parent for delivery.
- A dependency means the other Work must be delivered first. Whether it also
  holds back the dependent's definition, and whether a parent's dependencies
  also apply to its descendants, are open points.

## 5. Actions

### What an action is

An action is a named kind of work done on a Work. wio ships two, and they are
built in:

- **define**: turn an intent into a contract. This is where a Work is
  interviewed, written down, reviewed and, if needed, split.
- **deliver**: build what the contract says.

An action's **pipeline** is either a **preset** (an ordered list of stages, by
preset id) or a list of **stage names**. In both, some stages may be gates.
Custom actions come later and are not part of v0.1.

### Where the pipeline comes from

A contract follows a template, and the template's `[actions]` give the default
pipeline of each action. A contract may carry its own `[actions]`, and then it
**replaces all of the template's actions**, not only the ones it names:

```toml
[actions]
deliver = ["implementation"]
```

This is how a small leaf skips the stages a large parent needs. Because the
block replaces everything, an action that is left out does not apply. In the
example the Work has no `define` action: its definition is finished.

A string value is a preset id and an array is a list of stage names, so a
one-stage pipeline is a one-element array. Stage names and preset ids must exist
in the config. A contract that names stages is free to skip any of them,
including gates. Hygiene is the project's business, and guidance and
presets can encourage good practice.

wio does not update a contract that has its own `[actions]` when the template or
the config changes. `wio contract check` reports names that no longer exist.

### Procedures belong to stages

Splitting a Work, promoting a leaf to a parent, demoting a parent: these are
procedures. Each is a stage with a skill, and wio does not know how they work.
A stub, for example, is an ordinary contract whose own `[actions]` contain only
`define`. When the definition is finished, a stage rewrites the file: it fills
in the contract and removes that block, so the template's actions apply. wio has
no concept of a stub, a draft or a level.

What wio does is provide context to each stage, select its rules, log what
happens and check invariants afterwards.

### What `wio next` proposes

`wio next` proposes the next action and stage for a Work. It is a heuristic over
the data wio has, and the driver may do something else.

- A contract whose actions include `deliver` is assumed to be defined, so the
  proposal is a stage of `deliver`. Otherwise it is a stage of `define`.
- Within the action, the next stage is the first one in the pipeline that no
  merged pull request has delivered (section 11).
- If the contract file and the history disagree, the file wins and `wio next`
  warns.

For a whole tree, defining runs top-down and delivering runs bottom-up. A parent
is defined before the stubs it creates, and a parent is delivered after its
children. The leaves to deliver, with `depends_on`, form a graph that can be
sorted into batches, and the Works in one batch can run in parallel, for
example `(("32s", "97f"), "213as", ("8as", "732sfa"))`.

### Invariants wio checks

`wio contract check` and `wio config check` verify mechanically what wio relies
on, and they do not judge how a workflow is built:

- Every contract names an existing template, and the template's type is a
  declared type.
- The actions a contract resolves to are not empty, and each pipeline has at
  least one stage. An outcome with nothing to deliver belongs in the ticketing
  system, not in the repository.
- Every preset id and stage name in a template or a contract exists.
- Every `root` is a root in the config, every `depends_on` id exists, and there
  are no cycles.
- Required sections are present, as the template's directives say.

## 6. Stage

### What it is

A stage is one named step of working on a Work. It answers: *what is being
produced right now, and with which guidance?*

A stage definition has these parts:

| Part | Meaning |
| --- | --- |
| `name` | Identifier used in config, rules and logs. |
| `goal` | A short text that says what to produce. Used when the instructions fit in a few lines. |
| `skill` | A skill name, used instead of a goal when the procedure needs references, templates or scripts. |
| `tags` | Which rules apply (section 9). |
| `approval` | Optional. Marks that a human must approve before the next stage starts. |
| session policy | Whether the stage needs a fresh session, and whether later stages may continue its session. |

A stage with only a goal and tags is valid. A stage with a skill hands its
procedure to that skill. The engine does not care which; it prints the goal or
names the skill, and compiles the rules.

### Why stages exist

Staging lets a cheap artifact be reviewed before an expensive one is built. A
typed signature costs a few lines to produce and a few seconds to review. The
implementation behind it costs far more. If the signature is wrong, only the
signature is redone.

The engine does not decide which stages exist. Projects define stages in the
config file. A project may have one stage or twelve. A single-stage contract is
valid, and still benefits from the intent captured in the contract.

### Stages are not a pipeline

Real work goes back and forth. Implementation may show that the architecture
needs redoing. A review may send the work back one step. The engine therefore
treats stages as a **set of named steps**, and the order is a preset (section
12) that a driver follows, not a rule the engine enforces.

### Who knows which stage is current

Nobody records it. "Which stage is the Work at" is a decision, not a fact that
the repository can answer. A stage may have produced a valid artifact that is
nevertheless not approved, and with back-and-forth the answer is not even
monotonic. So the **driver** names the stage: the human in v0.1, an
orchestrator later. The command that starts a session (`wio context`, given the
Work and the stage) is the declaration.

### Sessions

A stage may require a **fresh session**. Reviews need one, because a reviewer
who shares the author's context shares the author's blind spots. A stage may
also mark itself as **not continuable**, so a later stage will not reuse it.
Otherwise a session may be continued from the previous stage, which saves tokens
because the contract and rules are already loaded. In v0.1 `wio context` only
prints this advice. The driver follows it.

## 7. Gate

### What it is

A gate is a point where work stops until a decision is made. The decision is one
of: continue to the next stage, go back to an earlier stage, or change the
contract.

In the engine a gate is not a separate object. It appears in two forms:

1. **Approval gate**: a stage marked `approval = "human"`. Work does not proceed
   until a person approves the stage's artifact.
2. **Review gate**: a stage whose job is to judge the previous stage's
   artifact. It is a normal stage with its own rules (tagged for review) and
   usually a fresh session. It can be a human review, or an automated check by
   an agent in a fresh session with a different ruleset. A review stage can
   itself carry an approval.

Both forms are built from stage properties. This keeps the engine small: there
is no gate type to learn, only stages that stop for a decision.

### What a good gate looks like

- It looks at the **exact revision** that was produced. A reviewer pinned to a
  commit cannot be fooled by later edits.
- It is done by someone other than the author, or by the human.
- It judges the artifact against the contract. The contract is the standard, the
  code is the subject.
- A passing automated check is evidence, not a verdict. A type check proves the
  types agree. It does not prove the design is right.

### What a gate decides

Three outcomes, all of which are normal:

- **Pass**: the next stage starts.
- **Back-edge**: the artifact exposes a gap in an earlier stage's work. Work
  returns to that stage. Repeated back-edges to the same stage are a signal that
  something unknown was treated as known, and the right response is to amend the
  contract or split the Work.
- **Contract change**: the intent was wrong. See section 2.

### What the engine enforces

In v0.1, the engine describes gates and the driver honors them. `wio context`
prints the stage's approval and session advice. It does not block anything.
Enforcement (for example refusing to start a stage whose predecessor lacks an
approval) belongs to a later orchestrator, which keeps the state in its own run
record and not in the repository.

## 8. Roots and rulesets

A **root** is the directories that a set of rules applies to. In a
single-language repo the root is the repo itself. In a monorepo with a backend,
a frontend and Terraform, there are three roots with three different toolchains
and three different sets of guidance.

A **ruleset** is a reusable bundle of rule files, for example "python" or
"fastapi". The repo's config **binds** rulesets to roots:

```toml
[[roots]]
name     = "api"
paths    = ["services/api"]
rulesets = ["python", "fastapi"]

[[roots]]
name     = "infra"
paths    = ["infra"]
rulesets = ["terraform"]
```

A root has a `name`, which contracts use in their `root` field, and `paths`, a
list of directories. The paths are plain directories for now, without globs.
It is a list from the start because adding `paths` later, next to a single
`path`, would mean supporting two forms.

Why bind at the repo level and not inside the ruleset? Because a ruleset must
work in any repo. It does not know where the FastAPI service lives. The repo
does.

A root is a **toolchain boundary**, not a kind of directory. Tests and sources
written in the same language under the same tools share a root. They differ by
rule tags, not by root.

## 9. Rules

### What a rule is

A rule is one atomic instruction with a one-line reason: do X, or don't do Y. It
is a small markdown file.

```markdown
<!-- wio
code = "ARC001"
name = "adapters-return-typed-results"
tags = ["architecture", "review"]
types = ["feature"]            # optional
-->

Adapters return typed results, not raw dicts.

Why: a dict hides the contract from the type checker, so drift appears at runtime.
```

The first line of the body is the rule's summary, and the rest is its reason.

Rules are atomic so they can be combined freely. A long guidance document cannot
be filtered, but forty small rules can be filtered down to the seven that matter
right now.

What is **not** a rule:

- A procedure with steps, references or scripts is a **skill**.
- A mechanical check that a tool can enforce (formatting, a type error, an
  import cycle) belongs in the **tool's config**. If a linter already catches
  it, it should not cost tokens in the bundle.
- Always-needed text (a short list of commands, a few style rules) belongs in
  `AGENTS.md`.

### Codes and families

Rules are identified the way linter rules are. A rule has a **code**, such as
`ARC001`, a **name**, such as `adapters-return-typed-results`, and a one-line
summary (the first line of its body). The letters of the code are its
**family**, which groups rules by topic.

- A ruleset declares its families and owns their prefixes. `wio rule new`
  assigns the next free number in a family, so codes cannot clash inside a
  ruleset, and `wio config check` fails when two rulesets bound in the same repo
  claim the same prefix.
- The code is the stable identifier. Verdicts in the event log and review
  comments cite it, and renaming a rule does not change it.
- A rule file is named `<code>-<name>.md`, so listings sort by family.
- Wherever a rule is shown to a person or an agent, the code and the name appear
  together, so the code is never opaque.

Family and tags are independent: a family groups rules by topic, and tags select
rules for a stage.

### Tags

Tags connect rules to stages. A tag is a label from a vocabulary declared in the
config, similar to the categories in a linter (style, complexity, security). The
vocabulary is declared so a misspelled tag is an error, not a rule that silently
never loads.

A stage lists tags, and a rule lists tags. In v0.1 the matching rule is
**all-of**: a rule applies to a stage only when **every** tag of the rule is
among the stage's tags.

An example shows why. Suppose the architecture stage has tags `[architecture,
testing]`, and the review stage has `[architecture, review]`.

| Rule tags | Architecture stage | Review stage |
| --- | --- | --- |
| `[architecture]` | applies | applies |
| `[architecture, review]` | does not apply | applies |
| `[testing]` | applies | does not apply |

The second rule is reviewer-only: a check that the reviewer applies but the
author is not told in advance. Reviewer-only rules cost tokens only when a
reviewer runs, and a rule that keeps being violated can be promoted by adding
the author's tag.

### What else filters a rule

- **Root**: only rulesets bound to the Work's root are considered.
- **Template type**: an optional `types` list restricts a rule to certain types
  of Work. The names must be declared types.
- **Stage**, through its tags. A stage lists the tags of the rules it should
  see, so an authoring stage and its review stage get different rules without
  any rule naming a stage. Stage names are chosen by each project and a ruleset
  has to work in any repo, so rules refer to tags and never to stage names. To
  scope a rule to exactly one stage, add a tag named after that stage to the
  vocabulary and list it in that stage's tags.

So selection is: root, then template type, then the stage's tags. Three
dimensions are enough. More would make rules hard to write and reason about.

## 10. The context compiler

`wio context` is the piece that joins everything. It answers: *what should this
agent session read before it starts?*

Inputs: a Work id (or only a root, before a contract exists), an action if the
stage name is ambiguous, and a stage name. It reads the contract and its
ancestors, the stage definition, the rulesets bound to the root, and the rule
files. When a Work is being defined, it also injects the template, prepared as a
contract skeleton (section 3), and the resolved view of its parent Works.

Output, printed to the session:

1. A header: Work, action, stage, number of rules, session advice, and a short
   bundle id (a hash of the text).
2. The stage's goal, or the name of its skill.
3. The resolved contract: the Work plus inheritable sections from its
   ancestors.
4. The selected rules, grouped by tag, in a stable order, each shown with its
   code and name.

Properties that matter:

- **Deterministic**: the same inputs produce the same bytes. This makes it
  testable with golden files and lets two evaluation runs be compared by bundle
  id ("these saw identical context").
- **Pull, not push**: the agent runs it itself as the first step of a stage, so
  a session always gets the bundle for its own stage. A dispatcher that pushed
  the wrong bundle could hand a reviewer the author's rules.
- **Loud failures**: an unknown Work, stage or root is an error. An empty bundle
  looks like success, so it is never produced by mistake. Zero matching rules is
  valid, and the header says so. A stage that is not in the Work's actions is
  only a warning, because the driver decides.
- **Explainable**: `wio context` can list why each rule was included or
  excluded.
- **Once per session**: the bundle is injected at session start. If the
  contract is amended afterwards, the session runs the command again.

## 11. Intent in the repo, progress outside

The engine keeps a strict line:

| Lives in the repository | Lives outside the contracts |
| --- | --- |
| Contracts (intent) | Which action and stage is current (the driver's decision) |
| Templates, rules, config | Whether a Work is done (a ticket, or the human) |
| Artifacts produced by stages | Which stages and criteria were delivered: the merged pull requests |
| | Event log: which stages ran, which rules were injected, review verdicts |

The reason is a fixed-point problem. A commit cannot record a fact that only
becomes true after the commit lands (merged, approved, done). Recording such
facts in the repo needs follow-up commits, and the follow-up commits need
recording too.

So there is no status field in a contract, no per-criterion state, and no stored
current stage. The repo can still be queried for what is **derivable**: the Work
tree, each leaf's scope, and what a contract inherits.

A change of intent is different from progress. A contract that stops being a
sketch and becomes a complete one, or that gets its own `[actions]`, is an edit
of intent that is made and reviewed in the repository. Which stage the Work is
in, and whether the outcome is truly done, stay outside.

Progress comes from two places:

- **Merged pull requests.** Squash merging copies the pull request description
  into the commit on `main`. Its Work section carries four lines, `ID:`,
  `Action:`, `Stage:` and `Criteria:`. The merge itself is the record, so no
  follow-up commit is needed. A tool can read these lines from the first-parent
  history, skip commits that lack them, and know which stages and criteria were
  delivered. Merged is a signal, not proof: a criterion addressed at the
  architecture stage is specified, not satisfied. Ids, not paths, identify the
  Work, so moving a directory does not break its history.
- **The event log.** An append-only JSONL file stored in the user's data
  directory, one file per repo. It holds ids and hashes only, no prompts and no
  code. It is personal to one machine, so history answers "what is merged" for
  everyone, and the log answers "what I started". In v0.1 it records two events:
  - `context`: a session started a stage, with the rule ids and hashes it
    received, the harness and the session id.
  - `verdicts`: a review round ended, with the reviewed commit and a verdict per
    rule code (pass, violation, not applicable, uncertain).

Because events carry the harness session id, they can be joined to the harness's
own transcripts. That gives token and cost totals per Work and per stage, which
is how a project learns what each stage costs and whether a rule earns its
place.

Logging never blocks a command. The log is written because it cannot be
reconstructed later, and analyzed whenever it is needed.

## 12. Presets: process built on the engine

A **preset** is a named ordered list of stages. The engine ships none in v0.1. A
preset becomes the pipeline of an action wherever a template or a contract names
it, so most contracts never list stages themselves.

The engine does not care what the stages are. For illustration only, one
possible preset is the typed-boundary flow, and a template binds it to the
`deliver` action:

```toml
[presets]
define-feature = ["define", "review-contract", "split"]
typed-boundary = [
  "architecture",         # typed signatures and test stubs
  "architecture-review",
  "wiring",               # composed skeleton with stubbed leaves
  "wiring-review",
  "implementation",
  "implementation-review",
]
```

```markdown
<!-- wio
name = "feature.leaf"
type = "feature"
description = "A capability delivered directly as one coherent outcome."

[actions]
deliver = "typed-boundary"

[contract]
root = ""
-->
```

Other presets are equally valid: a single `implement` stage, a flow that starts
with high-level acceptance tests in a readable DSL, or an organization-specific
procedure with extra approval stages. Presets and rulesets can live in their own
repositories and be used or forked by anyone. Joining presets, so that one is
built from others, may come later.

A preset only names stages and orders them. What a stage produces comes from its
goal or skill. How well it produces it comes from the rules its tags select.

## 13. What the engine deliberately does not do

- It does not decide when a stage is done, or which action comes next. The
  driver does. `wio next` only proposes.
- It does not store progress or status in contracts.
- It does not run agents. It prepares context for them.
- It does not prescribe a workflow. Splitting, promoting and demoting Works are
  procedures that skills own; wio checks the invariants afterwards.
- It does not manage branches, worktrees, publishing or cleanup. Those are
  project conventions.
- It does not assume a language. The typed-boundary preset needs a checker that
  can reject a skeleton cheaply (a type checker, architecture tests), but the
  engine itself only needs files, tags and text.

## 14. Open points

- Whether the harness session id is visible to the `wio context` process, or
  only to hooks. If not, events join to transcripts by time window and working
  directory.
- The exact field names for stage session policy, and the names of the config
  tables (`[presets]`, `[templates]`).
- Where a ruleset declares its families and prefixes, and whether rule files
  accept `+++` front matter as well. The rule example above uses the
  `<!-- wio -->` block, as contracts do.
- How a parent whose pipeline needs stages both before and after its children is
  expressed. Today a parent is delivered after its children. Interleaved flows,
  such as typed architecture and wiring of the whole before the leaves are
  implemented, need stage-level ordering across the tree. The history and the
  log already key on the Work, the action and the stage, so this can be added.
- Whether a parent's `depends_on` also applies to its descendants, and whether a
  dependency holds back the dependent's definition. The current lean is no to
  both.
- How `wio next` reads the history of a Work after a structural change such as
  promoting or demoting it. Custom actions, which come after v0.1, will carry
  their own metadata for this.
- The form of the metadata block (comment or `+++`) as a config setting, with a
  command that rewrites contracts and templates. Templates must keep their
  comments, so the rewrite either swaps only the delimiters or reads with a
  style-preserving parser.
- Flat splits, custom actions and the joining of presets, which come after v0.1.
- How finished contracts are retired: promote the lasting parts into
  documentation and delete the contract in the final commit, or keep them as
  decision records. Not decided.
- Whether all-of tag matching is enough. It is the simplest rule that works, and
  it can be replaced later without changing the file formats.
- How progress is read from pull requests: how far back to scan, and how an
  unknown history is reported, are for a later `wio next` to decide.
