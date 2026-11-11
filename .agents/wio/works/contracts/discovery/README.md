<!-- wio
id = "xtgz9z"
template = "feature.draft"
roots = []
depends_on = ["h69nf8"]
-->

# Finding the Works

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

Every command needs the same answer to which files are Works.

## Intent

Walk the Works directory, read each block, build the `Work`, honour both
hierarchy modes, and report duplicate ids, unreadable blocks and the reasons a
file is not a Work as diagnostics.
