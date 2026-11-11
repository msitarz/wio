<!-- wio
id = "mwyc7s"
template = "feature.draft"
roots = []
depends_on = ["xtgz9z"]
-->

# The skeleton of an existing Work

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

A stage that moves a Work to another template must keep its id and dependencies,
so that it keeps its records.

## Intent

`wio contracts skeleton <template> --work <id>` with `--keep`, which prints the
skeleton and lists on standard error what it dropped.
