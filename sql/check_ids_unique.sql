SELECT
  COUNT(id) = COUNT(DISTINCT id)
FROM
  staging_huggingface.raw_model