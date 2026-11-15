-- Per-arm feature means and second moments (for standardized mean differences)
SELECT
    treatment,
    AVG(CAST(f0 AS DOUBLE)) AS mean_f0,
    AVG(CAST(f0 AS DOUBLE) * CAST(f0 AS DOUBLE)) AS sq_f0,
    AVG(CAST(f1 AS DOUBLE)) AS mean_f1,
    AVG(CAST(f1 AS DOUBLE) * CAST(f1 AS DOUBLE)) AS sq_f1,
    AVG(CAST(f2 AS DOUBLE)) AS mean_f2,
    AVG(CAST(f2 AS DOUBLE) * CAST(f2 AS DOUBLE)) AS sq_f2,
    AVG(CAST(f3 AS DOUBLE)) AS mean_f3,
    AVG(CAST(f3 AS DOUBLE) * CAST(f3 AS DOUBLE)) AS sq_f3,
    AVG(CAST(f4 AS DOUBLE)) AS mean_f4,
    AVG(CAST(f4 AS DOUBLE) * CAST(f4 AS DOUBLE)) AS sq_f4,
    AVG(CAST(f5 AS DOUBLE)) AS mean_f5,
    AVG(CAST(f5 AS DOUBLE) * CAST(f5 AS DOUBLE)) AS sq_f5,
    AVG(CAST(f6 AS DOUBLE)) AS mean_f6,
    AVG(CAST(f6 AS DOUBLE) * CAST(f6 AS DOUBLE)) AS sq_f6,
    AVG(CAST(f7 AS DOUBLE)) AS mean_f7,
    AVG(CAST(f7 AS DOUBLE) * CAST(f7 AS DOUBLE)) AS sq_f7,
    AVG(CAST(f8 AS DOUBLE)) AS mean_f8,
    AVG(CAST(f8 AS DOUBLE) * CAST(f8 AS DOUBLE)) AS sq_f8,
    AVG(CAST(f9 AS DOUBLE)) AS mean_f9,
    AVG(CAST(f9 AS DOUBLE) * CAST(f9 AS DOUBLE)) AS sq_f9,
    AVG(CAST(f10 AS DOUBLE)) AS mean_f10,
    AVG(CAST(f10 AS DOUBLE) * CAST(f10 AS DOUBLE)) AS sq_f10,
    AVG(CAST(f11 AS DOUBLE)) AS mean_f11,
    AVG(CAST(f11 AS DOUBLE) * CAST(f11 AS DOUBLE)) AS sq_f11
FROM criteo
GROUP BY treatment
ORDER BY treatment;
