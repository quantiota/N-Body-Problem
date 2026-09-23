-- Successive difference of the reception stream on the real index `tick`
-- Datasource: QuestDB plugin (uid 2Bi8EToVz)  ·  Table: planetary_reception_stream
--
-- Reindex by -1 and subtract:  d[k] = v[k] - v[k-1]
-- `lag(...) OVER (ORDER BY tick)` is the reindex; the subtraction is the diff.
--
-- Panel: XY Chart, x = tick, y = q_relative_diff_delta.
-- IMPORTANT: draw POINTS, not lines (Draw style -> Points, or line width 0).
--   Consecutive ticks belong to DIFFERENT transition classes, so connecting them
--   paints a solid band.  As points, the scatter resolves into ~57 smooth strands
--   -- one per occurring (previous -> current) planet pair.
-- Color: Grafana transform "Partition by values" on source_compton_frequency_hz.
--
-- NULLs: q_relative_diff is undefined on each source's FIRST return, so a few
-- rows near the start carry a null delta (14 of the first 100,000).

SELECT
  tick,
  q_relative_diff - lag(q_relative_diff) OVER (ORDER BY tick) AS q_relative_diff_delta,
  source_compton_frequency_hz
FROM planetary_reception_stream
WHERE tick BETWEEN 1 AND 100000
ORDER BY tick;


-- Variant: colour the strands by TRANSITION (previous -> current) rather than by
-- the current planet alone.  Each strand is one ordered pair (i, j), matching the
-- 56 off-diagonal entries of W; the 7 absent combinations are the non-Mercury
-- self-loops (only the fastest returner, Mercury, may follow itself).
--
-- SELECT
--   tick,
--   q_relative_diff - lag(q_relative_diff) OVER (ORDER BY tick) AS q_relative_diff_delta,
--   lag(source_compton_frequency_hz) OVER (ORDER BY tick) AS prev_source_hz,
--   source_compton_frequency_hz AS curr_source_hz
-- FROM planetary_reception_stream
-- WHERE tick BETWEEN 1 AND 100000
-- ORDER BY tick;
