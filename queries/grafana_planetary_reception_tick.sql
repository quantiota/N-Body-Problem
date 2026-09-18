

-- The planetary reception stream on the REAL index `tick`
-- Datasource: QuestDB plugin (questdb-questdb-datasource, uid 2Bi8EToVz)
-- Table:      planetary_reception_stream
--
-- tick = the global reception-stream counter: 1 .. 4,745,929, strictly
-- increasing, fully unique. Exactly ONE echo per integer tick, in true
-- chronological order, and that echo belongs to exactly ONE source. The stream
-- is a single interleaved scalar signal q_relative_diff(tick).
--
-- Panel: XY Chart, x = tick, y = q_relative_diff, drawn as POINTS (consecutive
-- ticks are different sources -- do not connect them with lines).

-- ============================================================================
-- DISPLAY QUERY -- one nullable column per source, so Grafana can COLOR each
-- planet and give it a legend entry. This is STILL one event per index: each
-- row is one tick and exactly ONE column is non-null (the source of that echo);
-- the other seven are NULL. No GROUP BY / max() needed -- there is already one
-- row per tick. The coloring uses the source label (the truth map the learner
-- is not given); the DATA is one-event-per-index, the colors are annotation.
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
WHERE tick BETWEEN 1 AND 50000
ORDER BY tick;

-- ============================================================================
-- WHAT THE LEARNER ACTUALLY SEES -- the raw stream, one unlabeled series.
-- One column of q_relative_diff, one point per index, no source split.
-- ============================================================================
SELECT tick, q_relative_diff
FROM planetary_reception_stream
WHERE tick BETWEEN 1 AND 50000
ORDER BY tick;

-- Decimated across the full 25-year range (keep every 100th event):
SELECT tick, q_relative_diff
FROM planetary_reception_stream
WHERE tick % 100 = 0
ORDER BY tick;
