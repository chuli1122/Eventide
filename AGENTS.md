<!--
SPDX-FileCopyrightText: 2026 Chuli (@chuli1122) <https://github.com/chuli1122>
SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
-->

# Eventide Agent Instructions

## Licensing and attribution

- Preserve `LICENSE`, `LICENSES/`, every `Required Notice:` line, and all SPDX copyright and license declarations.
- Preserve existing `SPDX-FileCopyrightText` lines. New source, test, example, documentation, configuration, and workflow files must record the actual copyright holder and be covered by the repository's SPDX/REUSE metadata.
- Do not change the project license, copyright holder, attribution, or commercial-use policy without an explicit instruction from the repository owner.
- Do not add dependencies or copied code whose terms conflict with `PolyForm-Noncommercial-1.0.0`.
- Do not implement attribution through runtime traps, hidden identifiers, dead code, or behavior that makes the software fail when notices are changed.

## Verification

After relevant changes, run:

```bash
reuse lint
PYTHONPATH=src python3 -m unittest discover -s tests
python3 -m compileall -q src examples tests
```
