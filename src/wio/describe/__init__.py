# SPDX-License-Identifier: Apache-2.0
"""Self-description models and registry for `wio describe`."""

lazy from wio.describe.models import (
    CommandDescription,
    CommandForm,
    CommandSummary,
    Concept,
    EngineDescription,
    ExitCode,
    ReferenceEntry,
    ReferenceTable,
)
lazy from wio.describe.registry import (
    describe_command,
    describe_engine,
    registered_commands,
)

__all__ = [
    "CommandDescription",
    "CommandForm",
    "CommandSummary",
    "Concept",
    "EngineDescription",
    "ExitCode",
    "ReferenceEntry",
    "ReferenceTable",
    "describe_command",
    "describe_engine",
    "registered_commands",
]
