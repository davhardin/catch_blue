# Question Bank Tracker

Last updated: 2026-09-19 — **question-bank work ON HOLD** (David, 2026-09-19:
the bank is enough for A&P 1 and carries the A&P 2 students a few weeks;
the rewrite queues, the loose ends below, and the five unvetted Vol. 2
topics resume when it is needed). Tier counts added to the topic table.
Previous status, 2026-09-14 (Anson Vol. 2 import IN PROGRESS — blood, heart,
blood_vessels, lymphatic_and_immune_system, respiratory_system, and
digestive_system vetted and imported, 1,040 questions; metabolism onward
still awaiting David's vetting pass. Difficulty grading 1–3 done for the
whole bank (M7.e, 2026-09-14). Quality review of the six Vol. 2 banks added
to `data/questions/flagged_questions.md` 2026-09-14.
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
| Anson *3600+ Review Questions*, Vol. 2 (3rd ed.) | CC BY-SA 3.0 | **Import in progress.** All 1,884 questions audited (2026-09-08) → `question_recommendations_part2.md` (1,594 REC / 273 EDIT / 17 NO). David has vetted 6 of 11 topics (blood → digestive_system) in `Anson Vol.2 Final Questions.md` → 1,040 imported (656 on 2026-09-09, +155 respiratory_system on 2026-09-11, +229 digestive_system on 2026-09-14) via `anson_import2.py`. **Still to vet:** metabolism, urinary_system, fluids_and_acid-bases, reproductive_system, development_and_inheritance (the audit is done for all of them). Edit pile for the 6 imported topics: 145 entries (see loose ends). |
| OpenStax *A&P 2e* review questions (ch. 1–4+) | CC BY-NC-SA 4.0 | **Not started.** Maps section-for-section onto existing subtopics. Educator account (free instructor test bank) not yet applied for. |
| OpenStax *A&P 2e* critical-thinking questions | CC BY-NC-SA 4.0 | **Not started.** Raw material for the difficulty-3 tier; needs MCQ-ification. |
| OER Commons question banks (OpenStax-aligned) | varies per item | **Not started.** Needs a free account; check each item's license. |
| VTCSOM *Human Anatomy Self-Assessment* | CC BY 4.0 | **Not started.** Med-school level — difficulty-3 well for skeletal/muscular/nervous. |
| Kenhub, GetBodySmart, freeanatomyquiz.com, Martini 12e | copyrighted | Inspiration/coverage-checklists only — never transcribe. |

## Topic status

Subtopic layout = the post-vetting plan from `Anson Vol.1 Final Questions.md`
(topics 01–14) and `Anson Vol.2 Final Questions.md` (topics 15+).
"Anson vetted" = David's manual pass over the audit recommendations.
Every question now carries a graded `difficulty` (1–3) — the M7.e pass,
2026-09-14, using the depth / terminology / distractor-plausibility rubric;
digestive_system was graded on import the same day.
Seven questions carry `"shuffle": false` (two-choice items): `bio-anat-06-229`,
`bio-anat-14-067`, and from Vol. 2 `bio-anat-16-003`, `-004`, `-005`, `-010`,
`-068` (heart — systole/diastole pairs and one "overlap is greater/less").

Id prefixes continue the Vol. 1 numbering in topic-plan order: 15 blood,
16 heart, 17 blood_vessels, 18 lymphatic_and_immune_system, 19
respiratory_system, 20 digestive_system. The next Vol. 2 topics should take 21 metabolism,
22 urinary_system, 23 fluids_and_acid-bases, 24 reproductive_system,
25 development_and_inheritance.

| Topic | Qs | Tiers 1 / 2 / 3 | Subtopics (imported count) | Anson vetted |
|---|---|---|---|---|
| anatomical_language | 134 | 99 / 34 / 1 | Anatomical Directions (26), Anatomy vs Physiology (8), Body Cavities (14), Body Regions (49), Homeostasis (13), Levels of Organization (26) | ✅ |
| chemical_foundations | 65 | 51 / 14 / 0 | Atoms, Elements, and Compounds (15), Chemical Bonds (4), Chemical Reactions (11), Macromolecules (27), pH and Body Fluids (9) | ✅ |
| cells | 75 | 52 / 22 / 1 | Cellular Transport (12), DNA, Transcription and Translation (13), Cell Membrane (11), Organelles (28), The Cell Cycle (11) | ✅ |
| tissues | 75 | 42 / 33 / 0 | Aging: Tissues (2), Connective Tissue (38), Epithelial Tissue (28), Muscle and Nervous Tissue (8) | ✅ |
| integumentary_system | 70 | 48 / 20 / 2 | Aging: Integumentary System (2), Dermis and Hypodermis (8), Epidermis (21), Hair and Nails (14), Integumentary Damage / Repair (14), Sweat Glands (12) | ✅ |
| skeletal_system | 332 | 135 / 165 / 32 | Aging: Skeletal System (5), Appendicular Skeleton (82), Axial Skeleton (104), Bone Cell Types (6), Bone Classification (27), Bone Development and Growth (17), Bone Fractures (7), Joints (87) | ✅ |
| muscular_system | 231 | 114 / 98 / 19 | Appendicular Muscles (56), Axial Muscles (49), Cardiac and Smooth Muscle (18), Neuromuscular Junction, EC Coupling, and Cross-Bridge Cycling (19), Muscle Energy & Recovery (23), Muscle Functions (30), Skeletal Muscle Structure (39) | ✅ |
| nervous_system *(was nervous_tissue)* | 111 | 54 / 50 / 7 | Action Potential (26), Divisions of the Nervous System (14), Membrane Potential (12), Neural Cells (28), Synaptic Transmission (32) | ✅ |
| spinal_cord | 67 | 25 / 34 / 8 | Spinal Cord Structure (23), Spinal Nerves (36), Spinal Reflexes (8) | ✅ |
| brain | 110 | 56 / 44 / 10 | Brain Protection (11), Brain Stem (18), Brain Development (7), Cerebellum (4), Cerebral Cortex (50), Cerebrospinal Fluid (7), Diencephalon (9), Limbic System (5) | ✅ |
| sensory_pathways_and_somatic_nervous_system | 39 | 21 / 16 / 2 | Afferent Division (13), Efferent Division (8), Sensory Receptors (18) | ✅ |
| autonomic_nervous_system | 49 | 16 / 27 / 6 | Aging: ANS (2), Autonomic Nervous System (18), Divisions of the Autonomic Nervous System (33) | ✅ |
| special_senses | 129 | 64 / 54 / 11 | Equilibrium and Hearing (45), Eye Structures (31), Gustation and Olfaction (14), Visual System (41) | ✅ |
| endocrine_system | 88 | 33 / 48 / 7 | Adrenal Glands (15), Cell Signaling (11), Disease: Diabetes Mellitus (5), Endocrine Regulation (21), Pancreas (13), Parathyroid Glands (3), Secondary Endocrine Organs (7), Thyroid Gland (13) | ✅ |
| blood | 106 | 61 / 40 / 5 | Blood Composition (23), Blood Types (4), Hemostasis (32), Red Blood Cells (24), White Blood Cells (23) | ✅ Vol. 2 |
| heart | 172 | 70 / 79 / 23 | Cardiac Cycle (20), Cardiac Electrophysiology (37), Cardiac Output (42), Heart Anatomy (73) | ✅ Vol. 2 |
| blood_vessels | 202 | 58 / 111 / 33 | Aging: Cardiovascular System (1), Arteries and Veins (53), Blood Pressure & Resistance (42), Fetal Cardiovascular System (6), Pulmonary & Systemic Circuits (67), Regulating Blood Flow (39) | ✅ Vol. 2 |
| lymphatic_and_immune_system | 168 | 79 / 68 / 21 | Adaptive Immunity (75), Aging: Immune System (2), Immune Disorders (8), Innate Immunity (21), Innate vs Adaptive Immunity (2), Lymphatic System Anatomy (62) | ✅ Vol. 2 |
| respiratory_system | 152 | 73 / 69 / 10 | Aging: Respiratory System (2), Gas Exchange (16), Gas Transport (21), Lower Respiratory System (26), Regulation of Breathing (31), The Lungs (47), Upper Respiratory System (12) | ✅ Vol. 2 |
| digestive_system | 228 | 93 / 107 / 28 | Accessory Digestive Organs (51), Chemical Digestion (17), Digestive System Functions (36), Large Intestine (18), Oral Cavity (22), Pharynx and Esophagus (15), Small Intestine (30), Stomach (40) | ✅ Vol. 2 |
| metabolism | 0 | — | *(plan: 7 subtopics)* | ⏳ audited, not vetted |
| urinary_system | 0 | — | *(plan: 5 subtopics)* | ⏳ audited, not vetted |
| fluids_and_acid-bases | 0 | — | *(plan: 6 subtopics)* | ⏳ audited, not vetted |
| reproductive_system | 0 | — | *(plan: 6 subtopics)* | ⏳ audited, not vetted |
| development_and_inheritance | 0 | — | *(plan: 6 subtopics)* | ⏳ audited, not vetted |

**Bank total as of 2026-09-19: 2,603 questions** (1,575 Vol. 1 after
removals + 1,028 Vol. 2 after the 2026-09-14 quality pass removed 12).

**Tier thinness (M7.e success check):** every topic has tier-1 and tier-2
questions. `chemical_foundations` and `tissues` have **no tier-3**
question — Anson's items there are recall and application only, and
nothing in the playtest notes rose to analysis. The OpenStax
critical-thinking questions are the named well for both; until then the
distance policy falls back 3 → 2 silently on those topics, by design.

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
  questions — the plan notes it as endocrine/nervous crossover)*;
  **2026-09-14:** digestive_system: Aging: Digestive System *(the audit filed
  no questions there — Anson has none; the topic ships 8 of the planned 9)*

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
8. ~~**Difficulty tiers:** everything imported at difficulty 1.~~ — DONE
   2026-09-14 (M7.e): every question graded 1–3; see the tier column above.
   The difficulty-3 tier (OpenStax critical thinking / VTCSOM) is still the
   thin one and still to come.

