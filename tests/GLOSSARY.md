# Glossary of `tests`

Terms of the test setup. They bind to this directory and its descendants, and
the nearest `GLOSSARY.md` wins. The terms of the engine are in the
[repository glossary](../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Channel | A way a scenario reaches `wio`: `IN_PROCESS` calls the library in the same process, and `CLI` runs the installed command. |
| Test driver | The object that reaches `wio` for a scenario, on one channel, and returns data without asserting. It narrows the root glossary's Driver: that one advances a Work through its stages, while a test driver only runs `wio` and reports what happened. |
| Facade | The `Wio` object whose verbs a scenario calls, in domain terms; it hides the channel behind a test driver. |
| Sandbox | The directory under `tmp_path` and the environment that a test driver gives `wio`, so a scenario never touches the developer's own state. |
| Group | A directory directly under `tests/` (`unit`, `integration`, `acceptance`, `tooling`, `packaging`, `scripts`) and the marker of the same name, which `tests/conftest.py` sets from the path. |
