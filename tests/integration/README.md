# wio integration tests

How to write an integration test. It adds to the [test strategy](../README.md),
which says when a test is an integration test.

The subject of the test is real: the adapter on real git or a real disk, the
working directory and environment of the process, a fresh interpreter, the
installed command. Fake only what is not the subject. A fake that unit tests
also use lives in `tests/fakes.py`, and an integration test never imports a unit
test. `tests/integration/` mirrors `src/wio/`.
