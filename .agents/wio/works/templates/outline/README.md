<!-- wio
id = "vyjmpc"
template = "feature.draft"
roots = []
depends_on = ["p8vtzx"]
-->

# The outline of a Markdown body

## Purpose

The skeleton, the check of a template and later the contracts command must agree
on which lines of a Markdown body are headings, so one codec finds them.

## Intent

A function in `wio.formats` takes a body and its start line and returns the real
headings, each with its level, its text, its raw line and its line in the file,
skipping lines inside fenced code blocks and HTML comments. The leaf settles
whether `markdown-it-py` or a scanner of its own does it, behind that interface,
and is the only code that imports a Markdown parser.
