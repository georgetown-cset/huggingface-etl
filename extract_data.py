import urllib.request, json, re
import json
from collections import OrderedDict

def get_model_ids():
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

def get_model_data(models):
    info_dict = {}
    missed_list = []
    top_level_fields = OrderedDict()
    for i, model in enumerate(models):
        try:
            with urllib.request.urlopen(f"https://huggingface.co/api/models/{model['id']}") as url:
                data = json.load(url)
                info_dict[model["id"]] = data
                print(i, model["id"])
            for field in model:
                if field not in top_level_fields:
                    top_level_fields[field] = None
        except:
            missed_list.append(model["id"])
    return info_dict, missed_list, top_level_fields

def save_results(data, filename):
    out = open(filename, "w")
    for entry in data:
        out.write(json.dumps(data[entry], ensure_ascii=False) + "\n")
    out.close()

def save_missed(missed, filename):
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