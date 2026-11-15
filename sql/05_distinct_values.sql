-- Number of distinct values per feature (decides continuous vs. categorical treatment)
SELECT
    COUNT(DISTINCT f0) AS distinct_f0,
    COUNT(DISTINCT f1) AS distinct_f1,
    COUNT(DISTINCT f2) AS distinct_f2,
    COUNT(DISTINCT f3) AS distinct_f3,
    COUNT(DISTINCT f4) AS distinct_f4,
    COUNT(DISTINCT f5) AS distinct_f5,
    COUNT(DISTINCT f6) AS distinct_f6,
    COUNT(DISTINCT f7) AS distinct_f7,
    COUNT(DISTINCT f8) AS distinct_f8,
    COUNT(DISTINCT f9) AS distinct_f9,
    COUNT(DISTINCT f10) AS distinct_f10,
    COUNT(DISTINCT f11) AS distinct_f11
FROM criteo;
