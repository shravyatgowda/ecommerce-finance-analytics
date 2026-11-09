-- COD reconciliation: carrier remittance report vs internal order book (SQLite / ANSI-friendly)
WITH joined AS (
    SELECT
        o.order_id,
        o.carrier,
        o.internal_status,
        c.carrier_status,
        c.cod_collected,
        c.cod_remitted,
        CASE
            WHEN o.internal_status = 'RTO' AND c.carrier_status = 'DELIVERED' THEN 'RTO_STATUS_MISMATCH'
            WHEN c.carrier_status = 'DELIVERED' AND c.cod_remitted < c.cod_collected THEN 'SHORT_REMITTANCE'
            ELSE 'MATCHED'
        END AS issue
    FROM orders o
    JOIN carrier_cod_report c ON c.order_id = o.order_id
)
SELECT
    issue,
    COUNT(*)                                    AS orders,
    ROUND(SUM(cod_collected - cod_remitted), 0) AS leakage_amount
FROM joined
WHERE issue <> 'MATCHED'
GROUP BY issue;
