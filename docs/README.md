# Documentation

- [Core concepts](concepts.md): an index of the names and markers wio reads,
  and the few concepts the engine is built from (Work contract, templates,
  nesting, actions, stage, gate, roots, rules, context compiler, records) and
  how they fit together, including the `Wio-*` trailers wio reads and writes.
- [wio's own workflow](workflow.md): the process this repository runs on the
  engine (its actions, stage presets, stages and gates), how a contract is
  defined, delivered, changed and retired, and why.
- [Scope of v0.1](v0.1-scope.md): the components of the first release, and what
  each is for, delivers and how it is used.
- [Split exercises](split-exercises.md): four paper exercises that split an
  outcome into Works, and what they showed about the v0.1 design.
- [Known issues](known-issues.md): problems in this repository's tooling that
  are known and not yet fixed, with what each puts at risk.
- [Glossary](../GLOSSARY.md): the terms used across the project.
- [Test strategy](../tests/README.md): test layers, how to pick one and
  conventions.
- [Acceptance tests](../tests/acceptance/README.md): the acceptance-test DSL,
  test drivers and channels.
- [This repository's config](../.agents/wio/config.toml): the roots, kinds,
  actions, stages and stage presets wio's own development uses.
- [Work templates](../.agents/wio/templates): the draft, leaf and parent
  templates used to write Work contracts.
- [Contracts ruleset](../.agents/wio/rules/contracts): the rules for writing
  and reviewing Work contracts.
- [Contract-upkeep ruleset](../.agents/wio/rules/contract-upkeep): the rules
  that keep a contract true while its code is written.
