# SPDX-License-Identifier: Apache-2.0
"""The types of a Work's resolved view: its contract and what its ancestors pass."""

from dataclasses import dataclass

lazy from wio.models.works import Work


@dataclass(frozen=True)
class InheritedSections:
    """The sections that one ancestor passes on to a Work.

    It is immutable and exists only for an ancestor that passes at least one
    section.

    Attributes:
        ancestor: The ancestor the sections come from.
        title: The ancestor's title as the view names it.
        sections: The sections in the ancestor's order, each already in the form
            the view shows, so rendering only joins them.
    """

    ancestor: Work
    title: str
    sections: tuple[str, ...]


@dataclass(frozen=True)
class ResolvedContract:
    """A Work's contract with the inheritable sections of its ancestors.

    It is what a context bundle shows an agent for a Work: the Work's own
    contract plus the sections its ancestors mark as inherited, so the agent
    never reads a parent's whole contract. It holds the parts of the view and
    not its text, which `render_resolved` writes, so that every command that
    shows the view prints the same bytes.

    Attributes:
        work: The Work the view is of.
        own: The Work's own contract in the form the view starts with, empty for
            a contract with nothing after its metadata block.
        inherited: What each ancestor that passes anything contributes, nearest
            ancestor first, empty for a Work without a parent, under `flat`, and
            when no ancestor passes a section.
    """

    work: Work
    own: str
    inherited: tuple[InheritedSections, ...]
