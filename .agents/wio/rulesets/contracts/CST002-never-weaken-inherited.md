<!-- wio
code = "CST002"
name = "never-weaken-inherited"
tags = ["contract"]
-->

Never weaken a constraint or a shared guarantee inherited from a parent; amend
the parent instead.

Why: A child that weakens a shared guarantee breaks it for the whole parent
without anyone deciding so.
