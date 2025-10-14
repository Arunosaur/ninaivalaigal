# SPEC Dashboard - Active Work

```dataview
TABLE id, title, phase, status
FROM "specs"
WHERE status != "Complete"
SORT phase asc
```

## Dependencies View

```dataview
TABLE depends_on as "Depends On", length(depends_on) as "Dep Count"
FROM "specs"
WHERE length(depends_on) > 0
SORT length(depends_on) desc
```

## Phase Progress

```dataview
TABLE phase AS "Phase", length(rows) AS "Count"
FROM "specs"
GROUP BY phase
SORT phase asc
```

## Status Breakdown

```dataview
TABLE status AS "Status", length(rows) AS "Count"
FROM "specs"
GROUP BY status
SORT status asc
```
