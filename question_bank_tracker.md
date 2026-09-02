# Question Bank Tracker

Last updated: 2026-09-01 (Anson Vol. 1 import COMPLETE — endocrine vetted and
imported; the bank contains zero placeholder questions).

What this file tracks: which subtopics exist per topic, which sources have
been reviewed for which topics, and which sources are still untouched — so
nothing falls through the cracks between machines. This file lives at the
repo root **on purpose**: `question_sources/` is gitignored, so the audit and
vetting files there (`question_recommendations.md`, `Anson Vol.1 Final
Questions.md`, `Anson Vol.1 - unreviewed.md`) do **not** sync via git — this
tracker does.

## Sources

| Source | License | Status |
|---|---|---|
| Anson *3600+ Review Questions*, Vol. 1 (5th ed.) | CC BY-SA 3.0 | **Import complete.** All 1,870 questions audited (2026-08-31) → David vetted all 14 topics → 1,595 imported 2026-09-01. Remaining: the 177-question edit pile in `Anson Vol.1 - unreviewed.md` (David's rewrites). |
| Anson *3600+ Review Questions*, Vol. 2 | CC BY-SA 3.0 | On disk (`question_sources/`), **not audited**. Covers the A&P II sequence — relevant when topics expand past `endocrine_system`. |
| OpenStax *A&P 2e* review questions (ch. 1–4+) | CC BY-NC-SA 4.0 | **Not started.** Maps section-for-section onto existing subtopics. Educator account (free instructor test bank) not yet applied for. |
| OpenStax *A&P 2e* critical-thinking questions | CC BY-NC-SA 4.0 | **Not started.** Raw material for the difficulty-3 tier; needs MCQ-ification. |
| OER Commons question banks (OpenStax-aligned) | varies per item | **Not started.** Needs a free account; check each item's license. |
| VTCSOM *Human Anatomy Self-Assessment* | CC BY 4.0 | **Not started.** Med-school level — difficulty-3 well for skeletal/muscular/nervous. |
| Kenhub, GetBodySmart, freeanatomyquiz.com, Martini 12e | copyrighted | Inspiration/coverage-checklists only — never transcribe. |

## Topic status

Subtopic layout = the post-vetting plan from `Anson Vol.1 Final Questions.md`.
"Anson vetted" = David's manual pass over the audit recommendations.
All imported questions are `difficulty: 1` for now — no difficulty grading yet.
Two questions carry `"shuffle": false` (two-choice items): `bio-anat-06-229`
and `bio-anat-14-067`.

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
| endocrine_system | 89 | Adrenal Glands (15), Cell Signaling (11), Disease: Diabetes Mellitus (5), Endocrine Regulation (21), Pancreas (13), Parathyroid Glands (3), Secondary Endocrine Organs (7), Thyroid Gland (14) | ✅ |

**Thin subtopics — come back later** *(accepted as-is 2026-09-01)*: three
Aging subtopics sit at 2 questions, below the M5 ≥3 baseline, by decision:
`Aging: Tissues` (6 rewrite candidates waiting in the edit pile),
`Aging: Integumentary System` (1 candidate in the pile), and `Aging: ANS`
(Anson is exhausted — needs an original question or a merge). Top them up
when working the edit pile or importing the next source.

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
