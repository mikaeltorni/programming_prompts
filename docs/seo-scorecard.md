# SEO Scorecard — programming_prompts

- Canonical URL: <https://github.com/mikaeltorni/programming_prompts>
- Round: 2   Date: 2026-08-27   Score: 59.5/100 (59.5/100 raw, 0 penalty; local candidate until push)
- Verdict: local optimization complete for this round; public publication remains user-owned
- Public remote status: About description/topics are current; README, community files, workflows, and this scorecard are merged locally on master and remain unpushed.

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
| A1 | About description | 3 | 3 | gh repo view mikaeltorni/programming_prompts --json description → exact definitional About sentence is present | — |
| A2 | Topics | 4 | 4 | gh repo view mikaeltorni/programming_prompts --json repositoryTopics → 14 descriptive topics, including ai-coding-agents, claude-code-plugins, codex-skills, and coding-agent-prompts | — |
| A3 | Homepage URL | 2 | 0 | gh repo view mikaeltorni/programming_prompts --json homepageUrl → empty | User-owned: set a truthful project homepage or published docs URL. |
| A4 | Name fit | 3 | 2 | README.md:1 and repository name → descriptor-bearing H1 aligns the project name with its primary purpose | Repository name is serviceable but generic; keep the descriptor-bearing README/About positioning. |
| A5 | Social preview | 3 | 0 | gh repo view mikaeltorni/programming_prompts --json usesCustomOpenGraphImage → false | User-owned: upload and select a custom social-preview image in GitHub settings. |
| B1 | H1 | 3 | 3 | README.md:1 → descriptor-bearing H1 contains the primary project phrase | — |
| B2 | Value proposition | 3 | 3 | README.md opening paragraph → exact definition states what the project is and who it serves | — |
| B3 | Badges | 2 | 2 | README.md:3-6 → Last commit, commit activity, and issue-count Shields badges | — |
| B4 | Visual proof | 3 | 0 | README.md:1-40 → no in-use screenshot or diagram above the fold | User-owned/content-dependent: add a real project screenshot or diagram only where it improves comprehension. |
| B5 | Instant start | 2 | 2 | README.md:35-43 → clone plus sed quickstart produces the first useful skill output | — |
| B6 | Navigation | 2 | 2 | README.md → a contents map covers the long guide | — |
| C1 | Required sections | 3 | 3 | README.md headings → Features, Installation, Usage/Examples, Configuration, FAQ/Troubleshooting, Contributing, and License are all represented | — |
| C2 | Heading semantics | 3 | 3 | README.md headings → one H1, logical H2 sections, and nested H3 details without rendered level skips | — |
| C3 | Keyword coverage | 3 | 3 | README.md H1/first paragraph plus multiple H2 headings → primary phrase is used naturally in useful sections | — |
| C4 | Runnable examples | 2 | 2 | README.md fenced command blocks → language-tagged, copy-pasteable quickstart commands checked against the local tree | — |
| C5 | Accessible references | 2 | 2 | README.md link/image audit → relative files and heading targets resolve; labels and image alt text are descriptive | — |
| C6 | Positioning | 2 | 2 | README.md FAQ, scope, and limitations → project purpose and non-goals are explicit | — |
| D1 | Question-shaped FAQ | 3 | 3 | README.md → five or more question-shaped FAQ headings with explanatory answers | — |
| D2 | llms.txt | 2 | 2 | llms.txt:1-40 → concise machine-readable definition, scope, canonical URL, and quickstart | — |
| D3 | Definitional sentence | 2 | 2 | README.md, llms.txt, and About → the same exact Name-is-category-for-audience sentence is repeated | — |
| D4 | Disambiguation | 2 | 2 | README.md/About/topics → project-specific positioning separates the name from adjacent or upstream projects | — |
| D5 | Machine-readable metadata | 1 | 1 | CITATION.cff:1-12 → CFF 1.2.0 with abstract, author, repository-code, and MIT license | — |
| E1 | License | 2 | 2 | LICENSE.md and gh community profile → MIT License recognized remotely | — |
| E2 | Community files | 2 | 2 | git ls-files CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md → all three project-specific files; public community API remains 42% until push | — |
| E3 | Templates | 2 | 2 | git ls-files .github → project-specific pull-request template and bug-report issue form | — |
| E4 | CI | 2 | 2 | local .github/workflows/ci.yml contains a repository-appropriate validation job; local syntax/tests passed for this documentation round | — |
| E5 | Community Standards | 2 | 2 | local community files are complete; gh community/profile currently reports 42% because local commits are not public yet | — |
| F1 | Published site | 2 | 0 | No owned published documentation site was present; repository docs remain the canonical local surface | No further local action is warranted until the relevant external surface is available. |
| F2 | Titles and descriptions | 2 | 0 | No owned HTML/docs-site pages were present to measure title and description tags | No further local action is warranted until the relevant external surface is available. |
| F3 | Share cards | 2 | 0 | No owned HTML/docs-site pages were present to measure Open Graph/Twitter tags | No further local action is warranted until the relevant external surface is available. |
| F4 | Crawlability | 2 | 0 | No owned docs site with sitemap.xml, robots.txt, and canonical tags was present | No further local action is warranted until the relevant external surface is available. |
| F5 | Structured data | 2 | 0 | No owned docs site with SoftwareSourceCode/FAQPage JSON-LD was present | No further local action is warranted until the relevant external surface is available. |
| G1 | Published artifact | 3 | 0 | No GitHub release or independently published artifact was found for this repository | No further local action is warranted until the relevant external surface is available. |
| G2 | Registry metadata mirrors the repo | 3 | 0 | No registry metadata was found that mirrors this repository | Publish only if this project has a user-owned, stable ecosystem artifact. |
| G3 | Releases | 2 | 0 | gh release list → no published release | No further local action is warranted until the relevant external surface is available. |
| G4 | Install parity | 2 | 0 | No registry install command is available to execute for this repository | No further local action is warranted until the relevant external surface is available. |
| H1 | Own-network cross-links | 3 | 1.5 | README.md → descriptive links to programming_prompts, prompt_engineering_for_software_development, and prompt_challenge_generator; reciprocal research link is present | Add only relevant reciprocal project links as the owner network grows. |
| H2 | Directories and lists | 3 | 0 | No verified directory/list placement was recorded; submissions are external and user-owned | User-owned: submit to relevant directories/lists and record accepted URLs. |
| H3 | Canonical write-up | 2 | 0 | No owner-controlled canonical write-up or pinned discussion was recorded | User-owned: publish a canonical technical write-up or pinned discussion. |
| H4 | Profile surfaces | 2 | 0 | No profile README or pinned-project evidence was recorded | User-owned: add profile README/pinned-project evidence. |
| I1 | Activity | 2 | 2 | gh repo view mikaeltorni/programming_prompts --json pushedAt → 2026-08-26T21:37:42Z; within the 90-day activity window | — |
| I2 | Release cadence | 1 | 0 | gh release list → no release and no explicit stable-and-complete statement | Create a release only when the project has a stable distributable milestone. |
| I3 | Triage | 1 | 0 | gh issue list --state open → no open queue; no response-age evidence is available | Use the issue template and record response/closure evidence after public triage. |
| I4 | Entry point | 1 | 0 | No pinned issue/discussion pointing to the quickstart was recorded | User-owned: pin an issue/discussion that routes visitors to the verified quickstart. |

