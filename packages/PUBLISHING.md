# Publishing checklist

Three destinations, three different shapes of the same content. Do them in this order, the
DOIs from step 1 are needed by steps 2 and 3.

## Order of operations

1. **Zenodo**: mint the DOIs (the citable archive of record)
2. **Backfill DOIs** into the five `CITATION.cff` files and five `.zenodo.json` files
3. **GitHub**: push this repo, then attach the tarballs as Release assets
4. **OSF**: optional, as a parent project with five components

---

## 1. Zenodo (do this first)

Upload the **`.tar.gz` files**, not folders. Archives are exactly what Zenodo expects, and the
DOI attaches to the file.

For each of the five packages:

1. New Upload -> drag `pots-findings-<pkg>-v1.2.tar.gz`
2. Zenodo does **not** read `.zenodo.json` from a manually uploaded archive (that file only drives
   Zenodo's GitHub-release integration). Paste the fields from the package's
   `deposit/ZENODO_FORM.md`: title, description, keywords, license (CC BY 4.0), version, ORCID,
   related identifiers
3. Under *Related identifiers*, the four sibling entries currently read
   the four sibling DOIs with relation `references` (a sibling package is related, not a part)

**The placeholder problem.** You cannot know the five DOIs before you deposit, and each package
references the other four. Two ways out:

- **Reserve DOIs first (cleaner).** Zenodo lets you reserve a DOI on a draft before publishing.
  Create all five drafts, reserve all five DOIs, backfill each one's four sibling references,
  then publish. Everything is correct at v1.
- **Publish then version.** Publish all five with placeholders, then upload a v2 of each with
  the real DOIs filled in. Zenodo versioning keeps a single concept DOI, so citations stay
  stable, but v1 ships with placeholder text in it.

Consider also a **Zenodo Community** for the five so they present as one collection.

## 2. DOIs

The five DOIs were reserved on Zenodo before this build and are filled in everywhere (a search for leftover DOI placeholders returns nothing):

| package | DOI |
|---|---|
| `dysautonomia-core-findings-v1.2` | https://doi.org/10.5281/zenodo.23671720 |
| `comorbid-conditions-findings-a-v1.2` | https://doi.org/10.5281/zenodo.23671722 |
| `comorbid-conditions-findings-b-v1.2` | https://doi.org/10.5281/zenodo.23671724 |
| `postviral-autism-findings-v1.2` | https://doi.org/10.5281/zenodo.23671726 |
| `migraine-hypermobility-findings-v1.2` | https://doi.org/10.5281/zenodo.23671728 |

They resolve once each Zenodo record is published (step 1).

Before pushing, from the repository root:

```bash
cd <pkg> && shasum -a 256 CITATION.cff .zenodo.json
# update those two lines in CHECKSUMS.sha256, or regenerate it wholesale:
find . -type f ! -name CHECKSUMS.sha256 ! -name MANIFEST.json \
  -exec shasum -a 256 {} \; | sed 's| \./| |' > CHECKSUMS.sha256
```

`MANIFEST.json` also carries per-file SHA-256 values and will need the same two updated.

## 3. GitHub

**Attach the five package tarballs as Release assets.** This is what makes single-tier download
work for people who do not use Git, it is not optional garnish. The repo README points at
`../../releases` for exactly this.

### Push the repo


```bash
cd build/pots-findings
# macOS: strip resource forks before the first commit, or they land in history
find . -name '._*' -delete; find . -name '.DS_Store' -delete
git init
git add .
git commit -m "Five self-contained literature-extraction packages, 148,186 findings"
git branch -M main
git remote add origin git@github.com:erinmagennis/pots-findings.git
git push -u origin main
```

The repo is 327 files / 114.1 MB across 5 folders. No file exceeds 18 MB, so **no Git LFS is needed**.
GitHub warns at 50 MB and blocks at 100 MB per file.

`.gitignore` deliberately excludes `*.tar.gz`. Tarballs are deposit products, not sources:
committing them would double the repo and store a fresh copy in history on every rebuild.

### Attach the tarballs as Release assets

Release assets live outside Git history, no repo bloat, 2 GB per file.

```bash
gh release create v1.2 \
  build/dysautonomia-core-findings-v1.2.tar.gz \
  build/comorbid-conditions-findings-a-v1.2.tar.gz \
  build/comorbid-conditions-findings-b-v1.2.tar.gz \
  build/postviral-autism-findings-v1.2.tar.gz \
  build/migraine-hypermobility-findings-v1.2.tar.gz \
  --title "v1.2, five self-contained packages" \
  --notes-file dysautonomia-core-findings/deposit/github_release_notes.md
```

Each package also carries its own `deposit/github_release_notes.md` if you prefer five
separate releases (tags `dysautonomia-core-findings-v1.2`, `comorbid-conditions-findings-a-v1.2`, …).

### Repository settings worth setting

- **Description:** `148,186 structured findings extracted from 11,519 papers on POTS, dysautonomia and comorbid conditions`
- **Topics:** `pots`, `dysautonomia`, `me-cfs`, `long-covid`, `ehlers-danlos`, `fibromyalgia`,
  `open-data`, `text-mining`, `biomarkers`
- **Issues: on.** This is your takedown channel, the LICENSE commits to honoring author and
  publisher requests, so there must be somewhere to file one.
- **Enable Zenodo's GitHub integration** only if you want releases auto-archived. If you already
  deposited manually in step 1, leave it off to avoid duplicate DOIs for the same content.

## 4. OSF (optional)

Structure as a parent project with five components: `deposit/osf_metadata.json` in each
package names the intended parent and siblings.

1. Create project *POTS/Dysautonomia Cross-Condition Literature Findings*
2. Add five components, one per package, titled as in each `osf_metadata.json`
3. Upload each `.tar.gz` to its component
4. Paste each package's `docs/README.md` into that component's wiki home
5. Link the Zenodo DOIs from step 1 under each component's *Identifiers*

OSF can also link the GitHub repo directly, which keeps the two in sync without a second upload.

---

## Before you publish anything

- [ ] `python code/verify_package.py --self-test` passes in all five folders
- [ ] `shasum -a 256 -c CHECKSUMS.sha256` clean in all five
- [ ] Author name and ORCID correct in all five `CITATION.cff`
- [ ] No DOI placeholder left anywhere: search the tree for the builder's uppercase placeholder token (used before DOIs are known); it must return nothing. This line deliberately does not spell the token.
- [ ] No macOS junk: `find . -name '._*' -o -name '.DS_Store'` returns nothing. These are
      gitignored now, but a tree copied via macOS `tar` or a USB drive regrows them, and
      `tar -czf` on macOS emits them unless `COPYFILE_DISABLE=1` is set
- [ ] No `__pycache__` or `.pyc` in any package (`find . -name '__pycache__'`): running the
      verifier creates these; they are gitignored and excluded from the archives, but a
      hand-built tarball can pick them up and then the file count will not match MANIFEST.json
- [ ] You are content that the LICENSE excerpt policy is one you want to stand behind

That last item is a judgment call, not a checkbox. The `provenance_quote` column ships full
verbatim excerpts, median 180 characters, 98.2% under 400, longest 1,065, because a finding
without its source span cannot be checked by anyone. The LICENSE explains the reasoning and
commits to honoring takedown requests. **Whether this constitutes fair use or falls under a
quotation or text-and-data-mining exception is a legal question**, and one worth putting to your
institution's library or scholarly-communications office before a public deposit. I am not a
lawyer and cannot make that determination.
