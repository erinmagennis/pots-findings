# Correct counts, misleading examples: auto-picked "disagreements" on a health site

**Date:** 2026-10-27  **Context:** POTS Start page; five independent audit rounds before deploy

## The approach that worked
- An auditor who had not seen the builder recomputed every claim from the package parquets, then read the code.
- Every count was right in every round. Every round still found misleading framing, because the rule behind the number
  did not mean what the sentence said:
  - "disagreement" counted changes after treatment (heart rate 40 vs 16 became 40 vs 2 with only disease-state comparisons);
  - "vs disease state" also meant other patient groups and subgroups, not only healthy people;
  - a stricter "clear split" rule still picked different diseases, mouse studies and retold earlier work once the papers were read;
  - "barely studied" picks were artefacts of unmerged names or one case series retold by three papers.
- Fix that held: say plainly what the data can and cannot show ("no clear split among POTS vs healthy comparisons yet"),
  label automatic totals "possible splits", and show no automatic example where reading the papers breaks it.

## Judgment calls
- Chose honesty over a filled card: no disagreement example rather than a weak one.
- Kept the published Signals table and only relabelled it, so live numbers change once (2,315 instead of 3,934) for a stated reason.

## Reusable rule
Before an automatically picked example of a finding goes on a public health page, have someone who did not build it read the source papers behind that example; if they do not support the sentence, show the honest total and no example.
