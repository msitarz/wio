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
- The warning does not depend on where the bundle is delivered.

## Non-Goals

- Shortening or splitting the bundle.
- Writing the file, which the sibling does.

## Assumptions

### A-1

The size threshold of the config's bundle settings is in bytes, the unit of the
size the header states.

### A-2

Where the scope document and the concepts say "a bundle larger than the
configured threshold", it is right to compare the body, as the header states its
size, and the docs stage corrects both documents and the description of
`Bundle.size_threshold` in `src/wio/models/config.py`.

### A-3

The compiler result carries the UTF-8 bytes of the body, which are the number
that the header states, as the command Work's compiler port says.

## Mechanisms

- **`size_threshold`** — in the config's bundle settings, none by default, read
  through the shared `Settings` port.

## Acceptance criteria

### **AC-1** A body above the threshold is warned about

A body larger than the threshold gives a warning that names the size and the
threshold, and the bundle is still delivered.

#### Above and within

- **Given** a threshold of 1000 and compiler results whose bodies are 1001 and
  1000 bytes.
- **When** `wio context` runs for each.
- **Then** the first reports a warning that names 1001 and 1000, and the second
  reports none, and both deliver their bundle and exit 0.

### **AC-2** No threshold, no warning

A config with no threshold never gives this warning.

#### No threshold

- **Given** a config with no `size_threshold` and a very large body.
- **When** `wio context` runs.
- **Then** no warning about the size is reported.

### **AC-3** The warning does not depend on the destination

The same body gives the same warning on standard output and with `--output`.

#### Both destinations

- **Given** a threshold below the size of a body.
- **When** `wio context` runs without `--output` and with it.
- **Then** each reports the same warning and exits 0.

### **AC-4** A threshold of zero or less warns for any larger body

The comparison is that the size is greater than the threshold, so a threshold of
zero or a negative one warns for every body with bytes.

#### Zero and negative

- **Given** thresholds of 0 and -1 and a body of 1 byte.
- **When** `wio context` runs for each.
- **Then** each reports a warning that names 1 and the threshold.
