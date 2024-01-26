import json
import copy
from datetime import datetime
import argparse
import os

SUBFIELDS = set()

def stringify(element):
    return json.dumps(element) if type(element) == dict else f"{element}"

def fix_repeateds(data):
    """
    The goal of this function is to fix instances where there are two versions of a field in the json,
    one that is a nullable and the other that is a repeated. We'd like to make them all compatible
    with the repeated version.
    :param data: A field that could be either a list or not
    :return: fixed field as list
    """
    if type(data) != list:
        if not data:
            return []
        if type(data) == dict:
            return [stringify(data)]
        return [data]
    new_data = []
    for element in data:
        if element:
            # just stick the json in if we have even more records inside because they're not worth dealing with
            # they're usually extremely model-specific at this point and we no long want to specify, like
            # specific names of datasets as the keys
            if type(element) == dict:
                new_data.append(stringify(element))
            else:
                new_data.append(element)
    return new_data

def fix_records(data, record_label: str, repeated = False):
    """
    The goal of this function is to fix instances where there are two versions of a field in the json,
    one that is a repeated and the other that is a repeated record. We'd like to make them all compatible
    with the record version.
    :param data: The field to fix
    :param record_label: What field name to given the new record
    :param repeated: If we want the inner data to be a repeated inside of the record
    :return: The fixed instance as a repeated record
    """
    if type(data) == list and len(data) > 0 and type(data[0]) == str:
        if repeated:
            return [{record_label: [i]} for i in data]
        return [{record_label: i} for i in data]
    return data

def fix_model_index(data):
    """
    The goal of this function is to fix various bits of weirdness in the model index.
    :param data: The model index, either solo or from the card_data
    :return: The fixed model_index
    """
    if not data:
        return data
    results_fields = ["task", "tasks", "dataset", "datasets", "metric", "metrics", "values"]
    new_data = []
    if type(data) == dict:
        data = [data]
    for elem in data:
        new_elem = copy.deepcopy(elem)
        if "name" in elem and type(elem) == dict:
            if type(elem["name"]) == dict:
                # here we're testing for a case where the there's technically a dict under name
                # but the dict looks like {"some field": null} (which happens surprisingly
                # often). We just want to replace this with {"name": "some field"}
                if len(elem["name"]) == 1 and not list(elem["name"].values())[0]:
                    new_elem["name"] = list(elem["name"].keys())[0]
                else:
                    new_elem["name"] = stringify(elem['name'])
        if "datasets" in elem and not elem.get("results"):
            new_elem["results"] = {"datasets": fix_result_datasets(elem["datasets"])}
            del new_elem["datasets"]
        elif "results" in elem:
            if len(elem["results"]) > 0 and type(elem["results"][0]) != dict:
                new_elem["results"] = {"values": elem["results"]}
            else:
                new_vals = []
                for val in elem["results"]:
                    new_val = copy.deepcopy(val)
                    if "dataset" in val:
                        new_val["datasets"] = fix_result_datasets([val["dataset"]])
                        del new_val["dataset"]
                    if "datasets" in val:
                        new_val["datasets"] = fix_result_datasets(val["datasets"])
                    if "metrics" in val:
                        new_val["metrics"] = fix_result_metrics(val["metrics"])
                    if "metric" in val:
                        if type(val["metric"]) == dict:
                            new_val["metrics"] = fix_result_metrics([val["metric"]])
                            del new_val["metric"]
                        else:
                            new_val["metrics"] = fix_result_metrics(val["metric"])
                    if "tasks" in val:
                        new_val["task"] = val["tasks"]
                        if "metrics" in new_val["task"]:
                            new_val["task"]["metrics"] = stringify(new_val['task']['metrics'])
                        del new_val["tasks"]
                    extra_fields = [i for i in val if i not in results_fields]
                    if extra_fields:
                        results_params = []
                        for field_name in extra_fields:
                            results_params.append({"name": field_name, "val": stringify(new_val[field_name])})
                            del new_val[field_name]
                        new_val["params"] = results_params
                    new_vals.append(new_val)
                new_elem["results"] = new_vals
        new_data.append(new_elem)
    return new_data

