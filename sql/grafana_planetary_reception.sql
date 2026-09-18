-- Grafana / QuestDB queries for the planetary reception stream
-- Datasource: QuestDB plugin (questdb-questdb-datasource, uid 2Bi8EToVz)
-- Table:      planetary_reception_stream
--
-- GOAL: q_relative_diff on the Y axis, the EVENT INDEX on the X axis (NOT time).
-- Panel type: XY Chart  (x-field = source_sequence_index, y-field = q_relative_diff).
-- q_relative_diff is the per-source successive relative amplitude diff, so its
-- natural index is source_sequence_index (that source's own return counter:
-- 1, 2, 3, ...). Use "tick" instead for the global stream event index.
--
-- Millions of rows per planet -> decimate with:  AND source_sequence_index % 500 = 0
--
-- source_compton_frequency_hz per planet:
--   Mercury 4.4774923001163785e73    Mars    8.703848530773663e73
--   Venus   6.601982728808719e74     Earth   8.100606534925774e74
--   Uranus  1.1774829638745261e76    Neptune 1.3890706975128312e76
--   Saturn  7.708609105416307e76     Jupiter 2.5746024944209535e77

-- ============================================================================
-- q_relative_diff vs event index, per planet  (one target per planet: refId A..H)
-- ============================================================================

-- A  Mercury
SELECT source_sequence_index, q_relative_diff AS "Mercury"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 4.4774923001163785e73 AND source_sequence_index % 500 = 0
ORDER BY source_sequence_index;

-- B  Venus
SELECT source_sequence_index, q_relative_diff AS "Venus"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 6.601982728808719e74 AND source_sequence_index % 300 = 0
ORDER BY source_sequence_index;

-- C  Earth
SELECT source_sequence_index, q_relative_diff AS "Earth"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 8.100606534925774e74 AND source_sequence_index % 200 = 0
ORDER BY source_sequence_index;

-- D  Mars
SELECT source_sequence_index, q_relative_diff AS "Mars"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 8.703848530773663e73 AND source_sequence_index % 130 = 0
ORDER BY source_sequence_index;

-- E  Jupiter
SELECT source_sequence_index, q_relative_diff AS "Jupiter"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 2.5746024944209535e77 AND source_sequence_index % 40 = 0
ORDER BY source_sequence_index;

-- F  Saturn
SELECT source_sequence_index, q_relative_diff AS "Saturn"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 7.708609105416307e76 AND source_sequence_index % 20 = 0
ORDER BY source_sequence_index;

-- G  Uranus
SELECT source_sequence_index, q_relative_diff AS "Uranus"
FROM planetary_reception_stream
WHERE source_compton_frequency_hz = 1.1774829638745261e76 AND source_sequence_index % 10 = 0
ORDER BY source_sequence_index;

-- H  Neptune
SELECT source_sequence_index, q_relative_diff AS "Neptune"
FROM planetary_reception_stream

WHERE source_compton_frequency_hz = 1.3890706975128312e76 AND source_sequence_index % 6 = 0
ORDER BY source_sequence_index;

-- ============================================================================
-- ALL planets in one query, bounded by an EVENT-INDEX WINDOW (pivot on
-- source_sequence_index). Wide format: one named column per planet, so a single
-- Grafana XY-chart target yields all 8 series (x = source_sequence_index).
-- Adjust the window (BETWEEN lo AND hi) to zoom; keep hi <= 26352 to keep
-- Neptune present (its total return count).
-- ============================================================================
SELECT source_sequence_index,
  max(CASE WHEN source_compton_frequency_hz = 4.4774923001163785e73 THEN q_relative_diff END) AS "Mercury",
  max(CASE WHEN source_compton_frequency_hz = 6.601982728808719e74  THEN q_relative_diff END) AS "Venus",
  max(CASE WHEN source_compton_frequency_hz = 8.100606534925774e74  THEN q_relative_diff END) AS "Earth",
  max(CASE WHEN source_compton_frequency_hz = 8.703848530773663e73  THEN q_relative_diff END) AS "Mars",
  max(CASE WHEN source_compton_frequency_hz = 2.5746024944209535e77 THEN q_relative_diff END) AS "Jupiter",
  max(CASE WHEN source_compton_frequency_hz = 7.708609105416307e76  THEN q_relative_diff END) AS "Saturn",
  max(CASE WHEN source_compton_frequency_hz = 1.1774829638745261e76 THEN q_relative_diff END) AS "Uranus",
  max(CASE WHEN source_compton_frequency_hz = 1.3890706975128312e76 THEN q_relative_diff END) AS "Neptune"
FROM planetary_reception_stream
WHERE source_sequence_index BETWEEN 1 AND 5000
ORDER BY source_sequence_index;

-- ============================================================================
-- Single planet, full resolution (no decimation) - use when zoomed / for one source
-- ============================================================================


