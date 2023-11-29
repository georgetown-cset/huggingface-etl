SELECT
  DISTINCT
  id,
  _id,
  dataset.name as dataset,
  dataset.type as dataset_type,
  dataset.config,
  dataset.split as dataset_split,
  dataset.revision,
  dataset.args
  FROM staging_huggingface.raw_model
    CROSS JOIN UNNEST(cardData) as card
    CROSS JOIN UNNEST((card.model_index)) as mod_index
    CROSS JOIN UNNEST(mod_index.results) as result
    CROSS JOIN UNNEST(result.datasets) as dataset
UNION DISTINCT
SELECT
  DISTINCT
  id,
  _id,
  dataset.name as dataset,
  dataset.type as dataset_type,
  dataset.config,
  dataset.split as dataset_split,
  dataset.revision,
  dataset.args
  FROM staging_huggingface.raw_model
  CROSS JOIN UNNEST(raw_model.model_index) as mod_index
  CROSS JOIN UNNEST(mod_index.results) as result
  CROSS JOIN UNNEST(result.datasets) as dataset
ORDER BY id