def fix_result_datasets(datasets):
    """
    Fix the datasets field inside of results inside of model_index
    :param datasets: The datasets field, which should be a repeated (list)
    :return: The fixed datasets field
    """
    for dataset in datasets:
        # if we have strings instead of records in our datasets, shortcut this whole thing
        # and just return a new version with records
        if type(dataset) == str:
            return [{"name" : dataset} for dataset in datasets]
        if "args" in dataset:
            if type(dataset["args"]) == dict:
                if len(dataset["args"]) == 1:
                    dataset["args"] = [i for i in dataset["args"].values()][0]
                else:
                    dataset["args"] = stringify(dataset['args'])
    return datasets

def fix_result_metrics(metrics):
    """
    Fix the metrics field inside of results inside of model_index
    :param metrics: The metrics field, which should be a repeated (list)
    :return: The fixed metrics field
    """
    plurals = {"types": "type",
               "values": "value"}
    for metric in metrics:
        if "value" in metric:
            if type(metric["value"]) == list:
                if len(metric["value"]) == 0:
                    metric["value"] = None
                elif len(metric["value"]) == 1:
                    metric["value"] = metric["value"][0]
            elif type(metric["value"]) == dict:
                metric["value"] = stringify(metric['value'])
        if "args" in metric:
            if type(metric["args"]) == dict:
                metric["args"] = [json.dumps(i) if type(i) == dict else f"{i} : {j}" for i, j in metric["args"].items()]
            elif type(metric["args"]) == list:
                for i, arg in enumerate(metric["args"]):
                    if type(arg) == dict:
                        # Just convert these very specific arguments that occur very rarely into a string
                        metric["args"][i] = stringify(arg)
            else:
                metric["args"] = [metric["args"]]
        # we only want one of the singular or plural field, in this case the singular
        for field_name in plurals:
            if field_name in metric:
                if plurals[field_name] not in metric:
                    metric[plurals[field_name]] = ", ".join([stringify(elm) for elm in metric[field_name]])
                del metric[field_name]
    return metrics

def read_tag_data(tag_file):
    tag_dict = {}
    with open(tag_file, "r") as f:
        for i, line in enumerate(f):
            tag_info = json.loads(line)
            tag_dict[tag_info["id"]] = tag_info
            if not "subType" in tag_info:
                tag_dict[tag_info["id"]]["subType"] = None
    return tag_dict

def interpret_tags(tag_dict, tags):
    tag_list = []
    for tag in tags:
        if tag in tag_dict:
            tag_list.append(tag_dict[tag])
    return tag_list

def fix_nullable_record(data, record_label):
    """
    The goal of this function is to handle cases where there are two versions of a field, one that is a nullable
    and the other that is a nullable record. We want the nullable record, here.
    :param data: The data that could be either a nullable or a nullable record.
    :param record_label: The label for the new record field
    :return: The fixed nullable record
    """
    if type(data) != list and type(data) != dict:
        return {record_label: data}
    return data

def fix_metrics(data):
    """
    The metrics field in cardData (rather than in model-index inside cardData) is usually a single value or a list of
    values. However, sometimes it's a record of values of various types. We have to normalize this to the most
    complex form, the record.
    Also sometimes the metric's name is a problem and we have to fix that.
    :param data: The metrics field within cardData
    :return: The fixed metrics field within cardData
    """
    core_fields = {"name", "value", "type"}
    # if the field is empty, return a repeated of records
    if not data:
        return []
    # if we have a single value (string/float/int etc.) convert to a repeated record
    if type(data) != list and type(data) != dict:
        if type(data) == str:
            return [{"name": data}]
        else:
            return [{"value": data}]
    if type(data) == list:
        # if there's just a string or int or float sitting in the first element in metrics
        if type(data[0]) != dict:
            new_data = [{"name" if type(data[0]) == str else "value": stringify(element)}
                        for element in data if element]
        else:
            # normalize some of the names so they're more consistent
            temp_new_data = [{"_".join(i.split()).replace("F-1_score", "f1").lower(): stringify(j)
                              for i, j in element.items()} for element in data ]
            new_data = [{i: stringify(j) for i, j in element.items()} for element in temp_new_data
                                if element.keys() - core_fields == set()]
            other_part = [{"name": i, "value": stringify(j)} for element
                           in temp_new_data for i, j in element.items() if i not in core_fields]
            new_data.extend(other_part)
        return new_data
    return data

