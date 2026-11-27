<!-- wio
code = "PYT004"
name = "prefer-match-and-adts"
-->

Prefer `match` with named guards over long `if` chains, and model variants as
algebraic data types.

Why: Explicit variant types and exhaustive pattern matching make invalid states
unrepresentable and branching easier to verify.
