<!-- wio
code = "UPK002"
name = "correct-diagrams-to-the-implementation"
tags = ["delivery"]
-->

When the verified implementation differs from a diagram in the contract, correct
the diagram as a ratify: run `wio context <id> ratify ratify`, in this session
or a new one, and commit the correction with that stage's record.

Why: A stale diagram is believed over the code by every reader who does not
check, and a ratify record keeps the correction visible without making the
delivered stages stale.
