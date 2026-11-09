# wio's own workflow

The [core concepts](concepts.md) describe the engine and no process. This
document describes the process this repository runs on the engine: its kinds,
actions, stage presets, stages and gates, the rules each stage gets, and the
reasons behind them. It is one
workflow among many, and it shows how the concepts are meant to be combined.
The workflow itself is the [config](../.agents/wio/config.toml), the
[templates](../.agents/wio/templates) and the
[rulesets](../.agents/wio/rules); this document explains them. Terms are
defined in the [glossary](../GLOSSARY.md).

## 1. Overview

The repository declares one kind, `feature`, with three templates: a draft that
every new Work starts from, a leaf and a parent. Four actions work on a Work:

| Action | Pipeline | What it does |
| --- | --- | --- |
| `define` | `define-feature` | Turns an intent into a contract, and splits it when needed. |
| `deliver` | `typed-boundary` for a leaf, `integrate` for a parent | Builds what the contract says, and promotes it into the docs. |
| `amend` | `amend-contract`, on demand | Changes a defined contract's intent. |
| `ratify` | `ratify-contract`, on demand | Brings a contract in line with what was built. |

```mermaid
flowchart LR
    N[wio contracts new] --> D[define-feature]
    D -->|leaf| TB[typed-boundary]
    D -->|parent| CH[children defined and delivered]
    CH --> I[integrate]
    TB -.->|intent wrong| AM[amend-contract]
    TB -.->|wording off| RA[ratify-contract]
    AM -.->|delivery stale| TB
```

Every pipeline ends in a gate, and every authoring stage is followed by one.
`deliver` comes `after` `define`, and is `invalidated_by` `define`, `amend`
and the delivery of any descendant, so redefining or amending a Work, or
delivering one of its children again, makes its delivery stale.

## 2. What a contract states

The engine gives a contract no meaning beyond its metadata and headings. In
this workflow, a contract states one outcome and the behaviors that show it
has been achieved. It records **intent**: what should become true, and why.

It is deliberately not a plan, a task list or a progress report. Intent changes
rarely and by deliberate decision, while progress changes with every stage, and
the engine keeps progress in the history. So whatever would change while the
Work is built stays out of the contract.

The leaf and parent templates give a contract these sections:

| Section | Holds |
| --- | --- |
| Purpose | Why the change is needed. Required. |
| Goals and Non-Goals | The capabilities the Work makes possible, and what it deliberately does not do. Goals are required. |
| Glossary | Terms whose meaning could be read more than one way. A parent's is inherited by its descendants. |
| Assumptions | What the Work takes as true without having confirmed it, each with an id such as `A-1`. Required. |
| Mechanisms | The tools, packages, modules or data structures central to the solution, and their roles. |
| Constraints | The constraints the Work adds. A parent's are inherited by its descendants. |
| Visuals | Before and after diagrams of what the Work changes. Required for a parent. |
| Acceptance criteria | The behaviors, each a `### **AC-1** ...` subheading with its own id and Given/When/Then examples. Required. |
| Additional context | Context, risks and links that fit nowhere above. |

Assumptions and criteria carry ids so that an amendment can say precisely what
changed, and so that records and reviews can cite the items a commit
addresses. The draft template has only a Purpose and an Intent section, which
the define stage uses as working space.

## 3. Defining a Work

### From draft to leaf or parent

`wio contracts new feature` creates a Work from `feature.draft`. The draft has
only a purpose and an intent section, which serve as working space while the
`define` stage interviews the driver. Once the intent is clear, the stage
decides whether the Work is a leaf or a parent, prints that template with
`wio templates show <name> --work <id>` and rewrites the contract in its
shape. `--work` keeps the Work's id and its dependencies, so the Work keeps its
records. The stage passes no `--keep`, so the new template's roots and actions
apply: a leaf gets the typed-boundary delivery, and a parent gets
`roots = ["@descendants"]` and the integrate delivery. The intent section does
not carry over.

A contract created from a template keeps the template's authoring comments,
and the stage follows them while it fills each section in. The agent deletes
each authoring comment once its section is written, and deletes the sections it
leaves empty, unless they are required.

The draft requires only a Purpose, because that is all a fresh Work can supply.
Works created by a split can sit in the tree for a while before they are
defined, and they must still pass `wio contracts check`. The leaf and parent
templates carry the stricter directives.

The draft, the leaf and the parent are written together with the define stage,
as one package. The engine knows none of this: it only checks the result
against the template the contract names.

### When to split

For any outcome, the define stage asks one question: does it need
decomposition?

