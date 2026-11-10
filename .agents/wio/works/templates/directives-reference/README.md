<!-- wio
id = "whhw53"
template = "feature.draft"
roots = []
depends_on = ["1n1p8j", "776g94"]
-->

# Printing the directive grammar

## Purpose

A person or an agent that writes a template must be able to learn which
directives exist and how to write them without leaving the command line.

## Intent

`wio templates directives` prints the table of directives of `wio.formats` with
each one's syntax, meaning and example, as an indented list for a person and as
one JSON array for a program with `--json`. It reads no config and no file, so
it works outside a repository.
