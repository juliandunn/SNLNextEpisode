#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for response formatting utilities.
Tests all formatting functions with various input scenarios.
"""

import unittest
from datetime import date
from response_formatter import EpisodeResponseFormatter


class TestEpisodeResponseFormatter(unittest.TestCase):
    """Test cases for EpisodeResponseFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = EpisodeResponseFormatter()
        
        # Sample episode data for testing
        self.sample_episode_data = {
            "id": 3245127,
            "name": "Bad Bunny / Doja Cat",
            "season": 51,
            "number": 1,
            "airdate": "2024-12-15",
            "summary": "<p>Bad Bunny hosts Saturday Night Live with musical guest Doja Cat. The episode features comedy sketches and musical performances.</p>"
        }
        
        self.sample_episode_today = {
            "id": 3245128,
            "name": "Ryan Gosling / Chris Stapleton",
            "season": 51,
            "number": 2,
            "airdate": str(date.today()),
            "summary": "<p>Ryan Gosling returns to host with musical guest Chris Stapleton.</p>"
        }
    
    def test_format_air_date_valid_date(self):
        """Test date formatting with valid date."""
        result = self.formatter.format_air_date("2024-12-15")
        self.assertEqual(result, "December 15th, 2024")
    
    def test_format_air_date_ordinal_suffixes(self):
        """Test date formatting with various ordinal suffixes."""
        test_cases = [
            ("2024-01-01", "January 1st, 2024"),
            ("2024-01-02", "January 2nd, 2024"),
            ("2024-01-03", "January 3rd, 2024"),
            ("2024-01-04", "January 4th, 2024"),
            ("2024-01-11", "January 11th, 2024"),
            ("2024-01-21", "January 21st, 2024"),
            ("2024-01-22", "January 22nd, 2024"),
            ("2024-01-23", "January 23rd, 2024")
        ]
        
        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = self.formatter.format_air_date(input_date)
                self.assertEqual(result, expected)
    
    def test_format_air_date_invalid_input(self):
        """Test date formatting with invalid input."""
        invalid_inputs = ["invalid-date", "", None, "2024-13-45"]
        
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                result = self.formatter.format_air_date(invalid_input)
                self.assertEqual(result, "an upcoming date")
    
    def test_extract_host_info_standard_format(self):
        """Test host extraction with standard 'Host / Musical Guest' format."""
        result = self.formatter.extract_host_info("Bad Bunny / Doja Cat")
        self.assertEqual(result, "Bad Bunny with musical guest Doja Cat")
    
    def test_extract_host_info_same_host_and_guest(self):
        """Test host extraction when host and musical guest are the same."""
        result = self.formatter.extract_host_info("Taylor Swift / Taylor Swift")
        self.assertEqual(result, "Taylor Swift")
    
    def test_extract_host_info_host_only(self):
        """Test host extraction with no musical guest."""
        result = self.formatter.extract_host_info("Ryan Gosling /")
        self.assertEqual(result, "Ryan Gosling")
    
    def test_extract_host_info_no_slash(self):
        """Test host extraction with no slash separator."""
        result = self.formatter.extract_host_info("Steve Martin")
        self.assertEqual(result, "Steve Martin")
    
    def test_extract_host_info_empty_input(self):
        """Test host extraction with empty or None input."""
        result = self.formatter.extract_host_info("")
        self.assertEqual(result, "the host hasn't been announced yet")
        
        result = self.formatter.extract_host_info(None)
        self.assertEqual(result, "the host hasn't been announced yet")
    
    def test_clean_html_summary_basic_tags(self):
        """Test HTML cleaning with basic tags."""
        html_input = "<p>This is a <strong>test</strong> summary with <em>HTML</em> tags.</p>"
        expected = "This is a test summary with HTML tags."
        result = self.formatter.clean_html_summary(html_input)
        self.assertEqual(result, expected)
    
    def test_clean_html_summary_html_entities(self):
        """Test HTML cleaning with HTML entities."""
        html_input = "<p>Test &amp; example with &quot;quotes&quot; and &#39;apostrophes&#39;.</p>"
        expected = "Test & example with \"quotes\" and 'apostrophes'."
        result = self.formatter.clean_html_summary(html_input)
        self.assertEqual(result, expected)
    
    def test_clean_html_summary_whitespace_cleanup(self):
        """Test HTML cleaning with extra whitespace."""
        html_input = "<p>  Multiple   spaces    and\n\nnewlines  </p>"
        expected = "Multiple spaces and newlines"
        result = self.formatter.clean_html_summary(html_input)
        self.assertEqual(result, expected)
    
    def test_clean_html_summary_length_limit(self):
        """Test HTML cleaning without length limiting (length management is separate)."""
        long_text = "<p>" + "This is a very long summary. " * 20 + "Final sentence.</p>"
        result = self.formatter.clean_html_summary(long_text)
        
        # Should clean HTML but not truncate (that's done by manage_response_length)
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertIn("This is a very long summary.", result)
        self.assertIn("Final sentence.", result)
        
        # Test that length management works separately
        managed_result = self.formatter.manage_response_length(result, 300)
        self.assertLessEqual(len(managed_result), 350)
        self.assertTrue(managed_result.endswith('.') or managed_result.endswith('...'))
    
    def test_clean_html_summary_empty_input(self):
        """Test HTML cleaning with empty input."""
        self.assertEqual(self.formatter.clean_html_summary(""), "")
        self.assertEqual(self.formatter.clean_html_summary(None), "")
    
    def test_clean_html_summary_extended_entities(self):
        """Test HTML cleaning with extended HTML entities."""
        html_input = "<p>Test &mdash; with &ndash; dashes and &hellip; ellipsis &copy; 2024.</p>"
        expected = "Test — with – dashes and ... ellipsis © 2024."
        result = self.formatter.clean_html_summary(html_input)
        self.assertEqual(result, expected)
    
    def test_clean_html_summary_sentence_spacing(self):
        """Test HTML cleaning improves sentence spacing for voice."""
        html_input = "<p>First sentence.Second sentence.Third sentence.</p>"
        expected = "First sentence. Second sentence. Third sentence."
        result = self.formatter.clean_html_summary(html_input)
        self.assertEqual(result, expected)
    
    def test_extract_episode_summary_valid_data(self):
        """Test episode summary extraction with valid data."""
        episode_data = {
            "summary": "<p>This is a test episode summary with <strong>HTML</strong> tags.</p>"
        }
        result = self.formatter.extract_episode_summary(episode_data)
        self.assertEqual(result, "This is a test episode summary with HTML tags.")
    
    def test_extract_episode_summary_no_summary(self):
        """Test episode summary extraction with no summary field."""
        episode_data = {"name": "Test Episode"}
        result = self.formatter.extract_episode_summary(episode_data)
        self.assertEqual(result, "")
    
    def test_extract_episode_summary_empty_data(self):
        """Test episode summary extraction with empty or invalid data."""
        self.assertEqual(self.formatter.extract_episode_summary({}), "")
        self.assertEqual(self.formatter.extract_episode_summary(None), "")
        self.assertEqual(self.formatter.extract_episode_summary("invalid"), "")
    
    def test_manage_response_length_short_text(self):
        """Test length management with text shorter than limit."""
        short_text = "This is a short text."
        result = self.formatter.manage_response_length(short_text, 100)
        self.assertEqual(result, short_text)
    
    def test_manage_response_length_sentence_boundary(self):
        """Test length management truncates at sentence boundary."""
        long_text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        result = self.formatter.manage_response_length(long_text, 40)
        # Should truncate at sentence boundary
        self.assertTrue(result.endswith('.'))
        self.assertIn("First sentence.", result)
        self.assertLess(len(result), 45)
    
    def test_manage_response_length_comma_boundary(self):
        """Test length management truncates at comma when no sentence boundary."""
        long_text = "This is a very long sentence with commas, and more content, and even more content that goes on"
        result = self.formatter.manage_response_length(long_text, 50)
        # Should truncate at comma with ellipsis
        self.assertTrue(result.endswith('...'))
        self.assertIn(',', result)
    
    def test_manage_response_length_word_boundary(self):
        """Test length management truncates at word boundary as fallback."""
        long_text = "This is a very long text without punctuation that needs to be truncated somewhere"
        result = self.formatter.manage_response_length(long_text, 40)
        # Should truncate at word boundary with ellipsis
        self.assertTrue(result.endswith('...'))
        self.assertFalse(result.endswith(' ...'))  # No space before ellipsis
    
    def test_manage_response_length_hard_truncation(self):
        """Test length management with hard truncation fallback."""
        long_text = "Verylongwordwithoutspacesorpunctuationthatneedstobetruncat"
        result = self.formatter.manage_response_length(long_text, 30)
        # Should do hard truncation with ellipsis
        self.assertTrue(result.endswith('...'))
        self.assertEqual(len(result), 33)  # 30 + 3 for ellipsis
    
    def test_process_episode_description_with_summary(self):
        """Test episode description processing with summary available."""
        episode_data = {
            "summary": "<p>This is a test episode summary.</p>"
        }
        result = self.formatter.process_episode_description(episode_data)
        
        self.assertTrue(result['has_description'])
        self.assertEqual(result['processed_summary'], "This is a test episode summary.")
        self.assertGreater(result['original_length'], 0)
        self.assertGreater(result['processed_length'], 0)
        self.assertFalse(result['truncated'])
    
    def test_process_episode_description_long_summary(self):
        """Test episode description processing with long summary that gets truncated."""
        long_summary = "<p>" + "This is a very long episode summary. " * 20 + "</p>"
        episode_data = {"summary": long_summary}
        
        result = self.formatter.process_episode_description(episode_data)
        
        self.assertTrue(result['has_description'])
        self.assertGreater(result['original_length'], result['processed_length'])
        self.assertTrue(result['truncated'])
    
    def test_process_episode_description_no_summary(self):
        """Test episode description processing with no summary."""
        episode_data = {"name": "Test Episode"}
        result = self.formatter.process_episode_description(episode_data)
        
        self.assertFalse(result['has_description'])
        self.assertEqual(result['processed_summary'], "")
        self.assertEqual(result['original_length'], 0)
        self.assertEqual(result['processed_length'], 0)
        self.assertFalse(result['truncated'])
    
    def test_process_episode_description_invalid_data(self):
        """Test episode description processing with invalid data."""
        invalid_inputs = [None, {}, "invalid", []]
        
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                result = self.formatter.process_episode_description(invalid_input)
                self.assertFalse(result['has_description'])
                self.assertEqual(result['processed_summary'], "")
    
    def test_clean_html_summary_complex_html(self):
        """Test HTML cleaning with complex nested HTML structures."""
        complex_html = """
        <div class="episode-summary">
            <p>The episode features <a href="#">special guests</a> and includes:</p>
            <ul>
                <li>Comedy sketches with <em>celebrity cameos</em></li>
                <li>Musical performances by <strong>Grammy winners</strong></li>
            </ul>
            <p>Don't miss this <span style="color: red;">exciting</span> episode!</p>
        </div>
        """
        
        result = self.formatter.clean_html_summary(complex_html)
        
        # Should remove all HTML tags and normalize whitespace
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertIn('special guests', result)
        self.assertIn('Comedy sketches', result)
        self.assertIn('exciting episode', result)
        
        # Should have proper spacing
        self.assertNotIn('  ', result)  # No double spaces
    
    def test_clean_html_summary_malformed_html(self):
        """Test HTML cleaning with malformed HTML."""
        malformed_html = "<p>Unclosed paragraph <strong>bold text <em>nested emphasis</p>"
        
        result = self.formatter.clean_html_summary(malformed_html)
        
        # Should still clean up tags even if malformed
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertIn('Unclosed paragraph', result)
        self.assertIn('bold text', result)
        self.assertIn('nested emphasis', result)
    
    def test_format_next_episode_response_future_episode(self):
        """Test complete response formatting for future episode."""
        result = self.formatter.format_next_episode_response(self.sample_episode_data)
        
        self.assertIn("December 15th, 2024", result)
        self.assertIn("Bad Bunny with musical guest Doja Cat", result)
        self.assertIn("comedy sketches", result)
    
    def test_format_next_episode_response_today_episode(self):
        """Test complete response formatting for today's episode."""
        result = self.formatter.format_next_episode_response(self.sample_episode_today)
        
        self.assertIn("tonight", result)
        self.assertIn("Ryan Gosling with musical guest Chris Stapleton", result)
    
    def test_format_next_episode_response_no_summary(self):
        """Test response formatting with no episode summary."""
        episode_data = {
            "name": "John Mulaney / LCD Soundsystem",
            "airdate": "2024-12-20",
            "summary": ""
        }
        
        result = self.formatter.format_next_episode_response(episode_data)
        
        self.assertIn("December 20th, 2024", result)
        self.assertIn("John Mulaney with musical guest LCD Soundsystem", result)
        # Should not contain empty summary content
        self.assertNotIn("  ", result)  # No double spaces from missing summary
    
    def test_format_next_episode_response_empty_data(self):
        """Test response formatting with empty episode data."""
        result = self.formatter.format_next_episode_response({})
        self.assertEqual(result, "I'm having trouble getting the latest SNL information right now. Please try again later.")
        
        result = self.formatter.format_next_episode_response(None)
        self.assertEqual(result, "I'm having trouble getting the latest SNL information right now. Please try again later.")
    
    def test_format_episode_description_only_with_summary(self):
        """Test description-only formatting with summary available."""
        result = self.formatter.format_episode_description_only(self.sample_episode_data)
        
        self.assertIn("Here's what the episode is about:", result)
        self.assertIn("comedy sketches", result)
    
    def test_format_episode_description_only_no_summary(self):
        """Test description-only formatting with no summary."""
        episode_data = {
            "name": "Steve Martin / Steep Canyon Rangers",
            "summary": ""
        }
        
        result = self.formatter.format_episode_description_only(episode_data)
        
        self.assertIn("episode details aren't available yet", result)
        self.assertIn("Steve Martin", result)
    
    def test_format_episode_description_only_empty_data(self):
        """Test description-only formatting with empty data."""
        result = self.formatter.format_episode_description_only({})
        self.assertEqual(result, "I don't have episode details available right now.")
        
        result = self.formatter.format_episode_description_only(None)
        self.assertEqual(result, "I don't have episode details available right now.")
    
    def test_format_error_response_types(self):
        """Test error response formatting for different error types."""
        network_error = self.formatter.format_error_response("network")
        self.assertIn("trouble connecting", network_error)
        
        missing_data_error = self.formatter.format_error_response("missing_data")
        self.assertIn("isn't available yet", missing_data_error)
        
        general_error = self.formatter.format_error_response("general")
        self.assertIn("having trouble getting", general_error)
        
        # Test unknown error type defaults to general
        unknown_error = self.formatter.format_error_response("unknown_type")
        self.assertEqual(unknown_error, general_error)
    
    def test_format_error_response_default(self):
        """Test error response formatting with no error type specified."""
        result = self.formatter.format_error_response()
        self.assertIn("having trouble getting", result)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)