# SEO Scorecard — programming_prompts

- Canonical URL: <https://github.com/mikaeltorni/programming_prompts>
- Round: 1   Date: 2026-08-27   Score: 17/100 (19/100 raw, -2 penalty)
- Verdict: in progress

## Keyword model
| Role | Terms | Why |
| --- | --- | --- |
| Primary | AI coding-agent prompts | Narrow query matching the repository's user-facing purpose. |
| Secondary | Codex skills; Claude Code plugins; reusable coding prompts; prompt engineering; developer workflow | Adjacent searches supported by the current project surface. |
| Long-tail | reusable prompts for coding agents; installable Codex skills; Claude Code plugin prompts; secure project setup prompts; conventional commit workflow prompt; test-driven refactoring prompt | Specific problem phrasings the documentation can answer truthfully. |
| Confusable with | generic programming prompts; unrelated prompt libraries; Claude Code marketplace catalogs | Names and adjacent projects that require clear positioning. |

## Criteria
| ID | Criterion | Max | Score | Evidence | Gap / next action |
| --- | --- | ---: | ---: | --- | --- |
| A1 | About description | 3 | 3 | gh repo view mikaeltorni/programming_prompts --json description → "Reusable AI coding-agent prompts, plugins, and skills for Codex and Claude Code — guidelines, commit workflow, refactoring, secure project init." | — |
| A2 | Topics | 4 | 2 | gh repo view mikaeltorni/programming_prompts --json repositoryTopics → topics recorded in the remote audit | Add or verify this artifact in the next improvement round. |
| A3 | Homepage URL | 2 | 0 | gh repo view mikaeltorni/programming_prompts --json homepageUrl → "" | Add or verify this artifact in the next improvement round. |
| A4 | Name fit | 3 | 2 | README.md:1 and repository name "programming_prompts" | Add or verify this artifact in the next improvement round. |
| A5 | Social preview | 3 | 0 | gh repo view mikaeltorni/programming_prompts --json usesCustomOpenGraphImage → false; only GitHub's generated preview URL is configured | Add or verify this artifact in the next improvement round. |
| B1 | H1 | 3 | 1.5 | README.md:1 → current rendered H1 | Add or verify this artifact in the next improvement round. |
| B2 | Value proposition | 3 | 1.5 | README.md:3-10 → opening prose | Add or verify this artifact in the next improvement round. |
| B3 | Badges | 2 | 0 | rg -n 'badge|shields.io|img.shields.io' README.md → no informational badge row | Add or verify this artifact in the next improvement round. |
| B4 | Visual proof | 3 | 0 | README.md:1-40 → no in-use screenshot or diagram above the fold | Add or verify this artifact in the next improvement round. |
| B5 | Instant start | 2 | 0 | README.md:1-40 → no copy-pasteable install plus first-result example above the fold | Add or verify this artifact in the next improvement round. |
| B6 | Navigation | 2 | 0 | README.md:1-221 → navigation assessed against README length | Add or verify this artifact in the next improvement round. |
| C1 | Required sections | 3 | 0 | README.md headings and body → required-section coverage measured from the current document | Add or verify this artifact in the next improvement round. |
| C2 | Heading semantics | 3 | 1 | README.md headings → current heading levels and wording | Add or verify this artifact in the next improvement round. |
| C3 | Keyword coverage | 3 | 1 | README.md:1-40 plus keyword occurrences → current keyword coverage | Add or verify this artifact in the next improvement round. |
| C4 | Runnable examples | 2 | 1 | README.md fenced command blocks → language tags and clean-install parity checked | Add or verify this artifact in the next improvement round. |
| C5 | Accessible references | 2 | 0 | README.md link/image scan → descriptive references and target status checked | Add or verify this artifact in the next improvement round. |
| C6 | Positioning | 2 | 2 | README.md:12-16,66-76 → plugin/direct-skill ownership and installation positioning | — |
| D1 | Question-shaped FAQ | 3 | 0 | README.md → no five-question FAQ heading set in the current document | Add or verify this artifact in the next improvement round. |
| D2 | llms.txt | 2 | 0 | git ls-files llms.txt → no root llms.txt | Add or verify this artifact in the next improvement round. |
| D3 | Definitional sentence | 2 | 0 | README.md opening prose → no exact Name-is-category-for-audience sentence | Add or verify this artifact in the next improvement round. |
| D4 | Disambiguation | 2 | 0 | Keyword model → collision/disambiguation requirement assessed against README/About/topics | Add or verify this artifact in the next improvement round. |
| D5 | Machine-readable metadata | 1 | 0 | git ls-files package manifests/CITATION.cff → machine-readable description coverage checked | Add or verify this artifact in the next improvement round. |
| E1 | License | 2 | 2 | LICENSE or LICENSE.md and gh community/profile → license recognition checked | — |
| E2 | Community files | 2 | 0 | git ls-files CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md → missing project-specific community files | Add or verify this artifact in the next improvement round. |
| E3 | Templates | 2 | 0 | git ls-files .github → issue/PR templates absent | Add or verify this artifact in the next improvement round. |
| E4 | CI | 2 | 0 | git ls-files .github/workflows → real test CI absent | Add or verify this artifact in the next improvement round. |
| E5 | Community Standards | 2 | 0 | gh api repos/mikaeltorni/programming_prompts/community/profile → health checklist measured at 42% or unavailable | Add or verify this artifact in the next improvement round. |
| F1 | Published site | 2 | 0 | git ls-files docs mkdocs.yml .github/workflows → no owned published docs site | Add or verify this artifact in the next improvement round. |
| F2 | Titles and descriptions | 2 | 0 | No owned HTML/docs-site pages were present to measure title and description tags | Add or verify this artifact in the next improvement round. |
| F3 | Share cards | 2 | 0 | No owned HTML/docs-site pages were present to measure Open Graph/Twitter tags | Add or verify this artifact in the next improvement round. |
| F4 | Crawlability | 2 | 0 | No owned docs site with sitemap.xml, robots.txt, and canonical tags was present | Add or verify this artifact in the next improvement round. |
| F5 | Structured data | 2 | 0 | No owned docs site with SoftwareSourceCode/FAQPage JSON-LD was present | Add or verify this artifact in the next improvement round. |
| G1 | Published artifact | 3 | 0 | gh release list --repo mikaeltorni/programming_prompts → no published release artifact | Add or verify this artifact in the next improvement round. |
| G2 | Registry metadata mirrors the repo | 3 | 0 | No ecosystem registry metadata was found in the current repository/remote audit | Add or verify this artifact in the next improvement round. |
| G3 | Releases | 2 | 0 | gh release list and git tag --sort=-creatordate → no published release | Add or verify this artifact in the next improvement round. |
| G4 | Install parity | 2 | 0 | No registry install command was available to execute against a published artifact | Add or verify this artifact in the next improvement round. |
| H1 | Own-network cross-links | 3 | 0 | Owner-network cross-link scan of README files → reciprocal descriptive links not established | Add or verify this artifact in the next improvement round. |
| H2 | Directories and lists | 3 | 0 | No verified awesome-list/registry directory listing was recorded this round | Add or verify this artifact in the next improvement round. |
| H3 | Canonical write-up | 2 | 0 | No owner-controlled canonical write-up or pinned discussion was recorded | Add or verify this artifact in the next improvement round. |
| H4 | Profile surfaces | 2 | 0 | No profile README/pinned-project evidence was recorded | Add or verify this artifact in the next improvement round. |
| I1 | Activity | 2 | 2 | gh repo view ... --json pushedAt → 2026-08-26T21:37:42Z | — |
| I2 | Release cadence | 1 | 0 | gh release list → no release; README has no explicit stable-and-complete statement | Add or verify this artifact in the next improvement round. |
| I3 | Triage | 1 | 0 | gh issue/pr list → no response-age evidence recorded in this baseline | Add or verify this artifact in the next improvement round. |
| I4 | Entry point | 1 | 0 | No pinned issue/discussion pointing to the quickstart was recorded | Add or verify this artifact in the next improvement round. |

## Not applicable
| ID | Reason |
| --- | --- |
| — | No criteria were marked not applicable in this baseline; all rubric dimensions remain actionable or measurable. |

## Penalties
| ID | Penalty | Points | Evidence |
| --- | --- | ---: | --- |
| P6 | Broken links or missing images in the README or docs site | -2 | README link scan returned 404 for the installation_scripts dependency-map URL and the linux_codex_claude_code_setup repository URL. |

## Pending user actions
| Action | Why it needs the user | Exact command / draft |
| --- | --- | --- |
| Publish the verified default-branch commits | This workflow does not push to remotes. | `git push origin master` |
| Configure a public docs homepage/social preview or profile surface where desired | GitHub account/profile and publishing settings are external user-owned surfaces. | Review the proposed URL/assets after the local docs site source is ready. |

## Round history
| Round | Date | Score | What changed |
| --- | --- | ---: | --- |
| 1 | 2026-08-27 | 17/100 | Baseline audit recorded before this round's documentation and metadata changes. |

