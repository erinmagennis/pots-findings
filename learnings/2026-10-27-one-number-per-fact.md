# Parallel page builds each invented their own count for the same fact

**Date:** 2026-10-27  **Context:** POTS site design pass, three agents building Home, Start here and Connections at once

## The approach that worked
- Three builders each wrote their own "papers report higher / lower / no difference" count. The same fact came out three
  ways (norepinephrine in POTS: 46/6, 46/8; mast cells in MCAS: 74/24, 75/37). Each page passed its own checks.
- Found by reading the screenshots side by side, not by any verifier.
- Fixed by putting the rule in one module (`site_tools/signals_rules.py`) that matches the already-published table
  (contradictions.json), and making every page's verifier check its numbers against that table.
- Hidden conditions surfaced only when a builder reconciled to the table: treatment findings count, and a flip needs 2+
  distinct papers. They are now written in the module docstring.
- The same page also showed one entity twice with two different "no difference" counts (two definitions). Fix: never show
  the same entity in two lists that count it differently.

## Judgment calls
- Matched the existing Signals table rather than the "more correct" rule (leave out treatment findings), because Signals is
  already live and changing it would move a published number.
- Kept per-page verifiers but wired them into the one site verifier, with a planted fault to prove they run.

## Reusable rule
Before parallel builders show any number that already appears elsewhere on the site, name the one source table it must equal and add a check against that table to each builder's verifier.
