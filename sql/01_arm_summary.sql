-- Arm sizes and outcome rates (randomized variable: treatment)
SELECT
    treatment,
    COUNT(*)                                  AS n,
    AVG(CAST(visit AS DOUBLE))                AS visit_rate,
    AVG(CAST(conversion AS DOUBLE))           AS conversion_rate,
    AVG(CAST(exposure AS DOUBLE))             AS exposure_rate
FROM criteo
GROUP BY treatment
ORDER BY treatment;