def fix_widget_data(data):
    """
    Fix the widgetData field or widget field
    :param data: either the widgetData or widget. Should be a repeated record (list) but isn't always.
    :return: The fixed widget or widgetData
    """
    # We do all this copy nonsense and enumerate stuff because we don't want to extend the list
    # while we are iterating through it!
    if type(data) == dict:
        data = [data]
    elif type(data) != list:
        data = [{"text": [data]}]
        return data
    new_data = copy.deepcopy(data)
    core_field_names = ["text", "context", "src", "example_title", "candidate_labels", "sentences", "source_sentence"]
    for i, entry in enumerate(data):
        if type(entry) != dict:
            new_data[i] = {"text": [entry]}
            break
        if "text" in entry:
            if entry["text"] and type(entry["text"]) != list:
                new_data[i]["text"] = [entry["text"]]
            if not entry["text"]:
                new_data[i]["text"] = []
        for field_name in ["example_title", "candidate_labels"]:
            if field_name in entry:
                if type(entry[field_name]) == list:
                    # if for some reason we're stuck with a list
                    # just throw all the entries together in a string
                    # making sure the list actually contains strings first
                    new_data[i][field_name] = ", ".join([stringify(elm) for elm in entry[field_name]])
        params = []
        for field in entry:
            if field not in core_field_names:
                param = {"name": field, "value": stringify(entry[field])}
                params.append(param)
                del new_data[i][field]
        if params:
            new_data[i]["params"] = params
    return new_data

def clean_config(data):
    """
    The config field is a mess of user-defined fields. We need to clean this up if we want to include it.
    :param data: The config repeated record (a list)
    :return: The fixed config
    """
    # If config exists but it's empty, leave it
    if not data:
        return data
    new_data = copy.deepcopy(data)
    handled_config_fields = ["architectures", "model_type", "task_specific_params", "adapter_transformers",
                             "speechbrain", "auto_map", "diffusers", "sklearn"]
    external_params = []
    for field in data:
        if field == "architectures" and data[field] and type(data[field]) != list:
            if "value" in data[field] and type(data[field]["value"]) == list:
                new_data[field] = data[field]["value"]
            else:
                # we just don't care that much about architectures
                # most of them are formatted correctly or are misformatted as above
                # if any are misformatted in a new way
                # we're not letting a few rows that are badly formatted crash us
                new_data[field] = []
        if field == "model_type" and data[field]:
            if type(data[field]) == list:
                if len(data[field]) == 1:
                    new_data[field] = new_data[field][0]
                else:
                    # this has never happened but just in case
                    new_data[field] = ", ".join([stringify(i) for i in new_data[field]])
            elif type(data[field]) == dict:
                if "value" in data[field]:
                    new_data[field] = stringify(data[field]["value"])
                else:
                    new_data[field] = stringify(data[field])
        if field == "auto_map" and data[field]:
            subfields = []
            for subfield in data[field]:
                # For some reason there are a few of these with values of lists not strings with
                # lists that contain only 2 elements and the second element is None
                if type(data[field][subfield]) == list and len(data[field][subfield]) == 2:
                    if not data[field][subfield][1]:
                        new_data[field][subfield] = data[field][subfield][0]
                updated = {"name": subfield, "value": stringify(new_data[field][subfield])}
                subfields.append(updated)
            new_data[field] = subfields
        if field == "sklearn" and data[field]:
            known_subfields = ["filename", "columns", "environment", "example_input",
                               "model", "task", "use_intelex", "model_format"]
            for subfield in data[field]:
                if subfield in known_subfields:
                    new_data[field][subfield] = stringify(data[field][subfield])
                elif subfield not in known_subfields:
                    # We've never seen this so if this happens it happens so
                    # rarely the data is irrelevant and we don't care
                    del new_data[field][subfield]
        if field == "diffusers" and data[field]:
            for subfield in data[field]:
                if "class_name" == subfield:
                    new_data[field][subfield] = stringify(data[field][subfield])
                else:
                    # We've never seen this so if this happens it happens so
                    # rarely the data is irrelevant and we don't care
                    del new_data[field][subfield]
        # Then go through the task specific parameters to deal with their nonsense
        if "task" in field and "specific" in field and data[field]:
            # If the task specific parameters aren't a dictionary of parameters
            # Then just throw their name in a dict and leave it
            if type(data[field]) != dict:
                new_data[field] = {"name" : new_data[field]}
                return new_data
            # Otherwise we want to find each task specific params and add it to our list of subtasks
            # Our goal here is to transform the task specific parameters from a nullable record where each
            # key is a different task type, which is unmaintainable (there's too many task types possible)
            # to a repeated record with a "name" key whose value is the task type
            subtasks = []
            for subtask in data[field]:
                # Some of the task specific params are whole sets of params and others are single params
                # The sets of params show up in dicts, while the single params show up as immediate values
                # linked to the name of the task specific param
                # if we have the latter, we want to transform it so it is the value of "value" at the same
                # level as the "name" value
                if type(new_data[field][subtask]) != dict:
                    if type(new_data[field][subtask]) != list:
                        new_params = {"name": subtask.replace("-", "_"),
                                   "value": new_data[field][subtask]}
                        subtasks.append(new_params)
                    else:
                        # There's theoretically the possibility we could end up with a task specific param that
                        # is a list instead of a dict or a 'flat' val (e.g. int/float/string/boolean).
                        # This would mess things up so we want to know if it's happening.
                        new_params = {"name": subtask.replace("-", "_"),
                                      "value": ", ".join([stringify(i) for i in new_data[field][subtask]])}
                        subtasks.append(new_params)
                else:
                    # If the task specific parameters are a dict, we need to handle these as well
                    # These are also user-defined fields, so we need to turn their names into values instead of keys
                    # We do this by creating a repeated "params" field with two elements in it:
                    # "name" (for the parameter name) and "value" (for its value).
                    params = []
                    for param_name in data[field][subtask]:
                        params.append({"name": param_name,
                                       "value": f'{new_data[field][subtask][param_name]}'})
                        del new_data[field][subtask][param_name]
                    if params:
                        new_data[field][subtask]["params"] = params
                    new_data[field][subtask]["name"] = subtask.replace("-", "_")
                    subtasks.append(new_data[field][subtask])
                del new_data[field][subtask]
            new_data[field] = subtasks
        if field not in handled_config_fields:
            external_params.append({"name": field, "val": stringify(data[field])})
            del new_data[field]
    if external_params:
        new_data["params"] = external_params
    return new_data