- **Yes**: it contains independently useful, independently deliverable
  outcomes. Split them into child Works, created with
  `wio contracts new feature --parent <id>`.
- **No**: it is one coherent outcome. Keep it as a leaf.
- **Unknown**: you cannot tell yet. Resolve the uncertainty with the smallest
  exploration that answers it, within the authorized outcome. Exploration can
  inform a split. It never authorizes building the feature.

The children of a split start as drafts and are defined in turn. A parent is
defined before its children, and delivered after them. A boundary that several
leaves share is extracted as a leaf of its own and delivered first, and the
other leaves depend on it. The [split exercises](split-exercises.md) walk
through four splits.

### The contract gate

The gate of `define`, `review-contract`, is where the engine's first need is
met: a human confirms the understanding before expensive work starts. The
reviewer judges the contract on its own terms, by the rules, and only the
driver can say whether it states what they meant. So the gate is marked
`judge = "human"`, ends by asking the driver to confirm, and records `pass`
only once they have. The contract holds the intent in the template's shape,
not a transcript of the interview that produced it.

### The contract root

The rules for writing contracts are the `contracts` ruleset. The `contract`
root, whose path is the Works directory, selects its `authoring` rule preset
and the whole `writing` ruleset, which holds the rules for links and diagrams.
The define, amend and ratify stages and their gates select that root with
`roots = ["contract"]`. So a Work that is still being defined, and has no roots
yet, gets the rules for writing contracts, and an amendment or a ratify of a
delivered leaf gets them too, rather than the rules of the code the leaf
touches.

Each of those stages adds the `contracts` rule preset for its own work, which
the root reaches, so the stage needs no root of its own:

| Stage | Adds |
| --- | --- |
| `define` | nothing |
| `review-contract` | `contracts.review` |
| `amend` | `contracts.amend` |
| `review-amendment` | `contracts.amend`, `contracts.review` |
| `ratify` | `contracts.ratify` |
| `review-ratify` | `contracts.ratify`, `contracts.review` |

