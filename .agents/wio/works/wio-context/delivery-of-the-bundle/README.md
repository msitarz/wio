<!-- wio
id = "ymckyf"
template = "feature.parent"
roots = ["@descendants"]
depends_on = []
-->

# Delivery of the bundle

## Purpose

A harness truncates long command output and a truncated bundle looks complete,
so a session must be able to read the bundle from a file and must be told when
it is large.

## Goals

- A session can read the bundle from a file when it asks for one.
- A driver is warned when the bundle is larger than the configured threshold.

## Non-Goals

- Compiling the bundle, which the composition does.
- Shortening a bundle that is large, which a project does with its rules.

## Assumptions

None.

## Visuals

Before, the command prints only to standard output. After, it can also write the
bundle to a file and print the file's path, and it warns when the body is larger
than the configured threshold.

## Acceptance criteria

### **AC-1** A large bundle is warned about and can be read from a file

For a bundle over the threshold, the command warns, and `--output` gives a file
that holds the bundle.

#### An oversized bundle through a file

- **Given** a size threshold below the size of the body of a bundle.
- **When** `wio context --output` runs for it.
- **Then** a warning is reported, the path of a file is printed, and the file
  holds the bundle.