def clean_carddata_base_fields(card_data):
    """
    There are way too many possibilities for cardData base fields, and there's a reasonable
    chance that even if I try to enumerate all of them more will be added (given that there are
    some entries that appear to just have an entirely different set of base fields than everything else)
    So instead of dealing with this, we're going to dump everything outside of our "core" base fields
    into some pre-configured fields
    :param card_data: The cardData; should be a repeated record (a list)
    :return: The fixed cardData
    """
    core_fields = ["language", "tags", "license", "thumbnail", "pipeline_tag", "datasets", "metrics",
                   "widget", "model_index", "co2_eq_emissions", "model_type", "library_tag", "library_version"]
    string_core = ["thumbnail", "model_type", "library_tag", "library_version"]
    co2_fields = ["emissions", "source", "geographical_location", "hardware_used", "on_cloud", "training_type",
                  "cpu_model", "gpu_model", "ram_total_size", "hours_used"]
    new_card_data = copy.deepcopy(card_data)
    singulars = {"tag": "tags",
                 "dataset": "datasets"}
    additional_fields = []
    for index, field in enumerate(card_data):
        if type(field) == str and field in singulars:
            if singulars[field] not in card_data:
                if type(card_data[field]) == str:
                    new_card_data[singulars[field]] = [card_data[field]]
                elif type(card_data[field]) == list:
                    # Ensure everything in the list is a string
                    new_card_data[singulars[field]] = [stringify(i) for i in card_data[field]]
            # We're going to delete the singular version whether or not we copy it into the plural
            # Currently we don't think there are cases where both exist but even if there were
            # We don't think it's likely we'd need them both
            del new_card_data[field]
        # We check if it's a string because sometimes we may have a repeated, not just a record
        # These cases are rare but are already handled in the schema
        elif field not in core_fields and type(field) == str:
            field_data = {"name": field, "value": stringify(card_data[field])}
            additional_fields.append(field_data)
            del new_card_data[field]
        if field in string_core:
            new_card_data[field] = stringify(card_data[field])
    if additional_fields:
        new_card_data["params"] = additional_fields
    return new_card_data

