-- We're getting a small number of duplicate rows
-- I can't figure out how to eliminate them in the main code
-- I'm using the ids as keys to dicts; they shouldn't exist
-- So we just remove them here
SELECT * EXCEPT (row_val) from
(
  SELECT
  *,
  ROW_NUMBER() OVER (PARTITION BY id) row_val
FROM
  staging_huggingface.raw_model
)
where row_val=1
