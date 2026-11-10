<!-- wio
id = "6k795v"
template = "feature.draft"
roots = []
depends_on = ["0nfz54", "776g94"]
-->

# Showing a template

## Purpose

An agent must be able to see the shape of a template without creating a Work.

## Intent

`wio templates show <name>` prints the bare skeleton, with no header, no stderr
and no `--json`; an unknown name is an error.
