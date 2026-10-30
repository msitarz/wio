# SPDX-License-Identifier: Apache-2.0
from wio.cli import hello


def test_hello():
    assert hello() == "world"
