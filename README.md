# N-Body Problem

*Exploring the N-body problem through information theory and Structured Knowledge Accumulation (SKA)*

This repository investigates whether Structured Knowledge Accumulation (SKA)
can reconstruct the organization and dynamics of the Solar System through
learning from causal information exchanges, with kinetic energy interpreted
as the physical cost of learning.

## Research goal

The research proceeds in two stages:

1. **Learn from the planetary dataset.** Process the reception stream with
   SKA, track the weight matrix elements and entropy evolution, and test
   whether a weight–distance relationship such as $W_{ij}\propto 1/r_{ij}$
   emerges without imposing that dependence on the weights. Each matrix
   element must have a defined relational meaning so it can be compared with
   the corresponding distance held separately for evaluation.
2. **Explore autonomous reconstruction.** Use the learned relationship to
   investigate whether SKA can generate the system's evolving geometry without
   prescribing Newton's laws or supplying further planetary trajectories.
   The proposed starting condition is an asymptotic state of infinite
   separation and zero velocity. Kinetic energy is interpreted as the physical
   cost of learning; the quantitative connection between entropy evolution
   and kinetic energy remains to be established.

The central hypothesis is that the system can self-organize through learning
from its own interactions: received information changes the learned
relationships, those relationships determine geometry, and changing geometry
changes subsequent interactions. The experiments will test this hypothesis;
the inverse-distance weight dependence and autonomous reconstruction are not
assumed results.

## Current implementation

This version provides the observation stream for the first stage: a
deterministic dataset generated from planetary orbital inputs, together with
a replay program that emits events in their modeled reception-time order.
The SKA weight–distance experiment and autonomous reconstruction remain
research objectives.

The learner receives one return event at a time, representing the information
available to the Sun within the abstraction. It is not given eight
synchronized Cartesian positions. The stream provides a candidate input $X$
for testing a learned weight matrix $W$.

## The abstraction

The Sun emits a spherical wave with reference amplitude $A_0$ at its solar
Compton frequency:

$$
f_{C,\odot}=\frac{M_\odot c^2}{h}.
$$

Planet $i$ receives the wave and re-emits the received amplitude at its own
Compton frequency:

$$
f_{C,i}=\frac{m_i c^2}{h}.
$$

The outward and return legs each use an inverse-distance amplitude law. With
$R_\odot$ the solar radius, $R_i$ the planetary radius, and $d_i$ the
surface-to-surface separation, the returned amplitude ratio is:

$$
q_i=\frac{A_i^{\mathrm{return}}}{A_0}
=\frac{R_\odot R_i}{(R_\odot+d_i)(R_i+d_i)}.
$$

$$
\frac{\Delta A_i}{A_0}=q_i-1.
$$

For distances much larger than the body radii,

$$
q_i\approx\frac{R_\odot R_i}{r_i^2}.
$$

The inverse-square dependence is produced by composing the two $1/r$
propagation factors.

This is a property of the spherical wave. Its amplitude falls as $1/r$, and
because $\frac{d}{dr}\!\left(\frac{1}{r}\right) = -\frac{1}{r^2}$, the returned
$1/r^2$ is exactly the derivative of the outward $1/r$: the two legs are one
function and its gradient, not two independent factors.

The Compton frequency is the source signature. The return direction is given
by azimuth $\lambda$ and elevation $\beta$. A reception event therefore
contains amplitude, source signature, and direction.

## Why it is a stream

At local time $t$, the Sun does not receive the simultaneous state

$$
\bigl(\mathbf{x}_1(t),\mathbf{x}_2(t),\ldots,\mathbf{x}_8(t)\bigr).
$$

It receives delayed events from different retarded times. A round trip takes
approximately

$$
\tau_i\approx\frac{2r_i}{c}
$$

and the planet moves through an arc during that interval. Thus a tick is a
delayed observation associated with a finite path interval, rather than a
perfectly current point position. The stream records that interval through
the reception time and `round_trip_duration_seconds`.

All returns are merged chronologically. One arrival creates one integer tick:

$$
k=1,2,3,\ldots
$$

The tick order is the primary structure exposed to SKA. The stream is
forward-only and historical events are never rewritten.

## Learner-facing event

The file `data/planetary_reception_stream.jsonl.gz` contains 46,786 newline-
delimited JSON events. A shortened example is:

```json
{
  "schema": "ska.planetary_reception.v1",
  "event_id": "planetary-reception-000001",
  "tick": 1,
  "reception_seconds_since_j2000_tdb": 460.888664460066,
  "source_compton_frequency_hz": 4.477492300116378e+73,
  "return_amplitude_over_A0": 3.520178531091838e-07,
  "delta_A_over_A0": -0.9999996479821469,
  "azimuth_radians": 4.429360777355464,
  "elevation_radians": -0.05275792710191322,
  "round_trip_duration_seconds": 460.888664460066,
  "x_candidate": [-6.45343531, -0.27926465, -0.96021417,
                  -0.05273346, 0.99860862, 0.0]
}
```

The full event also contains the J2000 reception Julian date, the gap since
the previous reception, a local sequence count for the source signature, and
the names of the candidate features.

The stream does not expose:

- planet names;
- planet identifiers;
- heliocentric distance;
- Cartesian $(x,y,z)$ positions.

`data/frequency_truth_map.json` contains frequency-to-planet labels only for
evaluation after learning. It is kept outside the learner-facing event
records. The manifest lists the eight numeric source frequencies and points to
this optional truth sidecar; it does not add planet labels to the event stream.

## A candidate $X$

Each event includes one exploratory six-component vector:

