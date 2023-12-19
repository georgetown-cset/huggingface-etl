SELECT
  DISTINCT
  id,
  _id,
  metric.name as metric,
  metric.type as type,
  metric.value as value
  FROM staging_huggingface.raw_model
    CROSS JOIN UNNEST(cardData) as card
    CROSS JOIN UNNEST((card.model_index)) as mod_index
    CROSS JOIN UNNEST(mod_index.results) as result
    CROSS JOIN UNNEST(result.metrics) as metric
UNION DISTINCT
SELECT
  DISTINCT
  id,
  _id,
  metric.name as metric,
  metric.type as type,
  metric.value as value
  FROM staging_huggingface.raw_model
  CROSS JOIN UNNEST(raw_model.model_index) as mod_index
  CROSS JOIN UNNEST(mod_index.results) as result
  CROSS JOIN UNNEST(result.metrics) as metric
ORDER BY id