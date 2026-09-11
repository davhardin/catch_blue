# Question Bank Tracker

Last updated: 2026-09-11 (Anson Vol. 2 import IN PROGRESS — blood, heart,
blood_vessels, lymphatic_and_immune_system, and respiratory_system vetted and
imported, 811 questions; digestive_system onward still awaiting David's
vetting pass.
Vol. 1 import complete since 2026-09-01; zero placeholder questions).

What this file tracks: which subtopics exist per topic, which sources have
been reviewed for which topics, and which sources are still untouched — so
nothing falls through the cracks between machines. This file lives at the
repo root **on purpose**: `question_sources/` is gitignored, so the audit and
vetting files there (`question_recommendations.md`, `Anson Vol.1 Final
Questions.md`, `Anson Vol.1 - unreviewed.md`, and the Vol. 2 set:
`question_recommendations_part2.md`, `Anson Vol.2 Final Questions.md`,
`anson_import2.py`) do **not** sync via git — this tracker does.

## Sources

| Source | License | Status |
|---|---|---|
| Anson *3600+ Review Questions*, Vol. 1 (5th ed.) | CC BY-SA 3.0 | **Import complete.** All 1,870 questions audited (2026-08-31) → David vetted all 14 topics → 1,595 imported 2026-09-01. Remaining: the 177-question edit pile in `Anson Vol.1 - unreviewed.md` (David's rewrites). |
| Anson *3600+ Review Questions*, Vol. 2 (3rd ed.) | CC BY-SA 3.0 | **Import in progress.** All 1,884 questions audited (2026-09-08) → `question_recommendations_part2.md` (1,594 REC / 273 EDIT / 17 NO). David has vetted 5 of 11 topics (blood → respiratory_system) in `Anson Vol.2 Final Questions.md` → 811 imported (656 on 2026-09-09, +155 respiratory_system on 2026-09-11) via `anson_import2.py`. **Still to vet:** digestive_system, metabolism, urinary_system, fluids_and_acid-bases, reproductive_system, development_and_inheritance (the audit is done for all of them). Edit pile for the 5 imported topics: 110 entries (see loose ends). |
| OpenStax *A&P 2e* review questions (ch. 1–4+) | CC BY-NC-SA 4.0 | **Not started.** Maps section-for-section onto existing subtopics. Educator account (free instructor test bank) not yet applied for. |
| OpenStax *A&P 2e* critical-thinking questions | CC BY-NC-SA 4.0 | **Not started.** Raw material for the difficulty-3 tier; needs MCQ-ification. |
| OER Commons question banks (OpenStax-aligned) | varies per item | **Not started.** Needs a free account; check each item's license. |
| VTCSOM *Human Anatomy Self-Assessment* | CC BY 4.0 | **Not started.** Med-school level — difficulty-3 well for skeletal/muscular/nervous. |
| Kenhub, GetBodySmart, freeanatomyquiz.com, Martini 12e | copyrighted | Inspiration/coverage-checklists only — never transcribe. |

## Topic status

Subtopic layout = the post-vetting plan from `Anson Vol.1 Final Questions.md`
(topics 01–14) and `Anson Vol.2 Final Questions.md` (topics 15+).
"Anson vetted" = David's manual pass over the audit recommendations.
All imported questions are `difficulty: 1` for now — no difficulty grading yet.
Seven questions carry `"shuffle": false` (two-choice items): `bio-anat-06-229`,
`bio-anat-14-067`, and from Vol. 2 `bio-anat-16-003`, `-004`, `-005`, `-010`,
`-068` (heart — systole/diastole pairs and one "overlap is greater/less").

Id prefixes continue the Vol. 1 numbering in topic-plan order: 15 blood,
16 heart, 17 blood_vessels, 18 lymphatic_and_immune_system, 19
respiratory_system. The next Vol. 2 topics should take 20 digestive_system, 21 metabolism,
22 urinary_system, 23 fluids_and_acid-bases, 24 reproductive_system,
25 development_and_inheritance.

| Topic | Qs | Subtopics (imported count) | Anson vetted |
|---|---|---|---|
| anatomical_language | 136 | Anatomical Directions (26), Anatomy vs Physiology (8), Body Cavities (14), Body Regions (49), Homeostasis (13), Levels of Organization (26) | ✅ |
| chemical_foundations | 66 | Atoms, Elements, and Compounds (15), Chemical Bonds (4), Chemical Reactions (11), Macromolecules (27), pH and Body Fluids (9) | ✅ |
| cells | 75 | Cellular Transport (12), DNA, Transcription and Translation (13), Cell Membrane (11), Organelles (28), The Cell Cycle (11) | ✅ |
| tissues | 76 | Aging: Tissues (2), Connective Tissue (38), Epithelial Tissue (28), Muscle and Nervous Tissue (8) | ✅ |
| integumentary_system | 71 | Aging: Integumentary System (2), Dermis and Hypodermis (8), Epidermis (21), Hair and Nails (14), Integumentary Damage / Repair (14), Sweat Glands (12) | ✅ |
| skeletal_system | 335 | Aging: Skeletal System (5), Appendicular Skeleton (82), Axial Skeleton (104), Bone Cell Types (6), Bone Classification (27), Bone Development and Growth (17), Bone Fractures (7), Joints (87) | ✅ |
| muscular_system | 234 | Appendicular Muscles (56), Axial Muscles (49), Cardiac and Smooth Muscle (18), Neuromuscular Junction, EC Coupling, and Cross-Bridge Cycling (19), Muscle Energy & Recovery (23), Muscle Functions (30), Skeletal Muscle Structure (39) | ✅ |
| nervous_system *(was nervous_tissue)* | 112 | Action Potential (26), Divisions of the Nervous System (14), Membrane Potential (12), Neural Cells (28), Synaptic Transmission (32) | ✅ |
| spinal_cord | 67 | Spinal Cord Structure (23), Spinal Nerves (36), Spinal Reflexes (8) | ✅ |
| brain | 111 | Brain Protection (11), Brain Stem (18), Brain Development (7), Cerebellum (4), Cerebral Cortex (50), Cerebrospinal Fluid (7), Diencephalon (9), Limbic System (5) | ✅ |
| sensory_pathways_and_somatic_nervous_system | 39 | Afferent Division (13), Efferent Division (8), Sensory Receptors (18) | ✅ |
| autonomic_nervous_system | 53 | Aging: ANS (2), Autonomic Nervous System (18), Divisions of the Autonomic Nervous System (33) | ✅ |
| special_senses | 131 | Equilibrium and Hearing (45), Eye Structures (31), Gustation and Olfaction (14), Visual System (41) | ✅ |
| endocrine_system | 88 | Adrenal Glands (15), Cell Signaling (11), Disease: Diabetes Mellitus (5), Endocrine Regulation (21), Pancreas (13), Parathyroid Glands (3), Secondary Endocrine Organs (7), Thyroid Gland (13) | ✅ |
| blood | 106 | Blood Composition (23), Blood Types (4), Hemostasis (32), Red Blood Cells (24), White Blood Cells (23) | ✅ Vol. 2 |
| heart | 172 | Cardiac Cycle (20), Cardiac Electrophysiology (37), Cardiac Output (42), Heart Anatomy (73) | ✅ Vol. 2 |
| blood_vessels | 208 | Aging: Cardiovascular System (1), Arteries and Veins (53), Blood Pressure & Resistance (42), Fetal Cardiovascular System (6), Pulmonary & Systemic Circuits (67), Regulating Blood Flow (39) | ✅ Vol. 2 |
| lymphatic_and_immune_system | 170 | Adaptive Immunity (75), Aging: Immune System (2), Immune Disorders (8), Innate Immunity (21), Innate vs Adaptive Immunity (2), Lymphatic System Anatomy (62) | ✅ Vol. 2 |
| respiratory_system | 155 | Aging: Respiratory System (2), Gas Exchange (16), Gas Transport (21), Lower Respiratory System (26), Regulation of Breathing (31), The Lungs (47), Upper Respiratory System (12) | ✅ Vol. 2 |
| digestive_system | 0 | *(plan: 9 subtopics)* | ⏳ audited, not vetted |
| metabolism | 0 | *(plan: 7 subtopics)* | ⏳ audited, not vetted |
| urinary_system | 0 | *(plan: 5 subtopics)* | ⏳ audited, not vetted |
| fluids_and_acid-bases | 0 | *(plan: 6 subtopics)* | ⏳ audited, not vetted |
| reproductive_system | 0 | *(plan: 6 subtopics)* | ⏳ audited, not vetted |
| development_and_inheritance | 0 | *(plan: 6 subtopics)* | ⏳ audited, not vetted |

**Bank total as of 2026-09-09: 2,231 questions** (1,575 Vol. 1 after
removals + 656 Vol. 2).

**Removed during playtesting:** questions pulled from the bank after they
bit in play live in `data/questions/removed_questions.md`, verbatim, with
their ids — so a rewrite can restore one under the same id. That file is
committed and is the single list; the M6.e playtest log in
`milestones/m6.md` records *why* each was pulled. As of 2026-09-07 it holds
`bio-anat-14-084` (Thyroid Gland — the "unlike the other two, calcitonin"
prompt), which is why endocrine_system reads 88 above.

**Thin subtopics — come back later** *(accepted as-is 2026-09-01)*: three
Aging subtopics sit at 2 questions, below the M5 ≥3 baseline, by decision:
`Aging: Tissues` (6 rewrite candidates waiting in the edit pile),
`Aging: Integumentary System` (1 candidate in the pile), and `Aging: ANS`
(Anson is exhausted — needs an original question or a merge). Top them up
when working the edit pile or importing the next source. Vol. 2 adds three
more thin ones *(accepted 2026-09-09, same reasoning)*: `Aging:
Cardiovascular System` (1 — Blood Vessels #160 is the only item the audit
filed there), `Aging: Immune System` (2), and `Innate vs Adaptive Immunity`
(2).

## Scaffold subtopics removed in the rewrite

Dropped (no home in the new plan — re-add if a future source fills them):

- cells: Abnormal Cell Behavior: Cancer
- tissues: Tissue Types, Connective Tissue: Blood & Lymph, Tissue Injury, Abnormal Tissue Behavior: Cancer
- integumentary_system: Skin Functions: Sunlight
- skeletal_system: Skeletal System Functions *(deleted by David)*, Bone Physiology: Calcium Homeostasis
- muscular_system: Fascicle Arrangement *(deleted by David)*
- spinal_cord: Interneurons
- brain: Cranial Reflexes
- sensory_pathways_and_somatic_nervous_system: Sensory vs Motor *(removed by David)*
- autonomic_nervous_system: Higher-Order Cognitive Processes
- endocrine_system: 2nd Messenger Systems, Pineal Gland, Hormone Coordination /
  Physiology, General Adaptation Syndrome (all placeholder-only); Homeostasis:
  Endocrine Regulation + Hypothalamus + Pituitary Gland merged into
  "Endocrine Regulation"
- **Vol. 2 (2026-09-09):** blood: Platelets *(dissolved by David — #77/#78 →
  Hemostasis, #79–81 → Blood Composition)*; blood_vessels: Congenital Heart
  Problems *(merged into Fetal Cardiovascular System)*, Cardiovascular
  Response to Exercise *(no directive, no questions)*;
  lymphatic_and_immune_system: Regulation of Immunity *(no directive, no
  questions — the plan notes it as endocrine/nervous crossover)*

Merges/renames all follow `Anson Vol.1 Final Questions.md` (e.g. Gustation +
Olfaction → "Gustation and Olfaction"; Neuroglial Cells + Neurons → "Neural
Cells"; the four macromolecule subtopics → "Macromolecules").

## Loose ends (need David's decision)

1. ~~**Code follow-up:** `game_setup.py` `SUBJECT_TOPIC_ORDERS` rename~~ —
   done 2026-09-01 (`nervous_tissue` → `nervous_system` in `game_setup.py`
   and `tests/test_game_setup.py`; menu order verified against the real bank).
2. **8 Keep-range collisions:** these sat inside Keep ranges but the audit had
   filed them under Recommended-with-Edits (7) or Not Recommended (1), so they
   were NOT imported — they're flagged with ⚠ in `Anson Vol.1 - unreviewed.md`:
   LoA #31, #125 (the Not-Rec one), #148; CBO #44; Tissues #80; AppSkel #47;
   AxSkel #3; SpecSenses #142.
3. **13 True/False sweeps:** per the Misc note, every Recommended T/F-prompt
   question went to the unreviewed file, including 5 that were in Keep/Move
   lists (AxSkel #113, #120; BST #1–3) and 8 that were in Skip lists — each
   tagged with where it stood, pull back any I misread.
4. **5 recommendations never mentioned in the vetting file** (not imported,
   not in the edit pile): BST #61 (Bone Cell Types — oversight? the Keep list
   was 33, 58–60), BST #66/#81/#90 (Calcium Homeostasis, subtopic dropped),
   Tissues #1 (Tissue Types, subtopic dropped).
5. **SS #140/#141 double-listed:** inside the Equilibrium & Hearing Keep range
   *and* explicitly in Visual System's list — imported under **Visual System**
   (explicit beats range); say the word to flip them.
6. **Placements I chose** (moves whose target subtopic wasn't specified):
   BST #4/#18/#19 → skeletal / Bone Development and Growth (cartilage growth);
   Tissues #42/#43 → endocrine / Cell Signaling (`bio-anat-14-025`/`-026`);
   Tissues #44/#45 → integumentary / Sweat Glands; Tissues #83 →
   integumentary / Epidermis; Prime Movers #1 → muscular / Muscle Functions
   (absorbed Muscle Fiber Types).
7. **Missing concepts** (David's note, Body Regions): organ positions in the
   9 abdominopelvic regions and 4 quadrants — no source questions yet.
8. **Difficulty tiers:** everything imported at difficulty 1. Decided
   2026-09-01: grading waits for playtesting (see `implementation_plan.md`
   §7) — it matters most for Run from Red. The difficulty-3 tier (OpenStax
   critical thinking / VTCSOM) still to come.

## Loose ends — Vol. 2 (need David's decision)

Items 1–9 came out of the 2026-09-09 import of the first four topics; items
10–13 from the 2026-09-11 respiratory_system import. `anson_import2.py`
reproduces the run (`--write` regenerates all five JSON files from the audit +
vetting file, so fix things at the source and rerun).

1. ~~**Display label needed (game code):** `Cardiac Electrophysiology`~~ —
   DONE by David: aliased to "Cardiac Conduction" in `SUBTOPIC_DISPLAY_NAMES`.
2. ~~**Topic menu order (game code)**~~ — DONE by David for the first four
   topics, with a guard test (`test_every_shipped_topic_has_a_configured_position`).
   See item 10 for respiratory_system.
3. **3 Keep-range collisions:** inside Keep ranges but audit-filed under
   Recommended-with-Edits, so NOT imported: Blood #30 and #33 (Red Blood
   Cells, range 20–42) and Blood #108 (Hemostasis, range 82–111). Rewrite
   from the edit pile, or say "import as audited".
4. **Heart #119 — Keep vs Skip:** inside Cardiac Output's Keep range 118–121
   *and* on its Skip line; the explicit Skip won, so it's out (the
   cardioinhibitory-center question — #118 covers the accelerator side).
5. **Heart #92 placed under Cardiac Output:** it sits inside Cardiac
   Electrophysiology's Keep range 85–100 but David lists it explicitly under
   Cardiac Output (where the audit filed it too) — explicit beats range, as
   with SS #140/#141 in Vol. 1. Correctness check requested: "motor nerve
   fibers innervating the heart … modify heart rate" — fine as written.
   Heart #137 ("second heart sound … semilunar valves shut") also checks out.
6. **Blood #66 grammar fix applied:** prompt now reads "Lymphocytes can be
   recognized by their nuclei, which are _____, and by their cytoplasm, of
   which there is _____." (`bio-anat-15-096`).
7. **Subtopic label `Arteries and Veins`:** the vetting file says "and"; the
   topic plan and the audit say "Arteries & Veins". Imported with the vetting
   file's spelling (it's the canonical layout, per Vol. 1) — flip it in
   `anson_import2.py` PLAN and rerun if "&" was intended.
8. **Edit pile, 89 entries** for the four topics: 2 David moved (Heart #149,
   #111) + 87 audit Recommended-with-Edits (blood 11, heart 27, blood_vessels
   23, lymphatic_and_immune_system 26). No `Anson Vol.2 - unreviewed.md` has
   been generated yet — they still live in `question_recommendations_part2.md`
   under "Recommended with Edits". Generate the file once the remaining seven
   topics are vetted so it's built once.
9. **Coverage was complete:** every Recommended entry the audit filed under
   the four topics had a Keep/Skip/Move directive — nothing fell through.
10. **Topic menu order (game code), respiratory_system:** the guard test in
    `tests/test_game_setup.py` now fails (1 failed / 478 passed) because
    `SUBJECT_TOPIC_ORDERS` in `game_setup.py` doesn't list
    `respiratory_system` yet. Append it after `lymphatic_and_immune_system`.
    No display alias needed — all seven subtopic labels pass the pixel-layout
    width checks as-is.
11. **Respiratory #134 audit typo fixed at the source:** the audit's Options
    line had lost a `|`, making "carbaminohemoglobin dissolved carbon dioxide"
    one wrong choice of a two-choice item. Split into two choices in
    `question_recommendations_part2.md` → imported as a normal 3-choice
    shuffled question (`bio-anat-19-030`). Two-choice count for Vol. 2 stays at 5 (all heart).
12. **`Respiratory Anatomy` subtopic is empty:** its only two Recommended
    items (#38, #40) were moved to The Lungs per the vetting file, so the
    topic ships 7 subtopics, not the planned 8. Fine unless David wants the
    heading kept for future sources.
13. **Edit pile now 110 entries:** +21 audit Recommended-with-Edits for
    respiratory_system (no David-moved items this time). No Keep-range
    collisions with the edit pile, no Keep/Skip clashes, coverage complete.
