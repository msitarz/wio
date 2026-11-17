# SPDX-License-Identifier: Apache-2.0
"""The spec of the write form of `wio trailers`: print a checked record.

`wio trailers <work> <action> <stage>` prints the record for a Work, an action and
a stage, with optional item ids, a result and a judge, when every field holds, and
nothing when one does not. `wio.cli` dispatches on the first argument and wires
the ports, and this module holds what the form does, so the form is run in a test
with fakes of the ports.

The stub is the spec until the wiring stage of the Work that builds the write form
writes the module `wio.trailers.write` and deletes this stub, so the spec and the
code never coexist.
"""

from argparse import ArgumentParser, Namespace

from wio.io.ports import Stdio
from wio.trailers import Services

def configure_write(parser: ArgumentParser) -> None:
    """Add the arguments of the write form to its parser.

    It does no I/O. The positional arguments are the Work, the action and the stage,
    which argparse refuses to lack, and the options are `--items`, a comma-separated
    list of item ids, `--result`, `--judge` and `--cite`, which is repeated, is
    accepted and is ignored here because the gate leaf handles it. An unknown option
    is argparse's usage error.

    Args:
        parser: The parser that `wio.cli` created for the form.
    """
    ...

def run_write(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Print the record of the arguments, or say why it is refused.

    The record is built from the arguments with the judge `agent` when a result is
    given and no judge is, and it is judged in this order. An argument that is empty
    or holds a line end is refused as the finding of its field, so no argument can
    add a line to the record. The record is rendered and `check_shape` judges it
    with the reader of the config, and only when that finds nothing does
    `validate_record` judge its fields against the config and the Works, which the
    `Contracts` port finds in the working tree and then in `HEAD`. A `--judge`
    without a result is refused as the finding of `Wio-Judge`.

    Each finding of the shape check is written to standard error as
    `error: <key>: <message>` followed by its offending line, and each diagnostic of
    the validator as `<severity>: <where>: <message>`, in the order they come, with
    the key of the field as `<where>`. Nothing is written to standard output when
    anything is an error. A warning does not stop the record, which is written to
    standard output with its lines in the order of the keys.

    Args:
        services: The ports the form reads the config and the Works through.
        args: The arguments that `configure_write` parsed.
        stdio: Where the record and the findings are written.

    Returns:
        0 for a record that is printed, with or without a warning, and 1 for a field
        that is refused.

    Raises:
        TrailersError: If the Work is a list of ids or `none`, which this form does
            not write.
        ConfigurationError: If the config cannot be read.
    """
    ...
