SELECT
  DISTINCT
  id,
  _id,
  result.task.name as task,
  result.task.type as task_type,
  result.task.args,
  result.task.metrics
  FROM staging_huggingface.raw_model
    CROSS JOIN UNNEST(cardData) as card
    CROSS JOIN UNNEST((card.model_index)) as mod_index
    CROSS JOIN UNNEST(mod_index.results) as result
UNION DISTINCT
SELECT
  DISTINCT
  id,
  _id,
  result.task.name as task,
  result.task.type as task_type,
  result.task.args,
  STRING(NULL) as metrics
  FROM staging_huggingface.raw_model
  CROSS JOIN UNNEST(raw_model.model_index) as mod_index
  CROSS JOIN UNNEST(mod_index.results) as result