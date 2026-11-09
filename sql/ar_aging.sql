-- Accounts receivable aging with 30/60/90-day buckets (as of 2025-06-30)
WITH aged AS (
    SELECT
        invoice_id,
        customer,
        invoice_amount - amount_paid AS outstanding,
        CAST(julianday('2025-06-30') - julianday(due_date) AS INTEGER) AS days_overdue
    FROM ar_invoices
    WHERE invoice_amount - amount_paid > 0
)
SELECT
    CASE
        WHEN days_overdue <= 0  THEN '0 Current'
        WHEN days_overdue <= 30 THEN '1 1-30 days'
        WHEN days_overdue <= 60 THEN '2 31-60 days'
        WHEN days_overdue <= 90 THEN '3 61-90 days'
        ELSE '4 90+ days'
    END AS bucket,
    COUNT(*)                   AS invoices,
    ROUND(SUM(outstanding), 0) AS outstanding
FROM aged
GROUP BY bucket
ORDER BY bucket;
