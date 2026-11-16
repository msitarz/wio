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
        title: The ancestor's first heading as the view names it: the text of the
            first real heading of its body at any level, with a readable
            directive list taken off.
        sections: The sections in the ancestor's order, each as it stands in the
            view: its heading line demoted by one level, never below level 6,
            with its directive list taken off when the list can be read, and its
            text, without the blank lines that end it.
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
        own: The Work's own contract as the view starts with it: the text after
            its metadata block, with LF endings, every comment kept, the directive
            list taken off every heading whose list can be read, and no blank
            line at either end. It is empty for a contract with nothing after its
            block.
        inherited: What each ancestor that passes anything contributes, nearest
            ancestor first. It is empty for a Work without a parent, under
            `flat`, and when no ancestor passes a section.
    """

    work: Work
    own: str
    inherited: tuple[InheritedSections, ...]
