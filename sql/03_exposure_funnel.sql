-- Intention-to-treat vs. exposure: outcome rates by (treatment, exposure).
-- Exposure is NOT randomized (it depends on winning an ad auction), so comparing
-- exposed treated users with controls mixes the ad's effect with selection.
SELECT
    treatment,
    exposure,
    COUNT(*)                          AS n,
    AVG(CAST(visit AS DOUBLE))        AS visit_rate,
    AVG(CAST(conversion AS DOUBLE))   AS conversion_rate
FROM criteo
GROUP BY treatment, exposure
ORDER BY treatment, exposure;
