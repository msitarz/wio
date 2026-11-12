# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts check` reports about the body of a contract."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.block import MetadataBlock
    from wio.models.diagnostics import Diagnostic
    from wio.models.template import Template
    from wio.models.works import Work


class BodyChecker:
    """Checks the body of each contract against its source of directives.

    One checker serves one run of the check. It reads the file of a template once
    and shares what it found with every contract that follows the template, and
    it reads nothing else than through `files`, and writes nothing.
    """

    def __init__(self, root: Path, files: FileSystem) -> None:
        """Keep what a read of a template needs, and start with none made.

        Args:
            root: The repository root, which a template's `path` is relative to.
            files: The port that reads a template's file.
        """
        raise NotImplementedError

    def check(
        self, work: Work, block: MetadataBlock, template: Template | None
    ) -> list[Diagnostic]:
        """Check the body of one contract.

        The source of directives is the template that the contract names, and
        only that: `work.template` names none, and then the source is the
        contract's own `##` headings and only those, and `template` is `None`; or
        it names one and `template` is what the catalog gave for it. A contract
        that names a template that is missing or rejected, which is `template`
        `None` with `work.template` set, gets no diagnostic at all, because the
        check of the Works has reported it. A template whose file cannot be read
        or has no metadata block is skipped the same way, because `wio templates
        check` reports it. A section is a `##` heading and what follows it up to
        the next heading of level 1 or 2, and sections deeper than level 2 are
        free.

        A `##` heading of the contract matches one of the template by its text,
        ignoring case, the whitespace around it and a trailing directive list,
        and nothing else is normalized. When a `##` heading is repeated, in the
        contract or in the template, the first is the section. A directive list is
        anything that begins with the opener `<!-- wio:`, and the heading's text
        for matching is what comes before it.

        With a template:

        - A section that the template marks `required` and the contract lacks is
          an error at the file, ``The section `Goals` is required by the template
          `t` ``, named as the template writes it.
        - A directive list in the contract, on a heading of any level and whatever
          its syntax, changes nothing and is a warning at `<file>:<line>` of the
          heading, one for each list, ``The directive list is ignored because the
          contract follows the template `t` ``, and the parser's errors are not
          reported.
        - A `##` heading that the template does not have is a warning at its line,
          ``The section `Constraint` is not in the template `t` ``, with ``. Did
          you mean `Constraints`?`` when `closest_key` finds one among the texts of
          the template's sections as written.

        Without a template, the directives are those of the contract's own `##`
        headings. A list that the parser refuses is an error at
        `<file>:<line>:<column>` with the parser's column, and a list on a heading
        that is not level 2 is an error at the column of its opener, ``Directives
        are read on level-2 headings only``.

        In both cases the items of each section that has `items` or `pattern`
        directives are found and judged with `find_items` and `judge_items`, over
        the first section of each text only, which are counted and whose ids are
        checked. A repeated `##` heading is a warning at its line, ``The section
        `Goals` is repeated; the first one counts``, and carries no items. A
        contract with no title, which is `work.title` `None`, is a warning at the
        file, ``The contract has no title``. The sections that a contract inherits
        are not checked.

        Args:
            work: The Work, for its file and its title.
            block: Its metadata block, read again, whose body is checked and whose
                `body_start_line` gives each heading its line in the file.
            template: The template the catalog gave for `work.template`, or `None`
                when the Work names none or names one that is missing or rejected.

        Returns:
            The findings in any order, none for a contract whose template is
            missing, rejected or unreadable.
        """
        raise NotImplementedError
