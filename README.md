# huggingface-etl

This repository is designed to scrape data from Hugging Face's API, specifically about Hugging Face models.

Some relevant notes here:

1. Some models are missing in this process; the missed models appear to be those that require sharing your contact information in order to access the model, which is not supported in querying the API. This is a small percentage of models, and they are all catalogued in [missed.jsonl](data/missed.jsonl).
2. Significant portions of the data queries is user-defined, particularly things like the model index, the model card data, the mask token, and possibly the config. As a result, these fields do not have consistent formatting, and even sometimes have completely broken formatting (to the extent that if you view the corresponding model page on the Hugging Face website it will not display the model card info at all). To handle these broken fields, we are doing a lot of post-hoc cleaning, but beyond a certain point we're also just dumping the broken fields into strings and leaving it to be read if there's interest. This choice has been made because if we tried to account for every possible error type and scenario we'd likely have to update the code every time we re-ran, and we want something durable rather than brittle.
3. Given how inconsistent typing is in this json, and how often we're having to correct it, we're not using python function typing even though we'd prefer it.


# Deployment

To refresh the docker container (which you must do if you change any of the python scripts), run

```
docker build -t huggingface .
docker tag huggingface us.gcr.io/gcp-cset-projects/huggingface
docker push us.gcr.io/gcp-cset-projects/huggingface
```