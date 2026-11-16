<!--
WORKING DRAFT, owner: Ismael; writing: Ana and the team.
- Rename to <NOMBRE_EQUIPO>.md (or export to <NOMBRE_EQUIPO>.pdf) before submitting.
- Sections marked TODO depend on the pipeline or on open decisions (see docs/decisiones.md).
- Only aggregates from the provided game: no frame numbers, no per-frame values, no per-moment
  descriptions of the video.
- Delete this comment before submitting.
-->

# <NOMBRE_EQUIPO>: frame-level ball possession, FC Barcelona vs Athletic Club

Team: Ismael Pintor, David Ortega, Antonio Azuer, Manuel Herrero, Ana Aparicio.
Repository: TODO public URL.

## 1. Summary

TODO (write last, 5 lines): what we built, the result on the public window as a pipeline check
only, and the one idea that matters most.

## 2. Reading the task from the metric

The ranking metric, `spellF1`, treats each possession as an object and matches predicted
possessions to true ones by temporal overlap. Three consequences shaped every decision:

- **Fragmenting a possession is the most expensive error.** The official baselines show it: the same
  nearest-player algorithm scores `spellF1` 0.05 unsmoothed and 0.24 with a 50-frame window, while
  `macroF1` barely moves (0.65 to 0.67). The temporal model therefore matters more than the
  per-frame classifier.
- **Timing matters.** A transition placed 8 frames late costs about 11 points of `spellF1` on that
  possession; one second late costs about 35.
- **`X` never helps on a graded frame.** The scorer fills an `X` with the previous label of that half
  before computing `spellF1`, and counts it as a miss in `macroF1`. We write `X` only outside the
  graded halves and always emit `H`, `A` or `D` inside them, including during long occlusions.

The 5-minute public ground truth was used only to check alignment, file format and the meaning of
the labels, never to choose between versions. The repository itself shows why: the baseline that is
best on the public window (`smooth125`, 0.42) is not the best on the full match (`smooth50`, 0.24).

## 3. Approach

TODO when the pipeline exists. Planned structure (`docs/investigacion_metodos.md` §4):

1. **Ball cleaning:** interpolate short gaps, discard physically impossible jumps.
2. **Dead-ball detector (`D`):** restarts from Smart Tagging, player-based signals, and the
   pre-kick-off stretch at the start of each half.
3. **Per-frame possession evidence:** nearest team to the ball in metres, with a control criterion
   rather than a single touch; collective signals when the ball is missing.
4. **Temporal decoder over {H, A, D}:** Viterbi with a cost per state change.

Why rules first and a learned model only if it wins on external validation: TODO.

## 4. Assets used and dropped

| asset | use | notes |
|---|---|---|
| Tactical ATD (automatic tracking) | main input | ball missing in 41 % of graded frames, 46 track slots for 22 players, no identities; coordinates scaled to metres with the 105.3 × 68.0 pitch |
| Smart Tagging | TODO | automatic, phases not possessions; `Team = N/A` on every throw-in |
| Homography | TODO | valid on 100 % of frames |
| Tactical video | not processed | watched by one team member, only on the public window, to understand what the labels mean (section 7) |
| Broadcast video, tracking and homography | dropped | not synchronised with the tactical timeline, homography valid on 65.8 % of frames, and too costly for the time available |

What we measured about the ATD, as aggregates over the whole match (TODO: confirm once PR
`feat/detector-balon-muerto` is merged):

- only 4.2 % of frames with a ball place it outside the pitch, so "ball out → `D`" covers very
  little: when the ball goes out, the ATD usually loses it;
- unlike the open Bundesliga data, the ATD does not freeze the ball position during stoppages;
- the ball speed column does not behave as m/s, so speeds are recomputed from positions.

## 5. Handling missing and noisy tracking

TODO: gap filling, jump filter, what happens when the ball is missing for long stretches, and how
the decoder carries possession through occlusions.

## 6. Training and validation data

No labels of any kind from the provided game were used to train, tune or validate anything.

### 6.1 Main dataset: Bundesliga (Bassek et al., 2025)

- **What:** 7 matches of the 2022/23 season, 2 from the Bundesliga and 5 from the 2. Bundesliga, with
  TRACAB optical tracking at 25 Hz and synchronised event data. Data owner: Deutsche Fußball Liga
  (DFL); licence CC-BY 4.0. In total 1,002,644 frames, 2,351 changes of team possession with the
  ball alive, and 710 stoppages.
