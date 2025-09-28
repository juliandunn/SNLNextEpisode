import unittest
from unittest.mock import MagicMock, patch
from src.lambda_function import SNLIntentHandler

class TestSNLIntentHandler(unittest.TestCase):
    def setUp(self):
        self.handler = SNLIntentHandler()
        self.handler_input = MagicMock()
        self.handler_input.response_builder.speak.return_value = self.handler_input.response_builder
        self.handler_input.response_builder.ask.return_value = self.handler_input.response_builder

    @patch('src.lambda_function.requests.get')
    def test_handle_with_new_episode_today(self, mock_get):
        # Mock the API responses
        mock_show_response = MagicMock()
        mock_show_response.json.return_value = {
            "_links": {
                "nextepisode": {
                    "href": "https://api.tvmaze.com/episodes/2345"
                }
            }
        }
        mock_episode_response = MagicMock()
        mock_episode_response.json.return_value = {
            "airdate": "2025-09-27",
            "name": "Host/Musical Guest"
        }
        mock_get.side_effect = [mock_show_response, mock_episode_response]

        # Call the handle method
        response = self.handler.handle(self.handler_input)

        # Assert the response is as expected
        self.handler_input.response_builder.speak.assert_called_with("Yes, it is with Host and Musical Guest.")

    @patch('src.lambda_function.requests.get')
    def test_handle_with_no_new_episode_today(self, mock_get):
        # Mock the API responses
        mock_show_response = MagicMock()
        mock_show_response.json.return_value = {
            "_links": {
                "nextepisode": {
                    "href": "https://api.tvmaze.com/episodes/2345"
                }
            }
        }
        mock_episode_response = MagicMock()
        mock_episode_response.json.return_value = {
            "airdate": "2025-10-04",
            "name": "Host/Musical Guest"
        }
        mock_get.side_effect = [mock_show_response, mock_episode_response]

        # Call the handle method
        response = self.handler.handle(self.handler_input)

        # Assert the response is as expected
        self.handler_input.response_builder.speak.assert_called_with("No, the next new episode of Saturday Night Live is on October 04, 2025.")

if __name__ == '__main__':
    unittest.main()