#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration test for the enhanced SNLIntentHandler functionality.
Tests the response formatting and caching logic without Alexa SDK dependencies.
"""

import unittest
from datetime import date
from response_formatter import EpisodeResponseFormatter


class TestSNLIntentHandlerIntegration(unittest.TestCase):
    """Test the enhanced SNLIntentHandler functionality."""
    
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
    
    def test_comprehensive_response_generation(self):
        """Test comprehensive response generation with all components."""
        # Test future episode response
        response = self.formatter.format_next_episode_response(self.sample_episode_data)
        
        # Should include date, host, and description
        self.assertIn("December 15th, 2024", response)
        self.assertIn("Bad Bunny", response)
        self.assertIn("Doja Cat", response)
        self.assertIn("comedy sketches", response)
    
    def test_today_episode_response(self):
        """Test response for today's episode."""
        response = self.formatter.format_next_episode_response(self.sample_episode_today)
        
        # Should indicate it's tonight
        self.assertIn("tonight", response)
        self.assertIn("Ryan Gosling", response)
        self.assertIn("Chris Stapleton", response)
    
    def test_error_handling_integration(self):
        """Test error handling with different error types."""
        network_error = self.formatter.format_error_response("network")
        missing_data_error = self.formatter.format_error_response("missing_data")
        general_error = self.formatter.format_error_response("general")
        
        # Each should be different and appropriate
        self.assertIn("connecting", network_error)
        self.assertIn("available yet", missing_data_error)
        self.assertIn("trouble getting", general_error)
    
    def test_host_extraction_integration(self):
        """Test host extraction integration."""
        # Standard format
        result = self.formatter.extract_host_info("Ryan Gosling / Chris Stapleton")
        self.assertEqual(result, "Ryan Gosling with musical guest Chris Stapleton")
        
        # Host only
        result = self.formatter.extract_host_info("Emma Stone")
        self.assertEqual(result, "Emma Stone")
        
        # Empty/invalid
        result = self.formatter.extract_host_info("")
        self.assertEqual(result, "the host hasn't been announced yet")
    
    def test_episode_description_processing(self):
        """Test episode description processing."""
        # With summary
        result = self.formatter.process_episode_description(self.sample_episode_data)
        
        self.assertTrue(result['has_description'])
        self.assertGreater(result['original_length'], 0)
        self.assertGreater(result['processed_length'], 0)
        self.assertIn("Bad Bunny hosts", result['processed_summary'])
        
        # Without summary
        no_summary_data = {"name": "Test Episode", "airdate": "2024-12-15"}
        result = self.formatter.process_episode_description(no_summary_data)
        
        self.assertFalse(result['has_description'])
        self.assertEqual(result['processed_summary'], "")
    
    def test_response_length_management(self):
        """Test response length management for voice output."""
        long_text = "This is a very long text that should be truncated. " * 20
        
        # Test with default length
        result = self.formatter.manage_response_length(long_text)
        self.assertLessEqual(len(result), 300)
        
        # Test with custom length
        result = self.formatter.manage_response_length(long_text, 50)
        self.assertLessEqual(len(result), 53)  # Allow for ellipsis
        
        # Test short text (should not be truncated)
        short_text = "Short text"
        result = self.formatter.manage_response_length(short_text)
        self.assertEqual(result, short_text)
    
    def test_html_cleaning_integration(self):
        """Test HTML cleaning integration."""
        html_text = "<p>This is <strong>bold</strong> text with &amp; entities.</p>"
        result = self.formatter.clean_html_summary(html_text)
        
        self.assertEqual(result, "This is bold text with & entities.")
        self.assertNotIn("<", result)
        self.assertNotIn("&amp;", result)
    
    def test_session_caching_logic(self):
        """Test session caching logic (simulated)."""
        # This would test the caching methods if we could instantiate SNLIntentHandler
        # For now, we test the components that would be used
        
        # Test that responses are consistent
        response1 = self.formatter.format_next_episode_response(self.sample_episode_data)
        response2 = self.formatter.format_next_episode_response(self.sample_episode_data)
        
        self.assertEqual(response1, response2)
        
        # Test that different data produces different responses
        response3 = self.formatter.format_next_episode_response(self.sample_episode_today)
        self.assertNotEqual(response1, response3)


if __name__ == '__main__':
    unittest.main()