SELECT
  COUNT(_id) = COUNT(DISTINCT _id)
FROM
  staging_huggingface.raw_model