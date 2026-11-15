WITH mirror AS (
    SELECT
        x.cmd_code,
        x.period,
        x.reporter_code  AS exporter,
        x.partner_code   AS importer,
        x.primary_value  AS export_fob,
        m.primary_value  AS import_cif,
        m.primary_value - x.primary_value AS gap_usd,
        ROUND(100.0 * (m.primary_value - x.primary_value) / NULLIF(x.primary_value, 0), 1) AS gap_pct
    FROM trade_flows AS x
    LEFT JOIN trade_flows AS m
        ON  m.reporter_code = x.partner_code
        AND m.partner_code  = x.reporter_code
        AND m.cmd_code      = x.cmd_code
        AND m.period        = x.period
        AND m.flow_code     = 'M'
    WHERE x.flow_code = 'X'
)
SELECT *
FROM mirror
ORDER BY ABS(gap_pct) DESC NULLS FIRST;