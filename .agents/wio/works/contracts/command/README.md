<!-- wio
id = "sz1zsq"
template = "feature.draft"
roots = []
depends_on = ["h69nf8"]
-->

# The contracts command group and the template catalog

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

Every contracts subcommand needs the same command group, the same way to find a
template, and the same conventions, built once so that no leaf creates them and
no two leaves delivered together collide.

## Intent

The `wio contracts` group in `wio.cli` with its help and no subcommand yet, the
template catalog port declared in `wio.contracts` with its provider in
`wio.templates` and its wiring in `wio.cli`, and the loading of the config and
the repository root, the exit codes and `--json` that every subcommand shares.