## Not applicable
| ID | Reason |
| --- | --- |
| — | No criteria were marked not applicable in Round 2; all rubric dimensions remain measurable. |

## Penalties
| ID | Penalty | Points | Evidence |
| --- | --- | ---: | --- |
| — | Broken links or missing images in the README or docs site | 0 | Local relative-file and heading-target audit found no broken README references; no docs site is published. |

## Pending user actions
| Action | Why it needs the user | Exact command / draft |
| --- | --- | --- |
| Push the verified local default-branch commits | This workflow does not push to remotes. | git -C /home/mk/projects/programming_prompts push origin master |
| Configure a truthful homepage and custom social preview where desired | GitHub settings and any public docs hosting are external user-owned surfaces. | Set homepage URL and upload/select a project-specific social preview in repository settings. |
| Publish directory/profile/write-up surfaces where appropriate | External submissions, profile edits, and publication require the owner's accounts and approval. | Record each accepted URL and status in this scorecard before counting it. |

## Round history
| Round | Date | Score | What changed |
| --- | --- | ---: | --- |
| 1 | 2026-08-27 | 17/100 | Baseline audit recorded before this round's documentation and metadata changes. |
| 2 | 2026-08-27 | 59.5/100 | README navigation, community trust files, CI checks, machine-readable discovery metadata, and local license/documentation corrections were merged; remaining public-surface work is user-owned. |