- **Labels:** each frame carries `BallStatus` (alive or dead) and `BallPossession` (home or away),
  delivered by the provider with the tracking. The paper does not describe how these two flags are
  generated. Events (passes, ball recoveries, duels with a possession-change flag) are logged by
  human operators; so far we use them only as an independent reference to choose the control criterion.
- **Why this dataset:** it is the only open dataset we found with the same kind of per-frame label
  as the challenge ground truth.

**Experiment 0: do these labels follow the challenge rules?** Criteria were fixed before measuring,
with placebos and 21 variations of each parameter, per match and with the 7 matches pooled.

- **Dead ball: usable as is.** 99.4–100 % of throw-ins, goal kicks and corners have the end of a
  dead-ball stretch within ±5 s (14.6 % in the placebo).
- **But the ball position is frozen while dead,** and jumps a median 6.2 m when play resumes. A model
  trained on it would learn the label from the frozen ball, so the ball is masked during dead
  stretches and around their edges.
- **Team in possession: not usable as is.** The flag switches on the opponent's first touch, even
  without control: 72–85 % of uncontrolled touches between two controls of the same team flip it
  (10–14 % in the placebo). The challenge asks for a change only on controlled possession, so the
  team labels are re-derived with a control criterion.

**Experiment 1: which control criterion.** Using the human event annotations as an independent
reference:

- the choice of control definition removes between one third and two thirds of the provider's
  possessions;
- the current candidate is "the same player controls the ball for 12 frames, or the team makes two
  consecutive touches within 2 s". It is a measured compromise, not a clear winner. TODO: final
  choice and its numbers.

### 6.2 Secondary dataset: Metrica Sports sample data

TODO: whether it is used. Three anonymised matches with tracking and events; possession must be
derived from events, which tests whether conclusions hold with another provider.

### 6.3 Making the open data look like the ATD

TODO: degradation actually applied (removing ~41 % of ball frames, more in crowded areas and aerial
balls; removing identities; fragmenting tracks) and how close it gets to the ATD profile.

## 7. Possession rules implemented

Settled:

- **Three states.** `D` whenever the ball is dead; otherwise always `H` or `A`. A loose or contested
  ball stays with the last team in possession.
- **Second half.** The graded window starts 2,934 frames before the second-half kick-off; those
  frames are `D`. TODO: how the pipeline finds it (detected, or the kick-off frame published in
  `FAQ.md`).
- **`X`** only outside the graded halves.

Open (TODO before freezing):

- **Touch or control.** `CHALLENGE.md` defines a change of possession as the opponent gaining
  controlled possession, but also says the public ground truth is the reference when the two
  disagree. A team member watched the public window in the tactical video and reported counts only.
  In at least one short possession the ground truth gives possession after a touch without control,
  which points to a touch-based reading. This was one observer at one-second resolution: a signal,
  not a measurement.
- **When a change is dated:** at the first touch of the new team or once control is established.
  TODO: frame-level count on the public window, or the organisers' answer.
- Where we drew the line on loose balls, challenges, aerial duels and restarts. TODO.

## 8. Limitations

TODO. Known so far:

- the ball is missing exactly where possession tends to change;
- the label convention rests on a small qualitative check of the public window;
- the external data comes from another league and another tracking provider.

## 9. Reproduction

TODO: environment, pinned dependencies, the single command that regenerates the submission file
byte for byte, and expected run time.

```bash
pip install -r requirements.txt
export MTAH_DATA_DIR=/path/to/data
python -m possession.pipeline   # TODO: final command
python evaluation/validate_submission.py evaluation/results/<NOMBRE_EQUIPO>.csv
```

## 10. Use of LLMs

We used Claude (Anthropic) as a coding and research assistant. Following the competition terms,
no video, dataset or extract of the provided game was shared with it. It wrote code, which team
members ran locally, and it only saw aggregates (metrics, counts, timings), the public 5-minute
ground truth and open data from other matches.

## References

- Bassek, M., Rein, R., Weber, H. and Memmert, D. (2025). An integrated dataset of spatiotemporal
  and event data in elite soccer. *Scientific Data*, 12, 195.
  https://doi.org/10.1038/s41597-025-04505-y
- Metrica Sports sample data: https://github.com/metrica-sports/sample-data
- StatsBomb open data specification v1.1 (definition of possession).
- kloppy: https://github.com/PySport/kloppy
