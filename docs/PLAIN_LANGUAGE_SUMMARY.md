# What We Did, in Plain Language

**A plain-language guide to a machine-built index of POTS and dysautonomia research.**
Companion to `CORE_FINDINGS.md`, which has the technical detail and all the source links.

---

## First, the important warnings

**This is not medical advice.** What follows is a description of what research papers report. It is not
diagnosis, not treatment guidance, and not tailored to anyone's situation. Some sections mention specific
drugs and test results; none of that is a reason to start, stop, or change any treatment. Those decisions
belong to a clinician who knows your full history.

**The research is other people's work.** Everything indexed here was written by researchers who ran the
studies. A computer read their papers and organized what it found. That adds a searchable index; it adds
no new evidence. Every entry links back to the original paper, and if a finding matters to you, the paper
is the thing to read — the summary is just a signpost.

**This only covers POTS and dysautonomia.** Not ME/CFS. Not fibromyalgia. Not Ehlers-Danlos, MCAS, IBS,
migraine, or autism. Those literatures exist and are planned for later stages, but they have **not been
read yet**. If you came looking for how POTS compares to ME/CFS, this cannot tell you — not yet.

---

## What the project actually did

Medical research has a findability problem. There are thousands of papers on POTS and dysautonomia, each
reporting a handful of specific results, and no way to ask a question like "which markers have the most
independent studies behind them?" or "which treatments have failed in good-quality trials?" without a
person reading everything.

So we had a language model read the papers one at a time and fill in the same form for each result it
found: what was measured, whether it went up or down, in which condition, what kind of study it was, how
many participants, and — importantly — **a direct quote from the paper backing it up**. One paper
typically produces about a dozen of these entries.

Then we cleaned it up. The biggest problem was that papers write the same measurement dozens of different
ways. "HF power," "high-frequency HRV," "HF power (normalized units)" are all the same thing. Counting the
phrases instead of the concept made well-studied measurements look rare, so a second pass merged the
phrasings — 9,582 different phrases collapsed into 863 real concepts.

We also checked for the same paper appearing twice. Nine sets of papers had near-identical titles; we
examined all nine and merged eight of them (mostly a preprint and its later published version, which
should count as one study, plus a guideline printed in two journals at once and a couple of
corrections). **One we deliberately left alone**: two completely different research teams had published
papers with the identical generic title "Post-COVID-19 Postural Orthostatic Tachycardia Syndrome."
Merging those on title alone would have thrown away a real, independent second study. That check is worth
mentioning because it is the kind of thing an automated pipeline gets wrong when nobody validates it.

---

## What "36,459 findings from 3,121 papers" actually means

This number is easy to misread, so here is what it does and does not mean.

**It does mean:** the computer extracted 36,459 individual results from 3,121 separate research papers.
Every one has a quote from its source paper attached — 100% of them, with no exceptions. Every one links
to the paper, with the authors and journal named.

**It does not mean 36,459 discoveries.** A single paper produces many entries because it reports many
results. Ten papers all reporting that heart rate variability is lower in patients produce ten separate
entries about one repeatedly-observed thing. **When you want to know how well-supported something is,
count the papers, not the findings.**

**It does not mean all 3,121 papers are equally strong.** Most are observational studies — researchers
measured a group of patients and compared them to a control group. Only 877 findings come from randomized
controlled trials and 840 from meta-analyses, which are the study designs that support the strongest
conclusions. Roughly 226 papers contribute at least one meta-analysis-grade result. So the reliable core
is much smaller than the headline number, and the write-up says so throughout.

**It does not mean complete coverage.** 3,121 papers is about **22% of the ~14,263 papers** the full
project plans to read. And nearly half the extracted results (47.6%) describe symptoms or patient
experiences rather than a specific measurable substance, while others name something too rare to have
been matched to a standard concept. Only about 30% of entries end up in the marker-counting tables — those
tables are a useful slice of the corpus, not a picture of all of it.

---

## Four things that are genuinely interesting

### 1. A widely-used measurement had been badly undercounted

"HF power" is a way of measuring how much your nervous system's calming branch is influencing your heart
rhythm. Counting by exact phrase, it appeared in **9 papers** — which would make it a fringe measurement.
After merging the 25 different ways papers write it, it appears in **49 papers**. It was undercounted more
than fivefold. The same happened to related measures: SDNN went from 38 papers to 80, RMSSD from 33 to 70.

Why this matters: any automated index that skips this cleanup step will quietly tell you well-studied
things are obscure. That is a strong argument for doing the boring normalization work, and it is the
clearest proof in this project that the method needed it.

### 2. Some "disagreements" between studies may actually be different patient groups

The index found 532 places where studies contradict each other. That sounds like bad news for the field,
but 127 of them have a visible pattern in *who was studied*.

