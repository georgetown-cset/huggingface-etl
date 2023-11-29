-- We're getting a small number of duplicate rows
-- I can't figure out how to eliminate them in the main code
-- I'm using the ids as keys to dicts; they shouldn't exist
-- So we just remove them here
SELECT * from
(
  SELECT
  *,
  ROW_NUMBER() OVER (PARTITION BY id) row_num
FROM
  staging_huggingface.raw_model
)
where row_num=1
