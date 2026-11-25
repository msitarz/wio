<!-- wio
id = "jcax3k"
template = "feature.leaf"
roots = ["wio"]
depends_on = ["b53rss"]
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
- Writing the file, and the warning's independence of where the bundle goes,
  which the parent states.

## Assumptions

### A-1

The size threshold of the config's bundle settings is in bytes, the unit of the
size the header states, and no config check rejects zero or a negative number.

### A-2

Where the scope document and the concepts say "a bundle larger than the
configured threshold", it is right to compare the body, as the header states its
size, and the docs stage corrects both documents, records the unit, and corrects
the description of `Bundle.size_threshold` in `src/wio/models/config.py`.

### A-3

The compiler result carries the size of the body in UTF-8 bytes as an integer,
which is the number that the header states, as the command Work's compiler port
says.

## Mechanisms

- **`size_threshold`** — in the config's bundle settings, none by default, read
  through the shared `Settings` port.
- **The warning** — a line on standard error, in the form that the command Work
  gives, which the command reports before it delivers the bundle, so that a
  failed delivery still shows it.

## Acceptance criteria

### **AC-1** A body above the threshold is warned about

A body larger than the threshold gives a warning that names the size from the
compiler result and the threshold, and the bundle is still delivered; the size
comes from the result and not from the length of the text.

#### Above and within

- **Given** a threshold of 1000 and compiler results whose bodies are 1001 and
  1000 bytes, whose texts are 1400 bytes long.
- **When** `wio context` runs for each.
- **Then** the first reports a warning that names 1001 and 1000, and the second
  reports none, and both deliver their bundle and exit 0.

### **AC-2** No threshold, no warning

A config with no threshold never gives this warning.

#### No threshold

- **Given** a config with no `size_threshold` and a compiler result whose body
  is 1000000 bytes.
- **When** `wio context` runs.
- **Then** no warning about the size is reported.

### **AC-3** A threshold of zero or less warns for any larger body

The comparison is that the size is greater than the threshold, so a threshold of
zero or a negative one warns for every body with bytes.

#### Zero and negative

- **Given** thresholds of 0 and -1 and a compiler result whose body is 1 byte,
  which a fake compiler gives.
- **When** `wio context` runs for each.
- **Then** each reports a warning that names 1 and the threshold.