The most striking: studies finding that **midodrine** (a blood-pressure-raising drug) helped were mostly
studies of one POTS subtype, and studies finding it did not help were mostly of a different subtype. The
same split shows up for a proposed autoimmune marker. And several heart-rhythm measurements point in
opposite directions in children versus adults.

If that pattern holds up, those studies were never really contradicting each other — they were describing
different groups of patients who happen to share a diagnosis label. That is a real, testable idea about
POTS possibly being several different conditions, and it came out of counting rather than out of anyone's
hunch.

Two honest caveats. 61 of those 127 patterns turned out to be an artifact of our own pipeline — a
difference in whether we could read the whole paper or only its abstract, which is about our data access,
not about patients. And 376 of the 532 contradictions involve broad labels like "dysautonomia," which
lumps together genuinely different diseases; two studies of different diseases under one label will
disagree without either being wrong.

### 3. The record of what has *failed* is unusually complete here

Research publishing has a well-known bias: studies finding an effect get published more readily than
studies finding nothing. That means the picture patients and doctors see is skewed optimistic.

This index deliberately kept the negative results: **5,324 of them**, including **315 from randomized
trials and meta-analyses** — the study types where "we found nothing" is a genuinely strong statement.
Among the treatments with high-quality negative results recorded: intravenous immunoglobulin (a
placebo-controlled trial in POTS found no difference in symptom scores), pyridostigmine added to
beta-blockers, several vagus nerve stimulation devices tested against sham devices, and midodrine for
certain specific outcomes.

Read that carefully, because it is easy to misread: **this does not mean those treatments do not work.**
Each entry is one specific outcome, in one specific group of patients, in one trial. Midodrine also
appears with positive results across 86 papers in the same index. What the negative layer gives you is
the other half of the record — the half that is usually much harder to find. Whether any of it applies to
a particular person is a question only their clinician can answer.

### 4. The method rediscovered biology nobody told it about

This is the closest thing to a proof that the machinery works. The index looked for pairs of things that
show up in the same papers more often than chance. Buried in the results, it independently connected:

- **tafamidis** with **transthyretin** — tafamidis is a drug that stabilizes the transthyretin protein
- **hemin** with **HMBS** — hemin treats a disease caused by a fault in the HMBS gene
- **L-serine** with **SPTLC1** — L-serine is the treatment strategy for a nerve disease caused by
  SPTLC1 mutations

Nobody programmed those relationships in. The computer had no pharmacology knowledge; it noticed the
co-occurrences in the text. A method that can recover drug–target relationships it was never taught is a
method whose other connections are worth a look. A method that *couldn't* recover them would not be.

(Most of the strongest connections, it should be said, are boring: measurements that get printed in the
same table as each other. Those are reporting habits, not biology, and the write-up labels them as such.)

---

## What this cannot tell you

- **Whether anything here applies to you.** It cannot. It is a description of research papers, not of any
  individual, and it contains no diagnostic or treatment guidance.
- **Anything about ME/CFS, fibromyalgia, EDS, MCAS, IBS, migraine, or autism as their own subjects.**
  Those papers have not been read yet. When one of those conditions appears here, it is because a POTS
  researcher mentioned it in passing.
- **Whether shared mechanisms link these conditions.** This is the question the project exists to answer,
  and it needs the other literatures read first. A few markers look like they behave similarly across
  conditions, but that is currently based on POTS papers glancing sideways — a hypothesis, not a finding.
- **What causes anything.** Most entries (23,193 of 36,459) are explicitly labeled as correlation only.
  Two things moving together does not mean one caused the other.
- **Whether every entry is correct.** It is machine extraction and it has errors. Some concept names are
  flagged as uncertain (51 low-confidence, 240 medium). The thin, exciting-looking findings especially
  include noise and results from single labs that will not replicate.

The single biggest thing that would improve this: reading the next 7,243 papers, which cover ME/CFS,
MCAS, EDS, fibromyalgia, IBS, and small-fiber neuropathy. That is what would turn "here is a method that
works" into "here is what these conditions share."

---

## Why the source papers deserve the credit

Every entry in this index exists because a research group designed a study, recruited patients, collected
data, analyzed it, and published it — often on modest funding, in a field that has historically been
under-resourced and where patients have frequently been dismissed.

The computer read their papers. That is all it did. It did not discover that heart rate variability is
reduced in these patients; roughly 165 different research teams did, and this index counted them.

So: every finding carries its paper's authors, journal, and a working link, and quotes from papers are
kept short and always shown right next to the citation. If something here is useful to you, follow the
link, read the paper, and cite the researchers who did the work — not this index.

---

*Technical detail, full tables, and every source link: `CORE_FINDINGS.md`. Again, and it bears repeating:
this is machine-extracted research information, not medical advice. Talk to a qualified clinician about
your own health.*
