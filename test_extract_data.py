import unittest
import extract_data

class MyTestCase(unittest.TestCase):

    def test_get_model_ids(self):
        model_data = extract_data.get_model_ids()
        self.assertEqual(type(model_data), list)
        self.assertEqual(type(model_data[0]), dict)
        self.assertIn("id", model_data[0])
        # Make sure we're getting more than a single page of data
        self.assertGreater(len(model_data), 10000)

    def test_get_model_data(self):
        model_data = extract_data.get_model_ids()
        info_dict, missed_list = get_model_data(model_data[:10])
        self.assertEqual(len(info_dict), 10)
        self.assertEqual(len(missed_list), 0)
        self.assertIn("id", info_dict.pop())


if __name__ == '__main__':
    unittest.main()
