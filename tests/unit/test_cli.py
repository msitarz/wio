from wio.cli import hello


def test_hello():
    assert hello() == "world"
