# SPDX-License-Identifier: Apache-2.0
"""The type for the project's settings, an immutable tree of plain data.

The stub is the spec until the implementation stage replaces it with a `.py`
of the same annotations. Every field is named as its TOML key, so a key path
such as `works.defaults.actions` is a chain of field names. A `Config` built
with no arguments is the effective settings of an empty config file, and every
field carries a one-sentence description in its metadata, which a message can
quote. A `Config` holds what it is given: it judges nothing.
"""

from typing import Literal

class Defaults:
    """The default pipelines of the actions, for Works without a template."""

    actions: frozendict[str, str | tuple[str, ...]]
    """The stage preset or the stages of each action; empty by default."""

class Works:
    """Where wio finds Works and how it derives their hierarchy."""

    dir: str
    """The Works directory; `.agents/wio/works` by default."""
    hierarchy: Literal["flat", "nesting"]
    """How the hierarchy is derived; `flat` by default."""
    defaults: Defaults
    """The defaults of Works that name no template."""

class Templates:
    """Where the templates live and which one each kind starts from."""

    dir: str
    """The templates directory; `.agents/wio/templates` by default."""
    kinds: frozendict[str, str]
    """The entry template of each kind; empty by default."""

class Trailers:
    """How the records of commits are read."""

    reader: Literal["scan", "git"]
    """Who parses trailers, wio's scan or git; `scan` by default."""

class Skills:
    """Where the skills a stage names are looked up."""

    paths: tuple[str, ...]
    """The directories searched for skills; none by default."""

class Bundle:
    """How a context bundle is joined."""

    separator: str
    """The text between the parts of a bundle; a blank line by default."""
    size_threshold: int | None
    """The size above which a bundle is warned about; none by default."""

class Action:
    """One action a Work can run."""

    description: str
    """What the action does; required."""
    after: tuple[str, ...]
    """The actions this one is proposed after; none by default."""
    invalidated_by: tuple[str, ...]
    """The actions whose newer records make this one stale; none by default."""
    on_demand: bool
    """Whether `wio next` never proposes it; false by default."""

class Root:
    """A named area of the repository."""

    paths: tuple[str, ...]
    """The paths of the root; required."""
    rule_presets: tuple[str, ...]
    """The rule presets every stage that selects the root gets."""

class Stage:
    """One step of a pipeline."""

    goal: str | None
    """What the stage does, in prose; exclusive with `skill`."""
    skill: str | None
    """The skill that carries the goal; exclusive with `goal`."""
    roots: tuple[str, ...] | None
    """The roots the stage selects; none means the Work's own roots."""
    rules_include: tuple[str, ...]
    """The rules or rule presets the stage adds."""
    rules_exclude: tuple[str, ...]
    """The rules or rule presets the stage removes."""
    gate: bool
    """Whether the stage judges an artifact; false by default."""
    judge: Literal["human"] | None
    """Who judges a gate, when it is the driver."""
    session: Literal["any", "fresh"]
    """Whether the stage needs a fresh agent session; `any` by default."""
    continuable: bool
    """Whether an earlier session may continue into it; true by default."""

class RulePreset:
    """A named set of rules to include and exclude."""

    rules_include: tuple[str, ...]
    """The rules the preset includes."""
    rules_exclude: tuple[str, ...]
    """The rules the preset excludes."""

class Ruleset:
    """The settings of one ruleset."""

    alias: str | None
    """The short name its rules are selected by; none by default."""
    root_independent: bool
    """Whether its rules apply to every root; false by default."""

class Config:
    """The effective settings read from `.agents/wio/config.toml`.

    It is immutable once built, so every component that holds it sees the same
    results, Works, templates, trailers, skills, bundle, actions, roots,
    stages, stage presets, rule presets, rulesets and always fields. Two equal
    configs compare and hash equal, and a mapping it holds cannot be changed.
    """

    results: tuple[str, ...]
    """What a gate can decide; `pass`, `fail` and `unknown` by default."""
    works: Works
    """Where Works are found."""
    templates: Templates
    """The templates directory and kinds."""
    trailers: Trailers
    """How records are read."""
    skills: Skills
    """Where skills are found."""
    bundle: Bundle
    """How a bundle is joined."""
    actions: frozendict[str, Action]
    """The actions by name; empty by default."""
    roots: frozendict[str, Root]
    """The roots by name; empty by default."""
    stages: frozendict[str, Stage]
    """The stages by name; empty by default."""
    stage_presets: frozendict[str, tuple[str, ...]]
    """The stages of each stage preset; empty by default."""
    rule_presets: frozendict[str, RulePreset]
    """The rule presets by name; empty by default."""
    rulesets: frozendict[str, Ruleset]
    """The rulesets by name; empty by default."""
    rules_always_include: tuple[str, ...]
    """The rules every bundle includes."""
    rules_always_exclude: tuple[str, ...]
    """The rules no bundle includes."""
