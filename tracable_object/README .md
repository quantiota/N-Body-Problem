# The traceable object — arc per round trip

During one light round trip `τ = 2r/c` — the time the Sun's echo takes to reach a
planet and return — the planet moves along its orbit by an arc `s = v_orb · τ`.
How big is that arc? Two comparisons, with opposite characters.

Reproduce both tables:

```bash
python arc_analysis.py
```

## Table 1 — arc vs the planet's diameter (a *coincidence*)

| planet | round-trip τ | v_orb (km/s) | arc (km) | diameter (km) | arc / diameter |
|---|---|---|---|---|---|
| Mercury | 386 s | 47.88 | 18,492 | 4,879 | 3.79 |
| Venus | 722 s | 35.03 | 25,275 | 12,104 | 2.09 |
| Earth | 998 s | 29.78 | 29,725 | 12,742 | 2.33 |
| Mars | 1,521 s | 24.13 | 36,696 | 6,779 | 5.41 |
| Jupiter | 5,193 s | 13.06 | 67,804 | 139,822 | **0.48** |
| Saturn | 9,518 s | 9.64 | 91,798 | 116,464 | 0.79 |
| Uranus | 19,152 s | 6.80 | 130,216 | 50,724 | 2.57 |
| Neptune | 30,010 s | 5.43 | 163,003 | 49,244 | 3.31 |

The arc is the same order as the planet's diameter — but the ratio **wanders ~11×**
(0.48 → 5.41), and `arc/diameter = √(GM☉·r)/(c·R)` links the *orbit* to the
planet's *radius* with no mechanism between them. A variable ratio with no forcing
mechanism is a **coincidence**, not a law.

## Table 2 — arc as a fraction of the orbit (a *necessity*)

| planet | v_orb (km/s) | arc as % of orbit | = 1 part in (round trips / orbit) |
|---|---|---|---|
| Mercury | 47.88 | 0.00508% | 19,671 |
| Venus | 35.03 | 0.00372% | 26,887 |
| Earth | 29.78 | 0.00316% | 31,621 |
| Mars | 24.13 | 0.00256% | 39,036 |
| Jupiter | 13.06 | 0.00139% | 72,128 |
| Saturn | 9.64 | 0.00102% | 97,652 |
| Uranus | 6.80 | 0.00072% | 138,521 |
| Neptune | 5.43 | 0.00058% | 173,398 |

Here the arc is a **minuscule fraction of the orbit** — `~10⁻⁵`, one part in tens
of thousands. And this one **is** forced:

```
arc / orbit = τ / T = v_orb / (π c)
```

It depends only on `v_orb / c`, and planetary speeds are **always ≪ c**
(non-relativistic, for any bound orbit around a star). So `arc ≪ orbit` is
**guaranteed by `v ≪ c`** — law-like, not lucky. The light-speed round trip
*freezes* the slow-moving planet.

## Why it matters: the traceable object

Because the arc is `~1/20,000` to `~1/173,000` of the orbit, each planet is
essentially **frozen between receptions** — a sharp, well-localized, **traceable
object** from tick to tick. It does not smear or jump; it is the *same object*,
barely displaced, every time.

That is the **prerequisite for learning** from the reception stream: to accumulate
knowledge about a thing, the thing must persist as an *identifiable object* across
observations. If planets moved a large fraction of their orbit per round trip
(relativistic speeds), there would be no stable object to track and no learning
possible. Because light is fast and planets are slow, the abstraction hands the
learner **traceable objects by necessity**.

- `arc ≈ diameter` — a coincidence (variable, no mechanism).
- **`arc ≪ orbit` — a necessity (`v ≪ c`)**, and *this* is what makes the planet a
  traceable object.

The `1 part in N` column equals the number of round trips per orbit; Neptune's
~173,000 matches the ~174,000 cycles-per-orbit measured from the stream itself.
