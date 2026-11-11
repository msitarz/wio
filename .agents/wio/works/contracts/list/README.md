<!-- wio
id = "q6wxj6"
template = "feature.draft"
roots = []
depends_on = ["ces6tf"]
-->

# Listing the Works

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

People and agents need to see the Works and their hierarchy at a glance.

## Intent

`wio contracts list` with the id, title, path, template, roots and dependencies
of each Work, nested under `nesting`, and `--json`.
