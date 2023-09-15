import unittest
import clean_data


class TestCleanData(unittest.TestCase):
    def test_fix_repeateds(self):
        none_test = None
        self.assertEqual([], clean_data.fix_repeateds(none_test))
        dict_test = {"a": 1}
        self.assertEqual(["{'a': 1}"], clean_data.fix_repeateds(dict_test))
        nullable_test = "autotrain"
        self.assertEqual(["autotrain"], clean_data.fix_repeateds(nullable_test))
        nested_test = ["common_voice", {"FOSD": "https://data.mendeley.com/datasets/k9sxg2twv4/4"}]
        self.assertEqual(["common_voice", "{'FOSD': 'https://data.mendeley.com/datasets/k9sxg2twv4/4'}"],
                         clean_data.fix_repeateds(nested_test))
        correct_test = ["national library of spain", "spanish", "bne", "capitel", "ner"]
        self.assertEqual(correct_test, clean_data.fix_repeateds(correct_test))

    def test_fix_records(self):
        repeated_test = ["Me llamo francisco javier y vivo en madrid.",
                         "Mi hermano ramón y su mejor amigo luis trabajan en el bsc."]
        self.assertEqual([{"text": "Me llamo francisco javier y vivo en madrid."},
                          {"text": "Mi hermano ramón y su mejor amigo luis trabajan en el bsc."}],
                         clean_data.fix_records(repeated_test, "text"))
        repeated_true_test = ["conversation"]
        self.assertEqual([{"tags": ["conversation"]}], clean_data.fix_records(repeated_true_test, "tags", True))
        correct_test = [{"text": "12 sets of 2 minutes 38 minutes between each set"}]
        self.assertEqual(correct_test, clean_data.fix_records(correct_test, "text"))

    def test_fix_model_index(self):
        none_test = None
        self.assertEqual(none_test, clean_data.fix_model_index(none_test))
        dict_test = {"error": "Schema validation error. \"[0].results\" is required"}
        self.assertEqual([{"error": "Schema validation error. \"[0].results\" is required"}],
                         clean_data.fix_model_index(dict_test))
        name_dict_test = [{"name": {"Wav2Vec2-XLSR-53 Kyrgyz by adilism": None}}]
        self.assertEqual([{"name": "Wav2Vec2-XLSR-53 Kyrgyz by adilism"}], clean_data.fix_model_index(name_dict_test))
        names_dict_test = [{"name": {"Wav2Vec2-XLSR-53 Kyrgyz by adilism": "something?"}}]
        self.assertEqual([{"name": "{'Wav2Vec2-XLSR-53 Kyrgyz by adilism': 'something?'}"}],
                         clean_data.fix_model_index(names_dict_test))
        datasets_fix_test = [{"datasets": {"name": "food-101", "type": "food101", "args": "default"}}]
        self.assertNotIn("datasets", clean_data.fix_model_index(datasets_fix_test)[0])
        self.assertIn("results", clean_data.fix_model_index(datasets_fix_test)[0])
        results_list_test =  [{"name": "drug-stance-bert", "results": [1, 0, 2]}]
        self.assertEqual([{"name": "drug-stance-bert", "results": {"values": [1, 0, 2]}}],
                         clean_data.fix_model_index(results_list_test))
        dataset_test = [{"results": [{"dataset": {"name": "emotion", "type": "emotion", "args": "default"}}]}]
        self.assertIn("datasets", clean_data.fix_model_index(dataset_test)[0]["results"][0])
        self.assertNotIn("dataset", clean_data.fix_model_index(dataset_test)[0]["results"][0])
        metric_test = [{"results": [{"metric": {"name": "Accuracy", "type": "accuracy", "value": 0.9254587155963303}}]}]
        self.assertIn("metrics", clean_data.fix_model_index(metric_test)[0]["results"][0])
        self.assertNotIn("metric", clean_data.fix_model_index(metric_test)[0]["results"][0])
        tasks_test = [{"results": [{"tasks": {"name": "NER", "type": "token-classification", "metrics":
            [{"name": "Precision", "type": "precision", "value": 0.9021803182}, {"name": "Recall", "type":
                "recall", "value": 0.9069905213}, {"name": "F Score", "type": "f_score", "value": 0.9045790251}]}}]}]
        self.assertIn("task", clean_data.fix_model_index(tasks_test)[0]["results"][0])
        self.assertNotIn("tasks", clean_data.fix_model_index(tasks_test)[0]["results"][0])
        self.assertEqual("[{'name': 'Precision', 'type': 'precision', 'value': 0.9021803182}, "
                         "{'name': 'Recall', 'type': 'recall', 'value': 0.9069905213}, {'name': "
                         "'F Score', 'type': 'f_score', 'value': 0.9045790251}]",
                         clean_data.fix_model_index(tasks_test)[0]["results"][0]["task"]["metrics"])
        correct_test = [{"name": "distilbert-base-uncased-finetuned-ner", "results":
            [{"task": {"name": "Token Classification", "type": "token-classification"},
              "datasets": [{"name": "conll2003", "type": "conll2003", "args": "conll2003"}],
              "metrics": [{"name": "Accuracy", "type": "accuracy", "value": 0.9844313470062116}]}]}]
        self.assertEqual(correct_test, clean_data.fix_model_index(correct_test))

    def test_fix_result_datasets(self):
        string_test = ["wine-quality"]
        self.assertEqual([{"name": "wine-quality"}], clean_data.fix_result_datasets(string_test))
        args_null_test = [{"name": "LibriSpeech (other)", "type": "librispeech_asr", "config": "other",
                          "split": "test", "args": {"language": "en"}}]
        self.assertEqual([{"name": "LibriSpeech (other)", "type": "librispeech_asr", "config": "other",
                          "split": "test", "args": "en"}], clean_data.fix_result_datasets(args_null_test))
        args_multiple_test = [{"name": "LibriSpeech (other)", "type": "librispeech_asr", "config": "other",
                          "split": "test", "args": {"language": "en", "other": "something"}}]
        self.assertEqual([{"name": "LibriSpeech (other)", "type": "librispeech_asr", "config": "other",
                           "split": "test", "args": "{'language': 'en', 'other': 'something'}"}],
                         clean_data.fix_result_datasets(args_multiple_test))
        correct_test = [{"name": "custom", "type": "custom", "args": "ben"}]
        self.assertEqual(correct_test, clean_data.fix_result_datasets(correct_test))

    def test_fix_result_metrics(self):
        value_list_test = [{"name": "Test CER", "type": "cer", "value": ["18.55%"], "verified": False}]
        self.assertEqual([{"name": "Test CER", "type": "cer", "value": "18.55%", "verified": False}],
                         clean_data.fix_result_metrics(value_list_test))
        value_dict_test = [{"name": "F1", "type": "f1", "value": {"f1": 0.8276613385259164}, "verified": False}]
        self.assertEqual([{"name": "F1", "type": "f1", "value": "{'f1': 0.8276613385259164}", "verified": False}],
                         clean_data.fix_result_metrics(value_dict_test))
        args_dict_test = [{"type": "wer", "value": 59.1, "name": "Test WER",
                           "args": {"learning_rate": 0.0003, "train_batch_size": 16, "lr_scheduler_warmup_steps": 200,
                                    "mixed_precision_training": "Native AMP"}, "verified": False}]
        self.assertEqual([{"type": "wer", "value": 59.1, "name": "Test WER",
                           "args": ["learning_rate : 0.0003", "train_batch_size : 16",
                                    "lr_scheduler_warmup_steps : 200", "mixed_precision_training : Native AMP"],
                           "verified": False}], clean_data.fix_result_metrics(args_dict_test))
        args_list_test = [{"type": "rouge1", "value": 0.652, "name": "Avg. Test Rouge1"},
                          {"type": "rougeL", "value": 0.632, "name": "Avg. Test RougeL"},
                          {"type": "bertscore", "value": 0.665, "name": "Avg. Test BERTScore",
                           "args": [{"model_type": "dbmdz/bert-base-italian-xxl-uncased"}, {"lang": "it"},
                                    {"num_layers": 10}, {"rescale_with_baseline": True},
                                    {"baseline_path": "bertscore_baseline_ita.tsv"}]}]
        self.assertEqual([{"type": "rouge1", "value": 0.652, "name": "Avg. Test Rouge1"},
                          {"type": "rougeL", "value": 0.632, "name": "Avg. Test RougeL"},
                          {"type": "bertscore", "value": 0.665, "name": "Avg. Test BERTScore",
                           "args": ["{'model_type': 'dbmdz/bert-base-italian-xxl-uncased'}", "{'lang': 'it'}",
                                    "{'num_layers': 10}", "{'rescale_with_baseline': True}",
                                    "{'baseline_path': 'bertscore_baseline_ita.tsv'}"]}],
                         clean_data.fix_result_metrics(args_list_test))
        plurals_test = [{"name": "Test WER and CER on text and puctuation prediction", "types": ["wer", "cer"],
                       "values": ["19.47%", "6.66%"]}, {"name": "Test WER and CER on text without punctuation",
                                                        "types": ["wer", "cer"], "values": ["17.88%", "6.37%"]}]
        self.assertEqual([{"name": "Test WER and CER on text and puctuation prediction", "type": "wer, cer",
                       "value": "19.47%, 6.66%"}, {"name": "Test WER and CER on text without punctuation",
                                                        "type": "wer, cer", "value": "17.88%, 6.37%"}],
                         clean_data.fix_result_metrics(plurals_test))
        correct_test = [{"type": "exact_match", "value": 81.2867, "verified": False},
                        {"type": "f1", "value": 88.4735, "verified": False}]
        self.assertEqual(correct_test, clean_data.fix_result_metrics(correct_test))

    def test_fix_nullable_records(self):
        nullable_test = 7.2566545568791945
        self.assertEqual({"emissions": 7.2566545568791945}, clean_data.fix_nullable_record(nullable_test, "emissions"))
        correct_test = {"emissions": 1027.9}
        self.assertEqual(correct_test, clean_data.fix_nullable_record(correct_test, "emissions"))

    def test_fix_metrics(self):
        null_test = None
        self.assertEqual([], clean_data.fix_metrics(null_test))
        string_test = "wer"
        self.assertEqual([{"value": "wer"}], clean_data.fix_metrics(string_test))
        list_test = ["accuracy"]
        self.assertEqual([{"value": "accuracy"}], clean_data.fix_metrics(list_test))
        bad_name_test = [{"accuracy": 0.9018}, {"F-1 score": 0.8956}]
        self.assertNotIn("F-1 score", clean_data.fix_metrics(bad_name_test)[1])
        self.assertNotIn("F-1_score", clean_data.fix_metrics(bad_name_test)[1])
        self.assertIn("f1", clean_data.fix_metrics(bad_name_test)[1])
        cleanup_name_test = [{"EM": 17}, {"Subset match": 24.5}]
        self.assertNotIn("EM", clean_data.fix_metrics(cleanup_name_test)[0])
        self.assertIn("em", clean_data.fix_metrics(cleanup_name_test)[0])
        self.assertNotIn("Subset match", clean_data.fix_metrics(cleanup_name_test)[1])
        self.assertNotIn("subset match", clean_data.fix_metrics(cleanup_name_test)[1])
        self.assertNotIn("Subset_match", clean_data.fix_metrics(cleanup_name_test)[1])
        self.assertIn("subset_match", clean_data.fix_metrics(cleanup_name_test)[1])
        non_core_test = [{"eval_loss": 0.08608942725107592}, {"eval_accuracy": 0.9925325215819639},
                         {"eval_f1": 0.8805402320715237}, {"average_rank": 0.27430093209054596}]
        self.assertEqual([{'name': 'eval_loss', 'value': 0.08608942725107592},
                          {'name': 'eval_accuracy', 'value': 0.9925325215819639},
                          {'name': 'eval_f1', 'value': 0.8805402320715237},
                          {'name': 'average_rank', 'value': 0.27430093209054596}],
                         clean_data.fix_metrics(non_core_test))

    def test_fix_widget_data(self):
        nullable_test = {"text": "A courier received 50 packages yesterday and twice as many today.  All of these"
                                 " should be delivered tomorrow. How many packages should be delivered tomorrow?"}
        self.assertEqual([{"text": ["A courier received 50 packages yesterday and twice as many today.  All of these"
                                 " should be delivered tomorrow. How many packages should be delivered tomorrow?"]}],
                         clean_data.fix_widget_data(nullable_test))
        string_test = "Hamed is a"
        self.assertEqual([{"text": ["Hamed is a"]}], clean_data.fix_widget_data(string_test))
        string_list_test = ["text \"春坊日記\""]
        self.assertEqual([{"text": ["text \"春坊日記\""]}], clean_data.fix_widget_data(string_list_test))
        non_list_text = [{"text": "My name is Julien and I like to"}, {"text": "My name is Thomas and my main"},
                         {"text": "My name is Mariama, my favorite"}, {"text": "My name is Clara and I am"},
                         {"text": "My name is Lewis and I like to"}, {"text": "My name is Merve and my favorite"},
                         {"text": "My name is Teven and I am"}, {"text": "Once upon a time,"}]
        self.assertEqual([{"text": ["My name is Julien and I like to"]}, {"text": ["My name is Thomas and my main"]},
                          {"text": ["My name is Mariama, my favorite"]}, {"text": ["My name is Clara and I am"]},
                          {"text": ["My name is Lewis and I like to"]}, {"text": ["My name is Merve and my favorite"]},
                          {"text": ["My name is Teven and I am"]}, {"text": ["Once upon a time,"]}],
                         clean_data.fix_widget_data(non_list_text))
        list_test = [{"text": "Existing Gas Turbine power plant  to improve transport systems etc.",
                              "example_title": ["Act. mob.", "Pub. transport improvement"]},
                             {"text": "Energy efficiency improvement measures include market transformation.",
                              "example_title": ["Public transport improvement"]}]
        self.assertEqual([{"text": ["Existing Gas Turbine power plant  to improve transport systems etc."],
                              "example_title": "Act. mob., Pub. transport improvement"},
                             {"text": ["Energy efficiency improvement measures include market transformation."],
                              "example_title": "Public transport improvement"}], clean_data.fix_widget_data(list_test))
        empty_string_test = [{"text": ""}]
        self.assertEqual([{"text": []}], clean_data.fix_widget_data(empty_string_test))
        non_core_test = [{"text": "ETH", "hypothesis_template": "This is {}."}]
        self.assertEqual([{"text": ["ETH"], "params": [{"name": "hypothesis_template", "value": "This is {}."}]}], clean_data.fix_widget_data(non_core_test))
        correct_test = [{"text": ["Yucaipa owned Dominick 's before selling "
                                    "the chain to Safeway in 1998 for $ 2.5 billion.",
                                    "Yucaipa bought Dominick's in 1995 for $ 693 million"
                                    " and sold it to Safeway for $ 1.8 billion in 1998."],
                           "example_title": "Not Equivalent"},
                          {"text": ["Revenue in the first quarter of the year dropped "
                                    "15 percent from the same period a year earlier.",
                                    "With the scandal hanging over Stewart's company"
                                    " revenue the first quarter of the year dropped 15"
                                    " percent from the same period a year earlier."],
                           "example_title": "Equivalent"}]
        self.assertEqual(correct_test, clean_data.fix_widget_data(correct_test))

    def test_clean_config(self):
        null_test = None
        self.assertEqual(null_test, clean_data.clean_config(null_test))
        type_list_test = {"architectures": ["BiLstm_Model"], "model_type": ["roberta"]}
        self.assertEqual({"architectures": ["BiLstm_Model"], "model_type": "roberta"},
                         clean_data.clean_config(type_list_test))
        auto_list_test = {"architectures": ["GPTPanguForCausalLM"], "model_type": "gpt_pangu",
                          "auto_map": {"AutoConfig": "configuration_gptpangu.GPTPanguConfig",
                                       "AutoTokenizer": ["tokenization_gptpangu.GPTPanguTokenizer", None],
                                       "AutoModelForCausalLM": "modeling_gptpangu.GPTPanguForCausalLM"}}
        self.assertEqual({"architectures": ["GPTPanguForCausalLM"], "model_type": "gpt_pangu",
                          "auto_map": [{"name": "AutoConfig", "value": "configuration_gptpangu.GPTPanguConfig"},
                                {"name": "AutoTokenizer", "value": "tokenization_gptpangu.GPTPanguTokenizer"},
                                {"name": "AutoModelForCausalLM", "value": "modeling_gptpangu.GPTPanguForCausalLM"}]},
                         clean_data.clean_config(auto_list_test))
        example_input_test = {"sklearn": {"columns": ["sepal length (cm)", "sepal width (cm)", "petal length (cm)",
                                                      "petal width (cm)"], "environment": ["scikit-learn=1.0.2"],
                                          "example_input": {"petal length (cm)": [4.7, 1.7, 6.9], "petal width (cm)":
                                              [1.2, 0.3, 2.3], "sepal length (cm)": [6.1, 5.7, 7.7], "sepal width (cm)":
                                              [2.8, 3.8, 2.6]}}}
        self.assertEqual({"sklearn": {"columns": ["sepal length (cm)", "sepal width (cm)", "petal length (cm)",
                                                      "petal width (cm)"], "environment": ["scikit-learn=1.0.2"],
                              "example_input": "{'petal length (cm)': [4.7, 1.7, 6.9], 'petal width (cm)': [1.2, 0.3,"
                                               " 2.3], 'sepal length (cm)': [6.1, 5.7, 7.7], 'sepal width (cm)': [2.8,"
                                               " 3.8, 2.6]}"}}, clean_data.clean_config(example_input_test))
        name_val_test = {"architectures": ["BERT_model_multidata"], "model_type": "bert", "task_specific_params":
            {"bert_hidden_size": 768, "biaffine": False, "boundaries_labels": None, "crf": True, "md_model": True,
             "md_number": 4, "predict_boundaries": False, "predict_masked": False, "type_crf_constraints": "BIOES"}}
        self.assertEqual({"architectures": ["BERT_model_multidata"], "model_type": "bert", "task_specific_params":
            [{"name": "bert_hidden_size", "value": 768}, {"name": "biaffine", "value": False},
             {"name": "boundaries_labels", "value": None}, {"name": "crf", "value": True},
             {"name": "md_model", "value": True}, {"name": "md_number", "value": 4},
             {"name": "predict_boundaries", "value": False}, {"name": "predict_masked", "value": False},
             {"name": "type_crf_constraints", "value": "BIOES"}]}, clean_data.clean_config(name_val_test))
        param_test = {"architectures": ["GPT2LMHeadModel"], "model_type": "gpt2",
                     "task_specific_params": {"text-generation": {"do_sample": True, "max_length": 50}}}
        self.assertEqual({"architectures": ["GPT2LMHeadModel"], "model_type": "gpt2",
                          "task_specific_params": [{"params": [{"name": "do_sample", "value": "True"},
                                                               {"name": "max_length", "value": "50"}],
                                                    "name": "text_generation"}]}, clean_data.clean_config(param_test))

    def test_clean_carddata_base_fields(self):
        singular_test = {"language": "en", "tag": "text-classification", "datasets": ["twitter", "movies subtitles"]}
        self.assertEqual({"language": "en", "tags": ["text-classification"], "datasets":
                              ["twitter", "movies subtitles"]}, clean_data.clean_carddata_base_fields(singular_test))
        singular_list_test = {"tags": ["image-segmentation", "generic"], "pipeline_tag":
            "image-segmentation", "dataset": ["oxfort-iit pets"], "license": "apache-2.0"}
        self.assertEqual({"tags": ["image-segmentation", "generic"], "pipeline_tag": "image-segmentation", "datasets":
            ["oxfort-iit pets"], "license": "apache-2.0"}, clean_data.clean_carddata_base_fields(singular_list_test))
        non_core_test = {"language": "no", "license": "cc-by-4.0", "tags": ["norwegian", "bert", "ner"],
                         "thumbnail": "nblogo_3.png", "pipeline_tag": "token-classification", "datasets": ["norne"],
                         "inference": {"parameters": {"aggregation_strategy": "first"}}}
        self.assertEqual({"language": "no", "license": "cc-by-4.0", "tags": ["norwegian", "bert", "ner"],"thumbnail":
            "nblogo_3.png", "pipeline_tag": "token-classification", "datasets": ["norne"], "params":
            [{"name": "inference", "value": "{'parameters': {'aggregation_strategy': 'first'}}"}]},
                         clean_data.clean_carddata_base_fields(non_core_test))

if __name__ == '__main__':
    unittest.main()
