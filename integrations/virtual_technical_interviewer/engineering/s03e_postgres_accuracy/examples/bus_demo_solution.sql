WITH running AS (
    SELECT person_name, turn, SUM(weight) OVER (ORDER BY turn) AS accumulated
    FROM Queue
)
SELECT person_name
FROM running
WHERE accumulated <= 1000
ORDER BY turn DESC
LIMIT 1;
