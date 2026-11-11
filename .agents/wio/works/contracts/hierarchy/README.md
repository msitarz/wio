<!-- wio
id = "ces6tf"
template = "feature.draft"
roots = []
depends_on = ["xtgz9z"]
-->

# The hierarchy and the dependency graph of the Works

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

Commands need the parents, children and dependents of a Work, the roots a parent
collects and a graph without cycles.

## Intent

Compute parents and children, resolve `@descendants`, build the dependency graph
with each parent's implicit edge to its children, and detect cycles.
