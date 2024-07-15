# Querying for null json columns

In Postgresql a json column can contain SQL `NULL` and the JSON `null`. 

A simple `WHERE json_column IS NOT NULL` will not filter out rows where the column contains the JSON value `null`.

The way to filter out these values is thus:
```sql
SELECT *
FROM some_table
WHERE json_column IS NOT NULL and json_column::text <> 'null'
```