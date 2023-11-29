with initial as
(SELECT
  id,
  _id,
  ARRAY_CONCAT_AGG(card.language) as language,
  ARRAY_CONCAT_AGG(card.tags) as tags,
  ARRAY_CONCAT_AGG(card.license) as license,
  ARRAY_AGG(DISTINCT thumbnail IGNORE NULLS) as thumbnail,
  ARRAY_CONCAT_AGG(card.datasets) as datasets,
  ARRAY_AGG(DISTINCT model_type IGNORE NULLS) as model_type,
  ARRAY_AGG(DISTINCT library_tag IGNORE NULLS) as library_tag,
  ARRAY_AGG(DISTINCT library_version IGNORE NULLS) as library_version,
  FROM staging_huggingface.raw_model
    CROSS JOIN UNNEST(cardData) as card
  GROUP BY id, _id)
SELECT
  id,
  _id,
  ARRAY((SELECT DISTINCT * FROM UNNEST(language))) as language,
  ARRAY((SELECT DISTINCT * FROM UNNEST(tags))) as tags,
  ARRAY((SELECT DISTINCT * FROM UNNEST(license))) as license,
  ARRAY((SELECT DISTINCT * FROM UNNEST(thumbnail))) as thumbnail,
  ARRAY((SELECT DISTINCT * FROM UNNEST(datasets))) as datasets,
  ARRAY((SELECT DISTINCT * FROM UNNEST(model_type))) as model_type,
  ARRAY((SELECT DISTINCT * FROM UNNEST(library_tag))) as library_tag,
  ARRAY((SELECT DISTINCT * FROM UNNEST(library_version))) as library_version,
  FROM initial