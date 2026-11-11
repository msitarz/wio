<!-- wio
id = "h3jhtw"
template = "feature.draft"
roots = []
depends_on = ["ces6tf"]
-->

# The resolved view of a Work

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

An agent should read one view of a Work that holds what its ancestors pass on,
never a whole parent contract.

## Intent

Build `ResolvedContract` from the sections that an ancestor's directive source
marks `inherit`. Settles how inherited sections are rendered.
