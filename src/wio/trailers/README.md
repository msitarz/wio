# `wio.trailers`

The component behind `wio trailers`: it judges the records of commits against
the config and the Works, so that every command that handles a record judges it
the same way. A [record](../../../GLOSSARY.md) is a paragraph of
`Wio-*` trailers, and [Records](../../../docs/concepts.md#records) says what
each key means. The component reads the Works through the `Contracts` port of
[`ports.pyi`](ports.pyi) and the config through the shared ports, and it never
knows git, the files or the Works directory.

## Validating the fields of a record

`validate_record` and `validate_names` in [`validation.py`](validation.py) are
the one judgment of a record's fields against the config and the Works, so the
write command and the commit-time check cannot disagree about a record. Their
docstrings say what each takes and returns, `Field` says what a field holds, and
the [tests](../../../tests/unit/trailers/test_validation.py) say how each case
reads.

- **The record's form is not judged here.** The validator takes a record that
  passed the [shape check](../formats/README.md#the-records-of-a-message), so
  its keys are known and its values are well formed. A `Wio-Work: none` record
  has no other key, and the validator has nothing to check on it.
- **A field is a key, a value and an optional line.** The write command builds a
  record from its arguments, which have no lines, and the check reads one from a
  message, so the line is optional and a diagnostic is placed by the line when
  there is one and by the key when there is none.
- **A Work that no one has is an error, and the rest is still checked.** The
  lookup of the `Contracts` port says whether a Work exists, so a record that
  names an absent Work is refused for it, and its other fields are judged on
  their own, except what depends on the Work, which is its items and its
  pipeline.
- **A name the config lacks is an error, and never also a warning.** An action
  or a stage that the config does not have is refused once. A stage that the
  config has but that the Work's pipeline for the action does not list, and an
  action that the config has and the Work lacks, are warnings, because a record
  of such a stage is odd and not wrong. An action that the Work lacks is one
  warning for the Work and not also one for the stage, because a Work without
  the action has no pipeline to list the stage in.
- **Items are each Work's own.** An item that a Work does not have is an error
  that names the item and the Work, and a list of Works is judged Work by Work.
- **A result is present exactly on a gate.** A gate without a result and a
  result on a stage that is not a gate are errors, and a result that the
  config's `gates.results` does not list is one more. The two are independent,
  because each says something different about the record, whether a result may
  be there and whether it is a result at all, and a person fixes them one at a
  time. The messages `result required` and `not a gate` are fixed wording, which
  the commands report as they are. A stage that the config lacks gets no check
  of its result, so the one error for the stage stands alone.
- **The diagnostics come in the order of the fields.** The Work, the action, the
  stage, the items and then the result, an absent field at the place it would
  have, and a warning of a field before an error of a later one, so that the
  same record gives the same lines wherever it is checked.
- **The judge is not judged here.** `Wio-Judge` is checked against its gate by
  the command that records a gate's result.
- **`validate_names` is the names alone, for the later check.** It returns only
  the errors for an action or a stage that the config lacks and for a result
  that `gates.results` does not list, whatever the stage is, and never reads a
  Work, so that the check of a range of commits can turn them into warnings and
  not fail on a record that was valid when it was written.
