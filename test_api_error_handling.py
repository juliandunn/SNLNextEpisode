import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
import json
import time
from lambda_function import SNLIntentHandler
from ask_sdk_core.handler_input import HandlerInput


class TestSNLIntentHandlerErrorHandling(unittest.TestCase):
    """Test cases for enhanced API error handling and retry logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = SNLIntentHandler()
        self.test_url = "https://api.tvmaze.com/shows/361"
        
    @patch('lambda_function.requests.get')
    @patch('lambda_function.time.sleep')
    def test_successful_api_call(self, mock_sleep, mock_get):
        """Test successful API call on first attempt."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'id': 361, 'name': 'Saturday Night Live'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertEqual(result, {'id': 361, 'name': 'Saturday Night Live'})
        mock_get.assert_called_once_with(self.test_url, timeout=5)
        mock_sleep.assert_not_called()
        
    @patch('lambda_function.requests.get')
    @patch('lambda_function.time.sleep')
    def test_timeout_with_retry_success(self, mock_sleep, mock_get):
        """Test timeout on first attempt, success on retry."""
        # First call times out, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.json.return_value = {'id': 361}
        mock_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            mock_response
        ]
        
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertEqual(result, {'id': 361})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(1)  # First retry delay
        
    @patch('lambda_function.requests.get')
    @patch('lambda_function.time.sleep')
    def test_connection_error_with_retry_failure(self, mock_sleep, mock_get):
        """Test connection error on all attempts."""
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.ConnectionError("Connection failed")
        ]
        
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(1)
        
    @patch('lambda_function.requests.get')
    def test_http_error_4xx_no_retry(self, mock_get):
        """Test that 4xx errors don't trigger retries."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertIsNone(result)
        mock_get.assert_called_once()  # No retry for 4xx errors
        
    @patch('lambda_function.requests.get')
    @patch('lambda_function.time.sleep')
    def test_http_error_5xx_with_retry(self, mock_sleep, mock_get):
        """Test that 5xx errors trigger retries."""
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Internal Server Error")
        http_error.response = mock_response
        mock_get.side_effect = [http_error, http_error]
        
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(1)
        
    @patch('lambda_function.requests.get')
    def test_json_decode_error(self, mock_get):
        """Test handling of malformed JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.text = "Invalid JSON content"
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_get.return_value = mock_response
        
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertIsNone(result)
        
    @patch('lambda_function.requests.get')
    def test_unexpected_content_type(self, mock_get):
        """Test handling of unexpected content types."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.json.return_value = {'id': 361}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Should still work but log a warning
        result = self.handler.retrieve_data(self.test_url)
        
        self.assertEqual(result, {'id': 361})
        
    @patch('lambda_function.requests.get')
    @patch('lambda_function.time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_get):
        """Test exponential backoff delay calculation."""
        mock_get.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.Timeout("Timeout")
        ]
        
        # Test with more retries to see backoff
        result = self.handler.retrieve_data(self.test_url, max_retries=1)
        
        self.assertIsNone(result)
        mock_sleep.assert_called_once_with(1)  # First retry: 2^0 = 1 second
        
    @patch('lambda_function.requests.get')
    def test_custom_timeout_and_retries(self, mock_get):
        """Test custom timeout and retry parameters."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = self.handler.retrieve_data(self.test_url, max_retries=0, timeout=10)
        
        self.assertIsNone(result)
        mock_get.assert_called_once_with(self.test_url, timeout=10)


class TestSNLIntentHandlerIntegration(unittest.TestCase):
    """Integration tests for the complete handle method with error scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = SNLIntentHandler()
        self.mock_handler_input = Mock(spec=HandlerInput)
        self.mock_response_builder = Mock()
        self.mock_handler_input.response_builder = self.mock_response_builder
        self.mock_response_builder.speak.return_value = self.mock_response_builder
        self.mock_response_builder.response = Mock()
        
    @patch.object(SNLIntentHandler, 'retrieve_data')
    def test_handle_show_metadata_failure(self, mock_retrieve):
        """Test handle method when show metadata retrieval fails."""
        mock_retrieve.return_value = None
        
        result = self.handler.handle(self.mock_handler_input)
        
        self.mock_response_builder.speak.assert_called_with(
            "I'm having trouble getting the latest SNL information right now. Please try again later."
        )
        
    @patch.object(SNLIntentHandler, 'retrieve_data')
    def test_handle_missing_next_episode_link(self, mock_retrieve):
        """Test handle method when next episode link is missing."""
        mock_retrieve.return_value = {'id': 361, 'name': 'SNL'}  # Missing _links
        
        result = self.handler.handle(self.mock_handler_input)
        
        self.mock_response_builder.speak.assert_called_with(
            "The next episode information isn't available yet. Check back soon!"
        )
        
    @patch.object(SNLIntentHandler, 'retrieve_data')
    def test_handle_episode_metadata_failure(self, mock_retrieve):
        """Test handle method when episode metadata retrieval fails."""
        mock_retrieve.side_effect = [
            {'_links': {'nextepisode': {'href': 'http://example.com/episode'}}},
            None  # Episode retrieval fails
        ]
        
        result = self.handler.handle(self.mock_handler_input)
        
        self.mock_response_builder.speak.assert_called_with(
            "I can tell you there's an upcoming SNL episode, but details aren't available right now."
        )
        
    @patch.object(SNLIntentHandler, 'retrieve_data')
    def test_handle_missing_airdate(self, mock_retrieve):
        """Test handle method when episode data is missing airdate."""
        mock_retrieve.side_effect = [
            {'_links': {'nextepisode': {'href': 'http://example.com/episode'}}},
            {'name': 'Host / Musical Guest'}  # Missing airdate
        ]
        
        result = self.handler.handle(self.mock_handler_input)
        
        self.mock_response_builder.speak.assert_called_with(
            "I'm having trouble getting the episode date information. Please try again later."
        )
        
    @patch.object(SNLIntentHandler, 'retrieve_data')
    @patch('lambda_function.datetime')
    def test_handle_successful_today_episode(self, mock_datetime, mock_retrieve):
        """Test successful handling of today's episode."""
        mock_datetime.date.today.return_value.strftime.return_value = "2024-12-15"
        mock_datetime.date.today.return_value.__str__.return_value = "2024-12-15"
        
        mock_retrieve.side_effect = [
            {'_links': {'nextepisode': {'href': 'http://example.com/episode'}}},
            {'airdate': '2024-12-15', 'name': 'Host / Musical Guest'}
        ]
        
        result = self.handler.handle(self.mock_handler_input)
        
        self.mock_response_builder.speak.assert_called_with(
            "Yes, it is with Host and Musical Guest."
        )


if __name__ == '__main__':
    unittest.main()