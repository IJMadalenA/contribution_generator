# tests/test_contribution_generator.py
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import csv
from datetime import datetime
import contribution_generator

class TestContributionGenerator(unittest.TestCase):

    @patch('contribution_generator.os.path.exists')
    @patch('contribution_generator.open', new_callable=mock_open)
    def test_validate_file(self, mock_open, mock_exists):
        mock_exists.return_value = False
        contribution_generator.validate_file()
        mock_open.assert_called_once_with('contributions.csv', 'w', newline='')

    @patch('contribution_generator.open', new_callable=mock_open, read_data='date,contributions,daily_limit\n2023-10-10,5,10\n')
    def test_read_number(self, mock_open):
        with patch('contribution_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 10)
            self.assertEqual(contribution_generator.read_number(), 5)

    @patch('contribution_generator.open', new_callable=mock_open)
    def test_write_number(self, mock_open):
        with patch('contribution_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 10)
            contribution_generator.write_number(6)
            mock_open().write.assert_called()

    @patch('contribution_generator.random.randint')
    @patch('contribution_generator.open', new_callable=mock_open, read_data='date,contributions,daily_limit\n2023-10-10,5,10\n')
    def test_get_daily_limit(self, mock_open, mock_randint):
        with patch('contribution_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 10)
            self.assertEqual(contribution_generator.get_daily_limit(), 10)

    @patch('contribution_generator.random.random')
    def test_should_execute(self, mock_random):
        mock_random.return_value = 0.5
        self.assertTrue(contribution_generator.should_execute())

if __name__ == '__main__':
    unittest.main()
