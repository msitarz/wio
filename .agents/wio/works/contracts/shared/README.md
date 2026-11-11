<!-- wio
id = "h69nf8"
template = "feature.draft"
roots = []
depends_on = []
-->

# Shared helpers of the templates and contracts commands

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

`wio.templates` and `wio.contracts` need the same walk of the Works directory,
key check and ordering of diagnostics, and neither may import the other.

## Intent

Move the walk to `wio.io`, the unknown-key check to `wio.formats`, and
`has_error` and the ordering key to `wio.models`, unchanged, so `wio templates`
prints the same bytes.