## Loose ends — Vol. 2 (need David's decision)

Items 1–9 came out of the 2026-09-09 import of the first four topics; items
10–13 from the 2026-09-11 respiratory_system import; items 14–20 from the
2026-09-14 digestive_system import. `anson_import2.py` reproduces the run
(`--write` regenerates every listed JSON file from the audit + vetting file,
so fix things at the source and rerun). **Since 2026-09-14 pass
`--only=topic` with `--write`** — the other banks now carry hand-applied
difficulty grades that a full regeneration would reset to 1.

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
14. ~~**Topic menu order (game code), digestive_system:**~~ — DONE 2026-09-19:
    both topics appended to `SUBJECT_TOPIC_ORDERS` and the test list. Item 10 was
    open — `SUBJECT_TOPIC_ORDERS` in `game_setup.py` ends at
    `lymphatic_and_immune_system`, so
    `test_every_shipped_topic_has_a_configured_position` fails for both
    `respiratory_system` and `digestive_system`. Append both, in that order,
    and extend `ANATOMY_PHYSIOLOGY_TOPICS` in `tests/test_game_setup.py` to
    match. Subtopic labels ("Accessory Digestive Organs", "Digestive System
    Functions") pass the pixel-layout width checks — no display alias needed.
15. ~~**Pixel-layout test assumption (test code):**~~ — DONE 2026-09-19: the test
    now scrolls the widest label's row to the top of the region instead of to
    `max_scroll`. Original note:
    `test_scrolled_rightmost_label_click_uses_instance_clip` (both themes)
    fails with 20 topics. It scrolls the Topics list to `max_scroll` and
    clicks the widest label (sensory_pathways…, row 11); with 21 rows the
    bottom scroll offset is 624 px, which puts that row above the scroll
    region (y = 234 vs top 260). The game is fine — the test needs to scroll
    so the target row is visible (e.g. offset = target row × row height,
    clamped) instead of assuming the widest label survives a scroll to the
    end.
16. **Stomach directive read as two sections:** the vetting file lists all
    of Stomach under "gross anatomy: 39-45, 51-55, 57-66, 68, 69, 71-73,
    75-84, 86-88", but gross-anatomy 51–79 are Large Intestine / Accessory
    items already claimed elsewhere, and 51–88 with exactly those gaps (56,
    67, 70, 74, 85 = the audit's Recommended-with-Edits) is the Physiology
    section's Stomach block. Imported as GA 39–45 + PH 51–88 (40 questions,
    `bio-anat-20-190`–`-229`). Say the word if that was not the intent.
17. **Physiology #11 moved** from Chemical Digestion (audit) to Digestive
    System Functions per the vetting file (`bio-anat-20-088`).
18. **Subtopic spelling:** imported as "Pharynx and Esophagus" (vetting
    file); the audit and topic plan have the typo "Espophagus".
19. **Edit pile now 145 entries:** +35 audit Recommended-with-Edits for
    digestive_system (GA #4, 6, 10, 28, 33, 36, 68, 70; PH #6, 12, 13, 16,
    17, 30, 34, 36, 56, 67, 70, 74, 85, 93, 104, 105, 110, 116, 121, 136,
    137, 138, 156, 168, 173, 182, 183). No Keep-range collisions, no
    Keep/Skip clashes, no True/False sweeps, coverage complete (all 229
    Recommended entries had a directive). GA #35 is the section's one
    Not-Recommended item; untouched.
20. **Quality review, Vol. 2 banks (2026-09-14):** blood, heart,
    blood_vessels, lymphatic_and_immune_system, respiratory_system, and
    digestive_system read question-by-question, flags appended to
    `data/questions/flagged_questions.md` (second section, own summary
    table). Nothing removed — David decides per entry, as with the Vol. 1
    pass.
