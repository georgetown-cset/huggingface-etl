WITH
  has_tensor_type AS (
  SELECT
    id,
    _id,
    safetensors.total AS total_params,
    IF(safetensors.parameters.F64 IS NOT NULL, "F64", NULL) AS f64,
    IF(safetensors.parameters.F32 IS NOT NULL, "F32", NULL) AS f32,
    IF(safetensors.parameters.F16 IS NOT NULL, "F16", NULL) AS f16,
    IF(safetensors.parameters.I64 IS NOT NULL, "I64", NULL) AS i64,
    IF(safetensors.parameters.I32 IS NOT NULL, "I32", NULL) AS i32,
    IF(safetensors.parameters.I16 IS NOT NULL, "I16", NULL) AS i16,
    IF(safetensors.parameters.I8 IS NOT NULL, "I8", NULL) AS i8,
    IF(safetensors.parameters.BF16 IS NOT NULL, "BF16", NULL) AS bf16,
    IF(safetensors.parameters.U8 IS NOT NULL, "U8", NULL) AS u8,
    IF(safetensors.parameters.U16 IS NOT NULL, "U16", NULL) AS u16,
    IF(safetensors.parameters.U32 IS NOT NULL, "U16", NULL) AS u32,
    IF(safetensors.parameters.Q4 IS NOT NULL, "Q4", NULL) AS q4,
    IF(safetensors.parameters.bool IS NOT NULL, "BOOL", NULL) AS bool_tens,
    safetensors.parameters.F64 as F64_params,
    safetensors.parameters.F32 as F32_params,
    safetensors.parameters.F16 as F16_params,
    safetensors.parameters.I64 as I64_params,
    safetensors.parameters.I32 as I32_params,
    safetensors.parameters.I16 as I16_params,
    safetensors.parameters.I8 as I8_params,
    safetensors.parameters.BF16 as BF16_params,
    safetensors.parameters.U8 as U8_params,
    safetensors.parameters.U16 as U16_params,
    safetensors.parameters.U32 as U32_params,
    safetensors.parameters.Q4 as Q4_params,
    safetensors.parameters.bool as BOOL_params
  FROM
    staging_huggingface.raw_model)
SELECT
  id,
  _id,
  total_params,
  ARRAY_AGG(tensors IGNORE NULLS) AS tensor_types,
  F64_params,
  F32_params,
  F16_params,
  I64_params,
  I32_params,
  I16_params,
  I8_params,
  BF16_params,
  U8_params,
  U16_params,
  U32_params,
  Q4_params,
  BOOL_params
FROM
  has_tensor_type
LEFT JOIN
  UNNEST ([f64, f32, f16, i64, i32, i16, i8, bf16, u8, u16, u32, q4, bool_tens]) tensors
GROUP BY
  id,
  _id,
  total_params,
  F64_params,
  F32_params,
  F16_params,
  I64_params,
  I32_params,
  I16_params,
  I8_params,
  BF16_params,
  U8_params,
  U16_params,
  U32_params,
  Q4_params,
  BOOL_params