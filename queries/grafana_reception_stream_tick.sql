-- Planetary reception stream on the real index `tick`
-- Datasource: QuestDB plugin (uid 2Bi8EToVz)  ·  Table: planetary_reception_stream
--
-- tick = 1, 2, 3, ...  (+1 at each step, one echo per tick, chronological).
-- One row per tick: value q_relative_diff, tagged by source_compton_frequency_hz.
-- Panel: XY Chart, x = tick, y = q_relative_diff.
-- Color: Grafana transform "Partition by values" on source_compton_frequency_hz
--        (splits into one colored, legended series per planet).

SELECT tick, q_relative_diff, source_compton_frequency_hz
FROM planetary_reception_stream
WHERE tick BETWEEN 1 AND 100000
ORDER BY tick;