`authoring` excludes those three rule presets, so the rules that only a review,
an amendment or a ratify needs stay out of the define stage. How the roots, the
stages and the rule presets combine is
[how a rule is selected](concepts.md#how-a-rule-is-selected).

The few rules that the agent writing code needs about its contract, such as
asking for an amendment instead of working around a false assumption, are the
`contract-upkeep` ruleset. The code roots select it, so the deliver stages get
it and never select the contract root.

## 4. Delivering a Work

### Typed boundaries for a leaf

A leaf is delivered by the `typed-boundary` stage preset:

| Stage | Produces |
| --- | --- |
| `architecture` | The typed signatures and test stubs the contract needs. |
| `wiring` | A running skeleton that composes the boundaries, with stubbed leaves. |
| `implementation` | The code behind the stubs, until the tests and checks pass. |
| `promote-docs` | The contract's lasting guarantees, carried into the docs. |

Each is followed by its gate, in a fresh session. The order puts the cheapest
artifact first: a signature costs a few lines to review, and if it is wrong,
only the signature is redone. It relies on a checker that can reject a
skeleton cheaply, such as a type checker or architecture tests, which is why
this stage preset suits a typed language and is not part of the engine.

### Integration for a parent

A parent is delivered by the `integrate` stage preset: the `integration` stage
joins the delivered children and adds the tests for the parent's system-level
criteria, `system-review` judges the result against those criteria, and the
promote stages follow.

### The rules of the delivery stages

The deliver stages select the Work's roots, and the promote stages select the
`repo` root. A root's rule presets reach every stage that selects it, so the
`wio` root brings `contract-upkeep`, and the `repo` root brings
`contract-upkeep`, `docs` and `writing`. Each stage excludes, by family, what
it does not need, and the config says why next to the exclude:

| Stages | Exclude | Why |
| --- | --- | --- |
| `architecture`, `wiring`, `implementation`, `integration` | `docs.DOC`, `writing.WRT` | Writing code needs no rule for writing docs. |
| their gates | `contract-upkeep.UPK`, `docs.DOC`, `writing.WRT` | A review judges the code against the contract, and writes neither. |
| `promote-docs`, `docs-review` | `contract-upkeep.UPK` | The docs are written after the code, so keeping the contract true while coding does not apply. |

An exclude of a family that the stage's roots do not bring removes nothing, so a
stage can exclude `docs.DOC` whether or not the Work names the `repo` root.

### Retiring a contract

A contract is spent once its guarantees live elsewhere. `promote-docs` carries
the lasting rules, reasons and diagrams into the `README.md` and `GLOSSARY.md`
files of the directories the Work touched, linking instead of copying.
A guarantee that a stub, docstring or test already states is kept by a link to
it. `docs-review`, judged by a human, checks that no guarantee was lost and that
the docs restate nothing the source declares. A Work
without a parent then deletes its contract and those of its descendants in the
last commit of the stage, once the driver confirms. A Work with a parent only
promotes, because the tree is kept until its top Work has promoted. Git keeps
the deleted contracts, and the records keep the progress.

## 5. Changing a contract

Later stages can reveal that the contract was wrong or incomplete. That is
normal, not a failure. A downstream stage **proposes** a change and the driver
decides. The decision has three outcomes:

- **Abandon**: stop this Work by deleting its directory. Every Work that
  depends on it is updated in the same change. Abandoning is a change of
  intent, so the deleting commit carries a record of the `define` action. A
  Work that is retired once it is done is deleted by the commit of the last
  stage it belongs to, and carries that stage's record.
- **Amend**: change the acceptance criteria, assumptions or constraints, then
  rework whatever depended on them. An amendment runs through the on-demand
  `amend` action, which `deliver` lists in `invalidated_by`, so the delivered
  stages become stale. Its gate, `review-amendment`, sees the rules for
  amendments and asks the driver to confirm the amended parts.
- **Ratify**: update the contract to match what was built, without reworking
  anything. It runs through the on-demand `ratify` action, which `deliver` does
  not list in `invalidated_by`, so nothing becomes stale. Its gate,
  `review-ratify`, checks that no criterion's guarantee changed; one that did is
  an amendment.

Ratify is the cheap option and the one to watch. Used too often, it turns the
contract from a statement of intent into a log of what happened. Giving it its
own action keeps it visible: its records show how often it happens. So a commit
that changes a contract carries a record of the action that matches the change,
an amendment or a ratify, and never a record of the delivery stage it was found
in.

## 6. Gates

### What a good gate looks like

- It looks at the **exact revision** that was produced. A reviewer pinned to a
  commit cannot be fooled by later edits. The `context` event of a gate session
  records the commit the review starts from, and the `review` event records the
  commit that was judged, so a change in between is visible (see
  [the event log](concepts.md#the-event-log)).
- It is done by someone other than the author, or by the human. Every gate here
  asks for a fresh session.
- It judges the artifact against the contract. The contract is the standard, the
  code is the subject.
- A passing automated check is evidence, not a verdict. A type check proves the
  types agree. It does not prove the design is right.

### Results and back-edges

The results are `pass`, `fail` and `unknown`. `pass` means the next stage can
start, `fail` means it cannot, and `unknown` means the gate could not judge.
After a `fail`, the driver decides whether the work goes back to an earlier
stage or the contract changes.

A back-edge means the artifact exposed a gap in an earlier stage's work.
Repeated back-edges to the same stage are a signal that something unknown was
treated as known, and the right response is to amend the contract or split the
Work.

The contract, amendment and docs gates are marked `judge = "human"`, because
they ask whether something states what the driver meant. The delivery gates are
judged by an agent.

## 7. Checking the config after every edit

A config with an error is refused by every command, so an agent that edits it
needs to be told at once. `wio config check` prints the diagnostics and exits 1
on an error, and each project decides how its harness runs it. This repository
does it twice:

- **When an agent edits the config.** An entry in `.claude/settings.json` runs
  the check after `Edit`, `Write` and `MultiEdit`, and exits 2 with the
  diagnostics on standard error, which Claude Code gives back to the model. It
  reads the edited path with `jq` and runs the check only for the config, so wio
  holds no knowledge of the harness. The entry sits beside the formatter:

  ```json
  {
    "hooks": {
      "PostToolUse": [
        {
          "matcher": "Edit|Write|MultiEdit",
          "hooks": [
            {
              "type": "command",
              "command": "jq -r '.tool_input.file_path // empty' | { read -r f; case \"$f\" in */.agents/wio/config.toml) out=$(uv run wio config check 2>/dev/null); [ $? -ne 1 ] || { printf '%s\\n' \"$out\" >&2; exit 2; };; esac; }"
            }
          ]
        }
      ]
    }
  }
  ```

  A project that has `wio` on its `PATH` writes `wio config check` where this
  says `uv run wio config check`, and another harness does the same with its own
  hook.
- **When a commit changes the config.** The `wio-config` hook of `prek.toml`
  runs `uv run wio config check` when `.agents/wio/config.toml` is in the
  commit, and passes it no file names.