def fix_co2(co2_field):
    co2_subfields = ["emissions", "source", "geographical_location", "hardware_used", "on_cloud", "training_type",
                  "cpu_model", "gpu_model", "ram_total_size", "hours_used"]
    params = []
    subfields_to_remove = []
    for subfield in co2_field:
        if subfield not in co2_subfields:
            data = {"name": subfield, "value": co2_field[subfield]}
            params.append(data)
            subfields_to_remove.append(subfield)
    if params:
        co2_field["params"] = params
        for subfield_to_remove in subfields_to_remove:
            del co2_field[subfield_to_remove]
    return co2_field


def fix_data(filename, tag_dict):
    """
    The primary function for cleaning all the data
    :param filename: The filename containing the data to clean
    :return: The output data
    """
    output = []
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            result = json.loads(line)
            # print(i, result["id"])
            newline = copy.deepcopy(result)
            if "model-index" in newline:
                newline["model_index"] = fix_model_index(newline["model-index"])
                del newline["model-index"]
            if "widgetData" in newline and newline["widgetData"]:
                    newline["widgetData"] = fix_widget_data(newline["widgetData"])
            if "config" in newline:
                newline["config"] = clean_config(newline["config"])
            if "cardData" in result:
                if "Tags" in result["cardData"]:
                    if "tags" in result["cardData"]:
                        if type(result["cardData"]["Tags"]) == list and type(result["cardData"]["tags"]) == list:
                            newline["cardData"]["tags"].extend(newline["cardData"]["Tags"])
                            del newline["cardData"]["Tags"]
                        else:
                            del newline["cardData"]["Tags"]
                newline["cardData"] = fix_records(newline["cardData"], "tags", True)
                if "model-index" in result["cardData"]:
                    newline["cardData"]["model_index"] = fix_model_index(newline["cardData"]["model-index"])
                    del newline["cardData"]["model-index"]
                elif "model_index" in result["cardData"]:
                    newline["cardData"]["model_index"] = fix_model_index(newline["cardData"]["model_index"])
                if "widget" in result["cardData"] and result["cardData"]["widget"]:
                    newline["cardData"]["widget"] = fix_records(newline["cardData"]["widget"], "text")
                    newline["cardData"]["widget"] = fix_widget_data(newline["cardData"]["widget"])
                if "co2_eq_emissions" in result["cardData"]:
                    newline["cardData"]["co2_eq_emissions"] = fix_nullable_record(
                        newline["cardData"]["co2_eq_emissions"], "emissions")
                    newline["cardData"]["co2_eq_emissions"] = fix_co2(newline["cardData"]["co2_eq_emissions"])
                if "metrics" in result["cardData"]:
                    newline["cardData"]["metrics"] = fix_metrics(newline["cardData"]["metrics"])
                for field in ["tags", "language", "license", "datasets", "pipeline_tag"]:
                    if field in result["cardData"]:
                        newline["cardData"][field] = fix_repeateds(newline["cardData"][field])
                newline["cardData"] = clean_carddata_base_fields(newline["cardData"])
            newline["tags"] = interpret_tags(tag_dict, result["tags"])
            output.append(newline)
    return output

def write_output(data, out_dir: str):
    """
    Write the output json to a file
    :param data: The output data to write
    :param out_dir: directory for writing output data to
    :return: None
    """
    counts_fields = ["id", "_id", "modelId", "downloads", "likes"]
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    out = open(os.path.join(out_dir, "models_fixed.jsonl"), "w")
    usage_out = open(os.path.join(out_dir, "usage.jsonl"), "w")
    for entry in data:
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")
        usage_entry = {i: entry[i] for i in entry if i in counts_fields}
        usage_entry["update_time"] = timestamp
        usage_out.write(json.dumps(usage_entry, ensure_ascii=False) + "\n")
    out.close()
    usage_out.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", type=str,
                        help="A jsonl file containing the extracted model data, with fully specified path")
    parser.add_argument("tagfile", type=str,
                        help="A jsonl file containing the tag file, with fully specified path")
    parser.add_argument("out_dir", type=str,
                        help="A directory for writing the cleaned model data")

    args = parser.parse_args()
    if "jsonl" not in args.infile:
        parser.print_help()
    tag_helper = read_tag_data(args.tagfile)
    out_data = fix_data(args.infile, tag_helper)
    write_output(out_data, args.out_dir)