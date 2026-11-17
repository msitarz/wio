<!-- wio
id = "22j7aw"
template = "feature.leaf"
roots = ["repo"]
depends_on = ["570wa9", "frspda", "x4vs3k", "37vw05"]

[actions]
deliver = ["implementation", "implementation-review"]
-->

# Adopt wio trailers in the hook and CI

## Purpose

The commit-msg hook and the `records` workflow still run a stand-in script, so
the engine's own records are checked and folded by code the engine does not own.

## Goals

- A commit with a missing or invalid record is rejected at commit time by
  `wio trailers`.
- A pull request's commits are checked, and its body carries their folded
  records, by `wio trailers`.
- The stand-in script and its tests no longer exist.

## Non-Goals

- Updating the documents that mention the script or the `scripts` test group,
  such as `tests/README.md`; the `promote-docs` stage of the parent does that.
- Changing the configured reader.
- Failing CI on an unknown `Wio-` key, which `wio trailers check` warns about
  and the stand-in script rejected; that loosening is intended.

## Assumptions

### A-1

`uv run wio` is available in the hook environment and in the CI job, as it is
for the other `wio` hooks of `prek.toml`.

### A-2

`wio trailers check --require` reads the commit message file that prek passes,
and `check --ref-range` and `fold` take the range `$BASE..$HEAD`.

## Mechanisms

- **`records` hook of `prek.toml`** — the `commit-msg` entry that runs
  `wio trailers check --require` on a commit message file.
- **`.github/workflows/records.yml`** — the job that runs
  `wio trailers check --ref-range` on the commits of a pull request and
  `wio trailers fold body` and `fold block` to copy their folded records to its
  body, or to ask a fork to.

## Acceptance criteria

### **AC-1** The commit-msg hook checks records with `wio trailers`

The `commit-msg` hook of `prek.toml` runs `wio trailers check --require` on the
message, so a commit that needs a record and has none or an invalid one is
rejected.

#### A commit with no record is rejected

- **Given** a non-exempt commit message with no `Wio-*` record.
- **When** the `commit-msg` hook runs.
- **Then** the commit is rejected and the output reports that no record was
  found.

#### A commit with a valid record is accepted

- **Given** a commit message whose record names an existing Work and a stage of
  its actions.
- **When** the `commit-msg` hook runs.
- **Then** the hook passes.

### **AC-2** The `records` workflow checks and folds with `wio trailers`

The `records` workflow runs `wio trailers check --ref-range` on the commits of
a pull request, and takes both the body and the block for a fork from
`wio trailers fold`.

#### A malformed commit fails the job

- **Given** a pull request with one commit whose `Wio-Work` value is not a
  valid id.
- **When** the `records` job runs.
- **Then** the job fails and names that commit.

#### The body ends with the folded records

- **Given** a pull request in the same repository whose body lacks the records
  of its commits.
- **When** the `records` job runs.
- **Then** the body ends with the records that `wio trailers fold body` prints
  for the range.

#### A body that already ends with them is not edited

- **Given** a pull request in the same repository whose body already ends with
  the folded records of its commits.
- **When** the `records` job runs.
- **Then** the body is not edited.

#### A fork whose body is already right passes

- **Given** a pull request from a fork whose body already ends with the folded
  records of its commits.
- **When** the `records` job runs.
- **Then** the job passes.

#### A fork is shown the paragraphs to paste

- **Given** a pull request from a fork, which the workflow cannot edit.
- **When** the `records` job runs.
- **Then** the job fails and its summary shows the paragraphs that
  `wio trailers fold block` prints for the range.

### **AC-3** The stand-in script and its tests are gone

#### No file or reference remains

- **Given** the repository after this Work.
- **When** `scripts/records.py` and `tests/scripts/test_records.py` are looked
  for, and the `records` hook, the workflows, `scripts/` and `tests/` are
  searched for `records.py`.
- **Then** neither file exists and nothing mentions the script.

#### The test group of the script is gone

- **Given** the repository after this Work.
- **When** `tach.toml`, `pyproject.toml` and `tests/conftest.py` are searched
  for the `scripts` test group, and `uv run tach check` runs.
- **Then** the group is in none of them and `uv run tach check` exits 0.
