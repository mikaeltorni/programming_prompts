---
name: testing
description: >-
  v0.1.62 — Save and run each capability's public checks before its code,
  finishing that cycle before starting the next behavior sentence.
---

# Finish one capability's checks and code before the next

Read the entire request and repository guidance. Each behavior sentence is one
capability, including each “It should also” sentence and each revision of earlier
behavior. Keep all commands and semicolon/“and” clauses within one sentence
together. Artifact/signature
setup is not a capability; one small module is not one capability when the
request has several behavior sentences.

Identify and quote the current behavior sentence in your progress update before
saving its checks. With commits/workflow selected, use their existing queue;
testing alone adds no plan file or Git commits. Work only on the first unfinished
sentence:

1. Save its public success and rejection checks, then run the cumulative suite
   against the previous implementation. Record the actual baseline.
2. Implement only this sentence. Run the same saved checks plus earlier
   regressions; repair failures and rerun until they pass.
3. Review the saved files and finish selected commit/delivery. Only then quote
   the next sentence and save its checks.

Valid order is checks A → baseline A → code A → pass A → checks B → baseline B →
code B → pass B. Do not save all sentences' checks before writing the program.
Later commands remain rejected, including in seeds and observer queries, until
their own cycle. Do not scaffold working future selectors.

## Save complete public checks

Use existing project tooling; stdlib assertions or unittest suffice for a new
project. Apply selected function contracts to tests, fixtures and helpers from
the first saved draft. Derive expectations independently from the request,
original logs and preceding successful calls, never unchecked program output.

For each current command/query, save meaningful success cases and the applicable
rejections together, before its baseline:

- Blank input and unknown selectors. A valid free-form data operand is not an
  unknown selector, even when other forms have named commands.
- Missing and extra operands for each documented form. Zero-operand forms need
  only extra rejection; preserve requested optional operands and multiword text.
  For command-string APIs, count operands inside the string; do not invent
  unsupported function-call signatures. Result placeholders are outputs, not
  extra input operands.
- Invalid numeric text for every numeric operand, separately from domain and
  resource failures. Retain it when numeric acceptance widens.
- Requested domain boundaries at the strict excluded endpoint and beyond it,
  and requested missing/duplicate/insufficient resources with otherwise valid
  operands. Do not invent types, numeric limits, aliases or error wording.

One representative may cover an actually shared rule; separate numeric operands
and different rejection reasons still need applicable cases. Check all current
loops and helpers for omissions; no coverage inventory file is required.

Keep earlier assertions except rules the current sentence explicitly replaces.
Retire every superseded expectation, including old rejection loops, during that
sentence's cycle. Earlier whole-number rejections and truncated results remain
correct until the sentence widening inputs or precision. Test names do not freeze
a revision, and later results must not be pulled forward.

## Observe rejection without changing the fixture

Decide whether the interface is mutable. Stateless interfaces need neither seeds
nor state reads. For mutable checks, use a shared reject-and-observe helper: it
asserts the required exception, then immediately asserts independently expected
public values and required history. Pass the relevant read commands and expected
results for that fixture. Route malformed, domain and resource rejections through
it; catching an exception alone is incomplete when a public read exists.

When a current public mutation can establish meaningful state, seed through it
before rejection, except the required-empty cases below. A seed before a
rejection loop can serve every iteration, but each iteration must assert its
reads before another rejection, mutation, reset or reload. A mutation after rejection is not its seed. Public creation at zero can
be meaningful if a read detects resource loss.

Use the strongest currently available public view. History alone, private
equality and a mutation's returned count/value do not replace an available value
read. When only an aggregate is available, assert it and disclose its limits.
When no public read exists yet, use a weaker probe through an existing public
operation and state its limit; do not invent a getter or use a later command.

When this sentence introduces a read query, save its own checks **and upgrade
every earlier rejection body/helper** before its application edit. Add the new
query's expected assertions immediately after each retained rejection, seeding
meaningful state where missing. Include creation, duplicates and malformed input
in old files. A separate newer test does not upgrade them. The cumulative baseline
may now fail on the missing query; this is the query's current cycle, not early
implementation. Unasserted reads observe nothing.

Default empty/zero state does not make malformed input a required-empty case;
malformed requests still need public seeding when possible. Keep actual required
empty-state rejection cases empty. An asserted valid empty query
already observes emptiness; a required empty-state mutation rejection asserts
available reads of that empty state. This exception does not cover malformed
inputs. Private resets/reloads may isolate independent fixtures but cannot
replace applicable public seeds or enable later behavior through test-only flags.

## Verify before moving on

A correct-path missing-module/file baseline is valid for creation; do not change
its valid import path to hide that failure. Existing passing checks can protect
a refactor. Separate dependency/infrastructure errors from missing behavior.

Independent mutable cases start fresh, while required multi-call sequences retain
state. Verify isolation with a repeat in the same process or another order. Mock
unnecessary external effects and use temporary install/config targets.

After the last edit, run the saved cumulative suite directly with full output
and exit status visible. Check directory, discovery, imports and environment:
nonzero behavioral assertions must actually execute. Uncalled definitions and
zero-test runs prove nothing. Put new unittest methods inside their collected
class before its runner. A failed run is unfinished: repair the responsible
source or an independently incorrect expectation and rerun the same suite before
moving on or claiming success. Report actual commands, results and concrete limits.

Honor project test prohibitions and static/low-impact direct-check exceptions;
record their actual check instead of claiming a saved test. Do not install a
framework or hosted CI without a request.
