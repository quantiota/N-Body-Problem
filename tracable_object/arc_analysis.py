#!/usr/bin/env python3
"""Arc a planet sweeps during one light round trip, tau = 2 r / c.

During the round trip the Sun's echo takes to reach a planet and return, the
planet moves along its orbit by an arc  s = v_orb * tau.  Two comparisons:

  Table 1 -- s vs the planet's DIAMETER.  Ratio ~O(1) (0.5 .. 5), but it varies
             ~11x across planets and links the orbit to the planet's radius with
             no mechanism -> a coincidence, not a law.

  Table 2 -- s as a fraction of the ORBIT.  s/orbit = tau/T = v_orb/(pi c), which
             is ALWAYS << 1 because planetary speeds are << c (non-relativistic).
             This is law-like, guaranteed by v << c -- NOT a coincidence.

The point of Table 2: because the arc is ~1e-5 of the orbit, each planet is
essentially frozen between receptions -- a sharp, TRACEABLE OBJECT from tick to
tick.  A stable, identifiable object across observations is the prerequisite for
learning from the reception stream.  Light is fast and planets are slow, so the
abstraction hands the learner traceable objects by necessity.

"1 part in N" in Table 2 equals the number of round trips per orbit; Neptune's
~173,000 matches the ~174,000 cycles-per-orbit found from the stream itself.
"""
import numpy as np

GM = 1.32712440018e20      # GM_sun, m^3 s^-2
C = 299792458.0
AU = 1.495978707e11

# name, semi-major axis (AU), radius (km)
P = [("Mercury", 0.387, 2439.7), ("Venus", 0.723, 6051.8),
     ("Earth", 1.000, 6371.0),  ("Mars", 1.524, 3389.5),
     ("Jupiter", 5.203, 69911.0), ("Saturn", 9.537, 58232.0),
     ("Uranus", 19.19, 25362.0),  ("Neptune", 30.07, 24622.0)]


def main():
    print("Table 1 -- arc per round trip vs planet diameter (a coincidence, ~O(1))\n")
    print("  planet    round-trip tau   v_orb(km/s)   arc(km)     diameter(km)   arc/diameter")
    for n, a, rk in P:
        r = a * AU; v = np.sqrt(GM / r); tau = 2 * r / C; s = v * tau; d = 2 * rk * 1e3
        print("  %-8s   %8.1f s    %6.2f     %9.0f    %9.0f       %.2f"
              % (n, tau, v / 1e3, s / 1e3, d / 1e3, s / d))

    print("\n\nTable 2 -- arc as a fraction of the orbit (a necessity, v<<c -> arc<<orbit)\n")
    print("  planet    v_orb(km/s)   arc as %% of orbit   = 1 part in   (= round trips/orbit)")
    for n, a, rk in P:
        r = a * AU; v = np.sqrt(GM / r); tau = 2 * r / C
        T = 2 * np.pi * np.sqrt(r ** 3 / GM)
        frac = tau / T
        print("  %-8s   %6.2f        %.5f%%           %8.0f"
              % (n, v / 1e3, 100 * frac, 1 / frac))

    print("\n\nTable 3 -- learning time: one full orbit closes a source's loop\n"
          "(system learned when the SLOWEST source, Neptune, laps -> 173,398 round\n"
          " trips ~ 164.9 yr; then every planet has been seen through >= 1 orbit)\n")
    DAY = 86400.0; YR = 365.25 * DAY
    print("  planet    orbital period   round trips / orbit  (= learning round trips)")
    for n, a, rk in P:
        r = a * AU; tau = 2 * r / C; T = 2 * np.pi * np.sqrt(r ** 3 / GM)
        per = ("%.1f d" % (T / DAY)) if T < 2 * YR else ("%.2f yr" % (T / YR))
        print("  %-8s  %-11s    %10.0f" % (n, per, T / tau))


if __name__ == "__main__":
    main()
