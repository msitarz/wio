# SPDX-License-Identifier: Apache-2.0
"""The check that the requested Work can be resolved."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tests.fakes import value_or_raise
from wio.context.known_work import KnownWork, _KnownWorkNotImplementedError
from wio.errors import DiagnosticsError
from wio.models.frozen import freeze
from wio.models.resolved import ResolvedContract
from wio.models.works import Work

pytestmark = pytest.mark.xfail(strict=True, raises=_KnownWorkNotImplementedError)


@dataclass
class _Contracts:
    """Give a prepared resolution or refusal and record the lookups."""

    result: ResolvedContract | DiagnosticsError
    calls: list[str] = field(default_factory=list)

    def resolved(self, work_id: str) -> ResolvedContract:
        """Resolve as prepared.

        Args:
            work_id: The requested Work.

        Returns:
            The prepared contract.

        Raises:
            DiagnosticsError: The prepared refusal.
        """
        self.calls.append(work_id)
        return value_or_raise(self.result)

    def view(self, contract: ResolvedContract) -> str:
        """Give no view, which the check has no use for.

        Args:
            contract: The resolved contract.

        Raises:
            AssertionError: Always, because the check renders nothing.
        """
        raise AssertionError(contract)


def test_a_work_that_resolves_passes_without_warnings() -> None:
    """AC-5: a Work that resolves is not refused."""
    # Given a Work that resolves
    work = Work("k3m9xq", "Demo", Path("work.md"), None, (), (), freeze({}))
    contracts = _Contracts(ResolvedContract(work, "", ()))

    # When the run is checked
    warnings = KnownWork(contracts)("k3m9xq", "deliver", "implementation")

    # Then there is no warning and the requested Work was resolved
    assert not warnings
    assert contracts.calls == ["k3m9xq"]


def test_a_refused_work_stops_the_run() -> None:
    """AC-2 to AC-4: the refusal of the lookup is the refusal of the run."""
    # Given a lookup that refuses the Work
    refusal = DiagnosticsError("No Work has the id `nope11`.")
    contracts = _Contracts(refusal)
    check = KnownWork(contracts)

    # When the run is checked
    with pytest.raises(DiagnosticsError) as raised:
        check("nope11", "deliver", "implementation")

    # Then the refusal is passed on as it is
    assert raised.value is refusal
