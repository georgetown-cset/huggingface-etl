import urllib.request, json, re
import json
from collections import OrderedDict

def get_model_ids() -> list:
    """
    Run initial API pull to get the ids for every model.
    Must use paging to iterate through the list of models.
    :return: A list of the urls of every individual model
    """
    next_pattern = r'(<)([\S]+)(>; rel="next")'
    done = False
    cur_url = "https://huggingface.co/api/models"
    all_data = []
    while not done:
        with urllib.request.urlopen(cur_url) as url:
            data = json.load(url)
            all_data.extend(data)
            link = url.getheader("link")
            if link and 'rel="next"' in link:
                cur_url = re.findall(next_pattern, link)[0][1]
            else:
                done = True
    return all_data

def get_model_data(models: list) -> tuple[dict, list]:
    """
    Go through each model and do an API call to get the model's data.
    Add the data to our data dictionary.
    If the call fails, add the model to our missed list.
    :param models: The list of model urls
    :return: The dict of model info and the list of missed models
    """
    info_dict = {}
    missed_list = []
    for i, model in enumerate(models):
        try:
            with urllib.request.urlopen(f"https://huggingface.co/api/models/{model['id']}") as url:
                data = json.load(url)
                info_dict[model["id"]] = data
                print(i, model["id"])
        except:
            missed_list.append(model["id"])
    return info_dict, missed_list

def save_results(data: dict, filename: str) -> None:
    """
    Save the model info
    :param data: The dict of model info
    :param filename: The filename to save data to
    :return: None
    """
    out = open(filename, "w")
    for entry in data:
        out.write(json.dumps(data[entry], ensure_ascii=False) + "\n")
    out.close()

def save_missed(missed: list, filename: str) -> None:
    """
    Save the list of missed models
    :param missed: The list of missed models
    :param filename: The filename to save missed models to
    :return: None
    """
    out = open(filename, "w")
    for entry in missed:
        out.write(json.dumps({"missed": entry}) + "\n")
    out.close()

if __name__ == "__main__":
    all_models = get_model_ids()
    output, missed_data, top_level = get_model_data(all_models)
    save_results(output, "data/models.jsonl")
    save_missed(missed_data, "data/missed.jsonl")
    out = open("data/top_level.txt", "w")
    for entry in top_level:
        out.write(f"{entry}\n")
    out.close()