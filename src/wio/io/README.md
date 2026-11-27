# `wio.io`

The ports through which wio reaches the filesystem, the standard streams and
the repository, and the real adapters of those ports in
[`adapters.py`](adapters.py). The ports are declared in
[`ports.pyi`](ports.pyi), and how ports and adapters fit together is in the
[architecture](../README.md#ports-and-adapters).

## Reading a repository with git

`GitRepository` and `GitHistory` in [`adapters.py`](adapters.py) are the one
place that runs git to read a repository: the adapters of the `Repository` and
`History` ports. Their docstrings say what each member takes, returns and
raises, the [tests](../../../tests/integration/io/test_git_history.py) say how
each case reads, and `Commit` in [`commits.py`](../models/commits.py) says what
a commit holds. Every command that reads revisions, the index or the state of
the tree goes through these ports and never calls git itself.

- **Git is assumed to be installed and on `PATH`.** The `git` reader of
  trailers needs it wherever wio runs, so the adapters add no requirement and
  have no fallback; a git that cannot be run is a `RuntimeError` that says so.
- **Git runs where the environment says.** Both adapters are given an
  `Environment` and run git in the working directory it reports, never in one
  they find themselves, so a test can fix it. A directory that is not usable, a
  directory outside a repository and a git that cannot be run each raise a
  `RuntimeError` that names the directory and says what to do.
- **A refused revision is a `ValueError`, and it names the revision.** The
  message is git's own followed by the command, so a person sees what was asked.
  The two errors stay apart because a caller treats a wrong environment and a
  wrong revision differently.
- **What git prints is kept as it is.** The output is read as bytes and decoded
  as UTF-8, with no translation of line endings, so a file, a staged file or a
  commit message with a CRLF comes back with its carriage returns. A reader of
  trailers or a hash of the content would otherwise see text that was never
  committed. Content that is not UTF-8 raises a `ValueError`.
- **A revision is never read as an option.** A revision that begins with `-` is
  refused, and a tag is peeled to the commit it names, so `rev_parse` always
  gives the full id of a commit.
- **Paths are relative to the root, from any directory.** `list_files`, `show`
  and `show_index` take and give paths from the top of the working tree whatever
  the working directory inside it is, `list_files` sorts them by path, and the
  names are read with NUL separators, so no name is quoted or split. A file that
  did not exist, and a path that names a directory, read as no file and never as
  an error.
- **A read changes nothing.** The index, the refs and the working tree are the
  same afterwards. `is_dirty` takes no optional lock, because a plain
  `git status` refreshes the index that it reads and the status of a repository
  must not change it.
- **The order is the history's.** `history` gives parents before children,
  oldest first, and `first_parents` gives the walk along first parents, newest
  first, so a commit that a merge brought in is not in it.

## The views of the index and of a revision

`HeadFiles` and `IndexFiles` in [`views.py`](views.py) are read-only
`FileSystem`s over the `History` and `Repository` ports, so the code that reads
a tree of files, such as the discovery of Works, runs unchanged on a revision or
on the index. Their docstrings say what each holds and how it answers, and the
[tests](../../../tests/unit/io/test_views.py) say how each case reads. Like the
git adapters, they are imported only by `wio.cli` and the tests, and they never
call git themselves.

- **A view holds files, and a directory is a file below it.** A directory exists
  when a file of the view lies below it, a symbolic link never exists, and
  writing or appending raises `PermissionError`, so a command that reads cannot
  change what it reads. A path is absolute and below the root, and any other
  path is no path of the view.
- **A repository with no commit holds no file in `HEAD`.** The view of `HEAD`
  is empty then, so the first commit of a repository is checked like any other.
- **The index is listed through its candidates.** The `Repository` port reads a
  staged file by its path and lists none, so `IndexFiles` takes the Markdown
  files below its directory from the working tree and every file below it from
  `HEAD` and keeps those that the index holds. A file that is staged and is in
  neither place is not seen, and a file that the index lacks is not held,
  whatever the other two have.
- **A file that is not UTF-8 text is held and fails when it is read.** One such
  file below the directory therefore leaves every other file listed, and the
  reader that meets it decides, as it does for a file of the working tree.
- **A view reads its listing once.** Its file and directory queries answer from
  one listing, so a caller that needs to see a later change builds a new view.
  Path resolution instead uses the [local filesystem](paths.py), as the shared
  filesystem port requires, and follows links without requiring the target to
  exist.
