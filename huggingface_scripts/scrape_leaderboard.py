from bs4 import BeautifulSoup
import urllib.request
import re
import json
import argparse
import os

def get_page_data() -> list:
    url = "https://huggingfaceh4-open-llm-leaderboard.hf.space/?__theme=light"
    with urllib.request.urlopen(url) as url_doc:
        soup = BeautifulSoup(url_doc, 'html.parser')
        scripts = soup.find_all("script")
        for script in scripts:
            # this is the location of the relevant script data
            if "window.gradio_config" in script.text:
                json_containing_script = script.text
                json_data_locations = [m.start() for m in re.finditer(r'"data":', json_containing_script)]
                # we know from the structure of this file that the interesting data is in the second data entry
                # we also want to strip the "data" field
                json_str = json_containing_script[json_data_locations[3] + 7:]
                # the end of the data section will look like this
                # there will be multiple of these but find() will get us the first one
                end_mark = json_str.find("]]")
                # we want to add 2 back on here because we want the final two brackets
                json_str = json_str[:end_mark + 2]
                return json.loads(json_str)
    return []

def parse_leaderboard_data(leaderboard_json: list) -> list:
    all_fields = ["type_indicator", "model_website", "average", "ARC", "HellaSwag", "MMLU", "TruthfulQA",
                  "Winogrande", "GSM8K", "DROP", "type", "architecture", "precision", "hub_license",
                  "params", "hub", "available_on_hub", "sha", "id"]
    leaderboard = []
    for elem in leaderboard_json:
        json_elem = {all_fields[i]: value for i, value in enumerate(elem)}
        try:
            soup = BeautifulSoup(json_elem["model_website"], 'html.parser')
            json_elem["model_website"] = soup.a["href"]
        except:
            pass
        # for some reason some of the hub licenses are single-element lists
        if type(json_elem["hub_license"]) == list:
            json_elem["hub_license"] = json_elem["hub_license"][0]
        leaderboard.append(json_elem)
    return leaderboard

def write_result(leaderboard: list, filename: str) -> None:
    out = open(filename, "w")
    for entry in leaderboard:
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
    out.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", type=str,
                        help="A directory for writing the leaderboard data")
    args = parser.parse_args()
    leaderboard_page_data = get_page_data()
    leaderboard_data = parse_leaderboard_data(leaderboard_page_data)
    write_result(leaderboard_data, os.path.join(args.out_dir, "leaderboard.jsonl"))