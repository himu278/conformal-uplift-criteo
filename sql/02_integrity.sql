-- Logical checks that must hold in the released data
SELECT
    COUNT(*)                                                         AS n_rows,
    SUM(CASE WHEN conversion = 1 AND visit = 0 THEN 1 ELSE 0 END)    AS conversion_without_visit,
    SUM(CASE WHEN treatment = 0 AND exposure = 1 THEN 1 ELSE 0 END)  AS exposed_controls,
    SUM(CASE WHEN treatment NOT IN (0, 1) OR visit NOT IN (0, 1)
              OR conversion NOT IN (0, 1) OR exposure NOT IN (0, 1)
             THEN 1 ELSE 0 END)                                      AS non_binary_labels
FROM criteo;
