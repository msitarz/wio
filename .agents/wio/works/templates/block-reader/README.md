<!-- wio
id = "p8vtzx"
template = "feature.draft"
roots = []
depends_on = []
-->

# Reading the metadata block

## Purpose

Every file that carries wio metadata needs one reader that splits the metadata
block from the body.

## Intent

Read the `<!-- wio` and `+++` forms in `wio.formats`, split metadata from body,
and place a TOML error at its line in the file.
