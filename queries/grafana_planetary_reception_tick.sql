-- The planetary reception stream on the REAL index `tick`
-- Datasource: QuestDB plugin (questdb-questdb-datasource, uid 2Bi8EToVz)
-- Table:      planetary_reception_stream
--
-- tick = the global reception-stream counter: 1 .. 4,745,929, strictly
-- increasing, fully unique. Exactly ONE echo per integer tick, in true
-- chronological order, and that echo belongs to exactly ONE source. The stream
-- is a single interleaved scalar signal q_relative_diff(tick).
--
-- Panel: XY Chart, x = tick, y = q_relative_diff, with "Connect null values" =
-- true. Each per-source column is non-null only on that planet's own ticks, so
-- null-connection draws one clean line per planet (it never joins across
-- sources -- a different source lives in a different column).

-- ============================================================================
-- DISPLAY QUERY -- one nullable column per source, so Grafana can COLOR each
-- source and give it a legend entry. This is STILL one event per index: each
-- row is one tick and exactly ONE column is non-null (the source of that echo);
-- the other seven are NULL. No GROUP BY / max() needed -- there is already one
-- row per tick. The split is by source_compton_frequency_hz, a REAL observable
-- the learner receives -- so these curves are the stream to learn, not an
-- annotation. Only the legend NAMES (Mercury, Venus, ...) come from the truth
-- map, and are used to score the learner, never as input.
-- ============================================================================
SELECT tick,
  CASE WHEN source_compton_frequency_hz = 4.4774923001163785e73 THEN q_relative_diff END AS "Mercury",
  CASE WHEN source_compton_frequency_hz = 6.601982728808719e74  THEN q_relative_diff END AS "Venus",
  CASE WHEN source_compton_frequency_hz = 8.100606534925774e74  THEN q_relative_diff END AS "Earth",
  CASE WHEN source_compton_frequency_hz = 8.703848530773663e73  THEN q_relative_diff END AS "Mars",
  CASE WHEN source_compton_frequency_hz = 2.5746024944209535e77 THEN q_relative_diff END AS "Jupiter",
  CASE WHEN source_compton_frequency_hz = 7.708609105416307e76  THEN q_relative_diff END AS "Saturn",
  CASE WHEN source_compton_frequency_hz = 1.1774829638745261e76 THEN q_relative_diff END AS "Uranus",
  CASE WHEN source_compton_frequency_hz = 1.3890706975128312e76 THEN q_relative_diff END AS "Neptune"
FROM planetary_reception_stream
WHERE tick BETWEEN 1 AND 100000
ORDER BY tick;

-- ============================================================================
-- SOURCE-BLIND VIEW -- q_relative_diff alone, ignoring the source frequency.
-- A reduced view (drops an observable the learner actually has); useful to see
-- the aggregate transition signal, NOT "all the learner sees".
-- ============================================================================
SELECT tick, q_relative_diff
FROM planetary_reception_stream
WHERE tick BETWEEN 1 AND 100000
ORDER BY tick;

-- Decimated across the full 25-year range (keep every 100th event):
SELECT tick, q_relative_diff
FROM planetary_reception_stream
WHERE tick % 100 = 0
ORDER BY tick;

