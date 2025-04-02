import unittest
import extract_data

class MyTestCase(unittest.TestCase):

    def test_get_model_ids(self):
        """
        Test that we are pulling the model ids successfully
        :return:
        """
        model_data = extract_data.get_model_ids()
        self.assertEqual(type(model_data), list)
        self.assertEqual(type(model_data[0]), dict)
        self.assertIn("id", model_data[0])
        # Make sure we're getting more than a single page of data
        self.assertGreater(len(model_data), 10000)

    def test_get_model_data(self):
        """
        Test that we are getting the individual models' data correctly
        :return:
        """
        model_data = extract_data.get_model_ids()
        info_dict, missed_list = extract_data.get_model_data(model_data[:100000])
        # self.assertEqual(len(info_dict), 20000)
        # self.assertEqual(len(info_dict), len(set(info_dict.keys())))
        # self.assertEqual(len(missed_list), 0)
        # self.assertIn("id", info_dict.popitem()[1])

    def test_get_model_tags_by_type(self):
        tag_data = extract_data.get_model_tags_by_type()
        self.assertEqual(type(tag_data), dict)
        self.assertGreaterEqual(len(tag_data), 6)
        self.assertIn("pipeline_tag", tag_data)
        self.assertIn("dataset", tag_data)
        self.assertIn("region", tag_data)
        self.assertIn("library", tag_data)
        self.assertIn("license", tag_data)
        self.assertIn("language", tag_data)
        for entry in tag_data:
            for elem in tag_data[entry]:
                self.assertIn("id", elem)
                self.assertIn("label", elem)
                self.assertIn("type", elem)



if __name__ == '__main__':
    unittest.main()
