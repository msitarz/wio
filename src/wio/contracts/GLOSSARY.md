# Glossary of `src/wio/contracts`

Terms of finding Works. They bind to this directory and its descendants, and the
nearest `GLOSSARY.md` wins. The terms of the architecture are in the
[glossary of `src/wio`](../GLOSSARY.md) and those of the engine in the
[repository glossary](../../../GLOSSARY.md).

| Term | Meaning |
| --- | --- |
| Left out | A file that discovery could not identify as a Work, and so reports with one error: one that cannot be read or decoded, a block that cannot be read, a marker of an unknown version, or an `id` that is missing, not a string or empty. A file that a nesting collision excludes is not left out. |
| Excluded | A marked file that the nesting rules remove from the Works without it being left out: one of the files of a directory that holds two or more, or one directly in the Works directory. A file that is both is left out. |
| Incomplete tree | A tree in which a Work is left out, a collision excluded files, a marked file sits directly in the Works directory, or the Works directory cannot be walked, so that a command may not trust it to hold every Work. A wrong optional field and a shared id do not make it so. |
