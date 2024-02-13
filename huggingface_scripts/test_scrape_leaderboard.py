import unittest
import scrape_leaderboard


class TestScrapeLeaderboard(unittest.TestCase):
    def test_get_page_data(self):
        leaderboard_data = scrape_leaderboard.get_page_data()
        self.assertEqual(type(leaderboard_data), list)
        self.assertGreaterEqual(len(leaderboard_data), 500)
        for elem in leaderboard_data:
            self.assertEqual(type(elem), list)
            self.assertEqual(len(elem), 22)


    def test_parse_leaderboard_data(self):
        leaderboard_data = scrape_leaderboard.get_page_data()
        leaderboard = scrape_leaderboard.parse_leaderboard_data(leaderboard_data)
        self.assertEqual(type(leaderboard), list)
        self.assertEqual(len(leaderboard_data), len(leaderboard))
        for elem in leaderboard:
            self.assertEqual(type(elem), dict)
            self.assertEqual(len(elem), 22)
            self.assertIn("id", elem)

if __name__ == '__main__':
    unittest.main()
