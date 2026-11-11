<!-- wio
id = "zggta5"
template = "feature.draft"
roots = []
depends_on = ["mb4q2g", "d2ytdf"]
-->

# Hooks that run the contracts check

<!--
A draft is working space while an intent is captured. Its define stage
shapes the intent into a feature.leaf or a feature.parent contract and switches
`template`; the Intent section does not carry over.
-->

## Purpose

An agent that edits a contract, and a commit that changes one, must be told of a
problem at once.

## Intent

A `PostToolUse` entry in `.claude/settings.json` and the `wio-contracts` hook of
`prek.toml`, both running `wio contracts check`.
