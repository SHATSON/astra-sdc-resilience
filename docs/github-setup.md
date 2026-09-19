# Publishing this repository on GitHub

The repository is ready to push; it has no remote configured and no commits yet.

## 1. Replace the placeholders

```bash
grep -rn "SHATSON" .        # README.md, CITATION.cff
```

Replace them with your account or organization name, and fill in the author
fields in `CITATION.cff`, `LICENSE`, and the title page of the manuscript.

## 2. Create the repository and push

Using the GitHub CLI:

```bash
git init -b main
git add .
git commit -m "ASTRA v0.1.0: reference implementation, figures, evaluation protocol"
gh repo create astra-sdc-resilience --public --source=. --remote=origin --push
```

Or with the web UI: create an empty repository named `astra-sdc-resilience`
(no README, no license, since both exist here), then:

```bash
git init -b main
git add .
git commit -m "ASTRA v0.1.0: reference implementation, figures, evaluation protocol"
git remote add origin https://github.com/SHATSON/astra-sdc-resilience.git
git push -u origin main
```

## 3. Tag the release cited by the paper

```bash
git tag -a v0.1.0 -m "Artifact accompanying the ASTRA paper"
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes-file docs/release-notes-v0.1.0.md
```

## 4. Mint an archival DOI

Connect the repository to Zenodo (Zenodo → GitHub → enable the repository),
then publish the release. Zenodo archives the tag and issues a DOI. Add that
DOI to `CITATION.cff` and to the artifact-availability statement in the paper.

## 5. Check the automation

The workflow in `.github/workflows/tests.yml` runs the test suite and
regenerates the computed figures on Python 3.10 and 3.12. Confirm it is green
before announcing the release, and update the badge URL in `README.md`.
