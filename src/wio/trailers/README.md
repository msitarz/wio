# `wio.trailers`

The component behind `wio trailers`: it prints and judges the records of commits
against the config and the Works, so that every command that handles a record
judges it the same way. A [record](../../../GLOSSARY.md) is a paragraph of
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

## Printing a record

`run_write` and `configure_write` in [`write.py`](write.py) are the write form
of `wio trailers`, `wio trailers <work> <action> <stage>`, which prints the
record that an agent adds to its commit message. `wio.cli` dispatches on the
first argument, wires the ports and turns an error into the exit code 2, so this
module holds only what the form does and is run in a test with fakes. Their
docstrings say what each takes, prints and raises, and the
[tests](../../../tests/unit/trailers/test_write.py) say how each case reads.

- **A record is printed only when every field holds, and then alone.** Nothing
  is written to standard output when anything is an error, so an agent that
  appends the output to a message never appends half a record. The findings go
  to standard error.
- **The record is built from the arguments and laid out by the shared
  renderer.** The `--items` ids are joined by a comma and one space in the order
  given, the judge is `agent` when a result is given and no judge is, and the
  lines come in the order of the keys whatever the order of the options. The
  form never lays out a line itself, so no second layout can disagree with the
  parser's.
- **An argument cannot add a line to the record.** An argument that is empty or
  holds a line end, and a judge without a result, are refused as the finding of
  their field before the record is rendered, one finding at most for a field and
  the empty or line-end one first, and the offending line shows a line end as an
  escape, so that what is printed to refuse an argument is one line too.
- **The checks run in order, and the first that finds something stops the
  rest.** The refusal of an argument, then the shape check with the reader of
  the config, and only when that finds nothing the
  [validator](#validating-the-fields-of-a-record), so a record of a wrong form
  never reaches the validator, and a finding is never reported twice. A Work
  that only `HEAD` has, because the commit being made deletes it, is still
  found, for the `Contracts` port looks in `HEAD` after the working tree, so the
  commit that retires or abandons a Work can carry its record.
- **A finding is a line on standard error that names its field.** A finding of
  form is `error: <key>: <message>` followed by the offending line, and a
  diagnostic of the validator is `<severity>: <where>: <message>` with the key
  of the field as `<where>`, because a record built from arguments has no lines.
  A warning does not stop the record, which is printed with the exit code 0, and
  a refused field is the exit code 1.
- **A call that no form accepts is a usage error and exits 2.** A Work that is a
  list or `none` is refused before the config is loaded. The
  [concepts](../../../docs/concepts.md#records) allow both for a record, but
  this form writes one record for one Work, and a later form may write the rest.
  A missing stage, an unknown option or a config that cannot be read are refused
  by argparse and by the loader, so a mistake in how the command is called is
  never mistaken for a record that does not hold. The dispatch on the first
  argument and the turning of every such error into the exit code 2 belong to
  the command that wires the forms together, in `wio.cli`, and not to this
  module.
- **A stage outside the Work's pipeline is a warning here as well.** The record
  is printed and the warning goes to standard error, as the validator reports
  it, because a record of such a stage is odd and not wrong.
- **A cited item is accepted and ignored.** The gate form that records a result
  handles it, and accepting it here keeps one set of options for both.
