# SPDX-License-Identifier: Apache-2.0
"""The type for the project's settings, an immutable tree of plain data.

Every field is named as its TOML key, so a key path such as
`works.defaults.actions` is a chain of field names. A `Config` built with no
arguments is the effective settings of an empty config file, and every field
carries a one-sentence description in its metadata, which a message can quote.
A `Config` holds what it is given: it judges nothing. The field names are part of
the contract of the type, and the names of the nested types are provisional.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Defaults:
    """The default pipelines of the actions, for Works without a template."""

    actions: frozendict[str, str | tuple[str, ...]] = field(
        default=frozendict(),
        metadata={
            "description": (
                "The stage preset or the stages of each action; empty by default."
            )
        },
    )


@dataclass(frozen=True)
class Works:
    """Where wio finds Works and how it derives their hierarchy."""

    dir: str = field(
        default=".agents/wio/works",
        metadata={
            "description": "The Works directory; `.agents/wio/works` by default."
        },
    )
    hierarchy: Literal["flat", "nesting"] = field(
        default="flat",
        metadata={"description": "How the hierarchy is derived; `flat` by default."},
    )
    defaults: Defaults = field(
        default=Defaults(),
        metadata={"description": "The defaults of Works that name no template."},
    )


@dataclass(frozen=True)
class Templates:
    """Where the templates live and which one each kind starts from."""

    dir: str = field(
        default=".agents/wio/templates",
        metadata={
            "description": (
                "The templates directory; `.agents/wio/templates` by default."
            )
        },
    )
    kinds: frozendict[str, str] = field(
        default=frozendict(),
        metadata={"description": "The entry template of each kind; empty by default."},
    )


@dataclass(frozen=True)
class Trailers:
    """How the records of commits are read."""

    reader: Literal["scan", "git"] = field(
        default="scan",
        metadata={
            "description": "Who parses trailers, wio's scan or git; `scan` by default."
        },
    )


@dataclass(frozen=True)
class Skills:
    """Where the skills a stage names are looked up."""

    paths: tuple[str, ...] = field(
        default=(),
        metadata={
            "description": "The directories searched for skills; none by default."
        },
    )


@dataclass(frozen=True)
class Gates:
    """What the gates of the stages can decide."""

    results: tuple[str, ...] = field(
        default=("pass", "fail", "unknown"),
        metadata={
            "description": (
                "What a gate can decide; `pass`, `fail` and `unknown` by default."
            )
        },
    )


@dataclass(frozen=True)
class Bundle:
    """How a context bundle is joined."""

    separator: str = field(
        default="\n\n",
        metadata={
            "description": (
                "The text between the parts of a bundle; a blank line by default."
            )
        },
    )
    size_threshold: int | None = field(
        default=None,
        metadata={
            "description": (
                "The size above which a bundle is warned about; none by default."
            )
        },
    )


@dataclass(frozen=True)
class Action:
    """One action a Work can run."""

    description: str = field(
        metadata={"description": "What the action does; required."}
    )
    after: tuple[str, ...] = field(
        default=(),
        metadata={
            "description": "The actions this one is proposed after; none by default."
        },
    )
    invalidated_by: tuple[str, ...] = field(
        default=(),
        metadata={
            "description": (
                "The actions whose newer records make this one stale; none by default."
            )
        },
    )
    on_demand: bool = field(
        default=False,
        metadata={
            "description": "Whether `wio next` never proposes it; false by default."
        },
    )


@dataclass(frozen=True)
class Root:
    """A named area of the repository."""

    paths: tuple[str, ...] = field(
        metadata={"description": "The paths of the root; required."}
    )
    rule_presets: tuple[str, ...] = field(
        default=(),
        metadata={
            "description": "The rule presets every stage that selects the root gets."
        },
    )


@dataclass(frozen=True)
class Stage:
    """One step of a pipeline."""

    goal: str | None = field(
        default=None,
        metadata={
            "description": "What the stage does, in prose; exclusive with `skill`."
        },
    )
    skill: str | None = field(
        default=None,
        metadata={
            "description": "The skill that carries the goal; exclusive with `goal`."
        },
    )
    roots: tuple[str, ...] | None = field(
        default=None,
        metadata={
            "description": (
                "The roots the stage selects; none means the Work's own roots."
            )
        },
    )
    rules_include: tuple[str, ...] = field(
        default=(),
        metadata={"description": "The rules or rule presets the stage adds."},
    )
    rules_exclude: tuple[str, ...] = field(
        default=(),
        metadata={"description": "The rules or rule presets the stage removes."},
    )
    gate: bool = field(
        default=False,
        metadata={
            "description": "Whether the stage judges an artifact; false by default."
        },
    )
    judge: Literal["human"] | None = field(
        default=None,
        metadata={"description": "Who judges a gate, when it is the driver."},
    )
    session: Literal["any", "fresh"] = field(
        default="any",
        metadata={
            "description": (
                "Whether the stage needs a fresh agent session; `any` by default."
            )
        },
    )
    continuable: bool = field(
        default=True,
        metadata={
            "description": (
                "Whether an earlier session may continue into it; true by default."
            )
        },
    )


@dataclass(frozen=True)
class RulePreset:
    """A named set of rules to include and exclude."""

    rules_include: tuple[str, ...] = field(
        default=(), metadata={"description": "The rules the preset includes."}
    )
    rules_exclude: tuple[str, ...] = field(
        default=(), metadata={"description": "The rules the preset excludes."}
    )


@dataclass(frozen=True)
class Ruleset:
    """The settings of one ruleset."""

    alias: str | None = field(
        default=None,
        metadata={
            "description": "The short name its rules are selected by; none by default."
        },
    )
    root_independent: bool = field(
        default=False,
        metadata={
            "description": "Whether its rules apply to every root; false by default."
        },
    )


@dataclass(frozen=True)
class Config:
    """The effective settings read from `.agents/wio/config.toml`.

    It is immutable once built, so every component that holds it sees the same
    gates, Works, templates, trailers, skills, bundle, actions, roots,
    stages, stage presets, rule presets, rulesets and always fields. Two equal
    configs compare and hash equal, and a mapping it holds cannot be changed.
    """

    gates: Gates = field(
        default=Gates(),
        metadata={"description": "What a gate can decide."},
    )
    works: Works = field(
        default=Works(), metadata={"description": "Where Works are found."}
    )
    templates: Templates = field(
        default=Templates(),
        metadata={"description": "The templates directory and kinds."},
    )
    trailers: Trailers = field(
        default=Trailers(), metadata={"description": "How records are read."}
    )
    skills: Skills = field(
        default=Skills(), metadata={"description": "Where skills are found."}
    )
    bundle: Bundle = field(
        default=Bundle(), metadata={"description": "How a bundle is joined."}
    )
    actions: frozendict[str, Action] = field(
        default=frozendict(),
        metadata={"description": "The actions by name; empty by default."},
    )
    roots: frozendict[str, Root] = field(
        default=frozendict(),
        metadata={"description": "The roots by name; empty by default."},
    )
    stages: frozendict[str, Stage] = field(
        default=frozendict(),
        metadata={"description": "The stages by name; empty by default."},
    )
    stage_presets: frozendict[str, tuple[str, ...]] = field(
        default=frozendict(),
        metadata={"description": "The stages of each stage preset; empty by default."},
    )
    rule_presets: frozendict[str, RulePreset] = field(
        default=frozendict(),
        metadata={"description": "The rule presets by name; empty by default."},
    )
    rulesets: frozendict[str, Ruleset] = field(
        default=frozendict(),
        metadata={"description": "The rulesets by name; empty by default."},
    )
    rules_always_include: tuple[str, ...] = field(
        default=(), metadata={"description": "The rules every bundle includes."}
    )
    rules_always_exclude: tuple[str, ...] = field(
        default=(), metadata={"description": "The rules no bundle includes."}
    )
