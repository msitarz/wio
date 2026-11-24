<!-- wio
id = "jcax3k"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss", "bg0g78"]
-->

# Warn about an oversized bundle

## Purpose

A harness truncates long output and a truncated bundle looks complete, so a
driver must be told when a bundle is larger than the project allows.

## Goals

- A driver is warned when the size of the body is above the configured
  threshold.
- A driver is not warned when no threshold is configured or the body is within
  it.
- The warning compares the number that the header states.

## Non-Goals

- Shortening or splitting the bundle.
- Writing the file, which the sibling does.

## Assumptions

### A-1

The size threshold of the config's bundle settings is in bytes, the unit of the
size the header states.

## Mechanisms

- **`size_threshold`** — in the config's bundle settings, none by default.

## Acceptance criteria

### **AC-1** A body above the threshold is warned about

A body larger than the threshold gives a warning that names the size and the
threshold, and the bundle is still printed.

#### Above and within

- **Given** a threshold of 1000 and bodies of 1001 and 1000 bytes.
- **When** `wio context` runs for each.
- **Then** the first reports a warning that names 1001 and 1000, and the second
  reports none, and both print their bundle and exit 0.

### **AC-2** No threshold, no warning

A config with no threshold never gives this warning.

#### No threshold

- **Given** a config with no `size_threshold` and a very large body.
- **When** `wio context` runs.
- **Then** no warning about the size is reported.
