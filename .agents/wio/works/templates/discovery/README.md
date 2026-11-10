<!-- wio
id = "776g94"
template = "feature.draft"
roots = []
depends_on = ["p8vtzx"]
-->

# Finding and listing templates

## Purpose

People and agents must find the templates of a project and which one a kind
starts from.

## Intent

Walk the templates directory, name a template by its file stem, drop the `name`
key, build `Template`, and add `wio templates list` with `--kind`, the entry
marker, the grouped layout and `--json`.