$$
X_k=\begin{bmatrix}
\log_{10}(q_k)\\
\cos(\lambda_k)\\
\sin(\lambda_k)\\
\sin(\beta_k)\\
\cos(\beta_k)\\
\widetilde{\log_{10}(f_{C,k})}
\end{bmatrix}.
$$

The tilde denotes the normalized logarithmic source frequency.

The sine and cosine pairs preserve angular continuity at the azimuth wrap. The
frequency is scaled only for numerical convenience; the raw frequency remains
available in the event. This vector is a starting representation, not a final
definition of $X$. The raw stream fields allow other representations to be
tested without changing the generated events.

An SKA experiment can process one $X_k$ per tick and form:

$$
\begin{aligned}
Z_k&=WX_k,\\
D_k&=\sigma(Z_k),\\
\Delta D_k&=D_k-D_{k-1}.
\end{aligned}
$$

Here $\sigma$ is the elementwise sigmoid function.

The resulting structured knowledge and entropy can be recorded separately
from the raw stream. For the SKA formulation used in the project, the
discrete entropy accumulation is

$$
H_{\mathrm{SKA}}=-\frac{1}{\ln 2}\sum_k Z_k\cdot\Delta D_k.
$$

## Repository layout

```text
N-Body-Problem/
├── README.md
├── requirements.txt
├── data/
│   ├── planetary_reception_stream.jsonl.gz  # learner-facing ticks
│   ├── stream_preview.json                  # first 12 events
│   ├── stream_manifest.json                 # schema and checksum
│   ├── frequency_truth_map.json             # evaluation metadata
│   ├── directional_tick_stream.npz          # directional source dataset
│   └── planetary_wave_samples.npz           # launch/return samples
├── figures/
│   └── helicoidal_tick_stream.png
└── scripts/
    ├── build_stream.py
    └── replay_stream.py
```

## Rebuild the stream

The repository includes the exact input arrays used to generate the supplied
stream. Install the one numerical dependency and rebuild:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python scripts/build_stream.py
```

The builder checks the chronological tick index, reception ordering, and
positive return envelopes. It writes the learner stream, preview, frequency
truth map, and manifest into `data/`.

## Replay the stream

The replay program writes one JSON event per line to standard output. It keeps
the modeled reception gaps when `--speed 1` is used. Larger values accelerate
the same sequence; `--speed 0` removes waiting.

```bash
# Inspect the first 160 events quickly
python scripts/replay_stream.py --speed 1000000 --limit 160

# Pipe events directly into an SKA consumer
python scripts/replay_stream.py --speed 1000000 | your_ska_consumer
```

Use `--emit-replay-time` when a consumer also needs the wall-clock time at
which the replay process emitted each event. The original J2000 reception time
is always retained.

## Provenance and scope

The orbital input comes from JPL's approximate Keplerian elements and rates,
Table 1, valid for 1800–2050:

<https://ssd.jpl.nasa.gov/planets/approx_pos.html>

Planetary radii and masses used in the amplitude calculation come from JPL's
planetary physical parameters:

<https://ssd.jpl.nasa.gov/planets/phys_par.html>

The Earth orbital position is represented by the Earth–Moon barycentre. The
current dataset uses the same frozen-geometry-per-round-trip approximation as
the earlier plots. It does not include endpoint motion during a signal leg,
measurement noise, carrier phase, Doppler corrections, gravitational
frequency shifts, or a dynamical force law.

This is an abstraction and a controlled learning dataset. It is not a claim
that the Sun or planets physically exchange total-mass Compton waves. The
positions are used internally to synthesize the observation stream; they are
not supplied to the learner.

## Validation snapshot

- 46,786 chronological reception ticks.
- Eight unique Compton-frequency signatures.
- Shared observation window: approximately 88.4 days from J2000.
- First reception: 460.888664 seconds after J2000.
- Last reception: 7,637,776.630 seconds after J2000.
- The manifest records the SHA-256 checksum of the uncompressed JSONL stream.
pe

The orbital input comes from JPL's approximate Keplerian elements and rates,

## A note on Wheeler's participatory picture

The construct is a working realization of John Archibald Wheeler's
*it from bit*: the idea that every "it" derives its existence from
answers to yes-or-no questions.

> "It from bit. [...] every 'it' — every particle, every field of force,
> even the spacetime continuum itself — derives its function, its meaning,
> its very existence entirely [...] from [...] answers to yes-or-no
> questions, binary choices, bits." — J. A. Wheeler

Read that way, the abstraction is a dialogue:

- The outward spherical wave is a question: *where are you?*
- Each return is an answer: *I am here* — a single complete bit carrying
  identity (the Compton frequency), direction (azimuth and elevation), and
  amplitude (the $1/r$ potential and its $1/r^2$ gradient).
- The geometry is not measured; it is **assembled from the accumulated
  answers**. No question, no bit; no bit, no geometry. This is why the
  configuration is relaxed into rather than launched, and why motion is the
  cost of learning rather than the effect of a force.

The same picture fixes the arrow of time. Because a round trip takes
$\tau_i \approx 2r_i/c$, every *I am here* refers to a **past** here. The
learner never holds the simultaneous present state that a differential
equation presupposes — a state that, under relativistic causality, no
observer possesses. What exists in the present is only the record: the
weight matrix and the accumulated entropy. The stream is forward-only and
historical events are never rewritten.

> "The past has no existence except as it is recorded in the present."
> — J. A. Wheeler

This is the conceptual lineage of the abstraction, not a claim to have
reproduced Wheeler's program. It states the design axiom plainly: keep only
the recorded present, and refuse the simultaneous global state that the
differential-equation view quietly assumes.
