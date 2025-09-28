# -*- coding: utf-8 -*-

"""
Unit tests for host information extraction functionality.
Tests various host name formats and edge cases for SNL episode data.
"""

import unittest
from response_formatter import HostExtractor, EpisodeResponseFormatter


class TestHostExtraction(unittest.TestCase):
    """Test cases for host information extraction from episode names and summaries."""
    
    def test_standard_slash_format_single_host(self):
        """Test standard format with host only."""
        # Host with empty musical guest
        result = HostExtractor.extract_host_information("Ryan Gosling / ", None)
        self.assertEqual(result, "Ryan Gosling")
        
        # Host with same name as musical guest
        result = HostExtractor.extract_host_information("Justin Timberlake / Justin Timberlake", None)
        self.assertEqual(result, "Justin Timberlake")
    
    def test_standard_slash_format_with_musical_guest(self):
        """Test standard format with host and musical guest."""
        result = HostExtractor.extract_host_information("Ryan Gosling / Chris Stapleton", None)
        self.assertEqual(result, "Ryan Gosling with musical guest Chris Stapleton")
        
        result = HostExtractor.extract_host_information("Ariana Grande / Stevie Nicks", None)
        self.assertEqual(result, "Ariana Grande with musical guest Stevie Nicks")
    
    def test_alternative_separator_formats(self):
        """Test various separator formats beyond slash."""
        # Ampersand separator
        result = HostExtractor.extract_host_information("Tina Fey & Amy Poehler", None)
        self.assertEqual(result, "Tina Fey and Amy Poehler")
        
        # "and" separator
        result = HostExtractor.extract_host_information("Steve Martin and Martin Short", None)
        self.assertEqual(result, "Steve Martin and Martin Short")
        
        # "with" separator
        result = HostExtractor.extract_host_information("Emma Stone with Taylor Swift", None)
        self.assertEqual(result, "Emma Stone with musical guest Taylor Swift")
        
        # Comma separator
        result = HostExtractor.extract_host_information("John Mulaney, Olivia Rodrigo", None)
        self.assertEqual(result, "John Mulaney and Olivia Rodrigo")
    
    def test_single_host_no_separator(self):
        """Test episode names with single host and no separator."""
        result = HostExtractor.extract_host_information("Dave Chappelle", None)
        self.assertEqual(result, "Dave Chappelle")
        
        result = HostExtractor.extract_host_information("Scarlett Johansson", None)
        self.assertEqual(result, "Scarlett Johansson")
    
    def test_multiple_host_formats(self):
        """Test various formats for multiple hosts."""
        # Co-hosts with "and"
        result = HostExtractor.extract_host_information("Kristen Wiig and Maya Rudolph", None)
        self.assertEqual(result, "Kristen Wiig and Maya Rudolph")
        
        # Co-hosts with "&"
        result = HostExtractor.extract_host_information("Jonah Hill & Emma Stone", None)
        self.assertEqual(result, "Jonah Hill and Emma Stone")
    
    def test_musical_guest_detection(self):
        """Test detection of musical guest indicators."""
        # Clear musical guest indicators
        result = HostExtractor.extract_host_information("Pete Davidson with musical guest Machine Gun Kelly", None)
        self.assertEqual(result, "Pete Davidson with musical guest Machine Gun Kelly")
        
        # Band indicator
        result = HostExtractor.extract_host_information("Adam Driver / Halsey", None)
        self.assertEqual(result, "Adam Driver with musical guest Halsey")
    
    def test_edge_cases_and_invalid_formats(self):
        """Test edge cases and invalid input handling."""
        # Empty or None input
        result = HostExtractor.extract_host_information("", None)
        self.assertEqual(result, "the host hasn't been announced yet")
        
        result = HostExtractor.extract_host_information(None, None)
        self.assertEqual(result, "the host hasn't been announced yet")
        
        # Whitespace only
        result = HostExtractor.extract_host_information("   ", None)
        self.assertEqual(result, "the host hasn't been announced yet")
        
        # Numbers only
        result = HostExtractor.extract_host_information("12345", None)
        self.assertEqual(result, "the host hasn't been announced yet")
        
        # Common placeholders
        result = HostExtractor.extract_host_information("TBD / TBA", None)
        self.assertEqual(result, "the host hasn't been announced yet")
        
        result = HostExtractor.extract_host_information("Episode 1", None)
        self.assertEqual(result, "the host hasn't been announced yet")
    
    def test_summary_extraction_fallback(self):
        """Test host extraction from episode summary when name parsing fails."""
        # Summary with clear host mention
        summary = "<p>This week's episode is hosted by Ryan Reynolds and features musical guest Taylor Swift.</p>"
        result = HostExtractor.extract_host_information("", summary)
        self.assertEqual(result, "Ryan Reynolds")
        
        # Summary with different host pattern
        summary = "<p>Join host Emma Stone for a night of comedy and music.</p>"
        result = HostExtractor.extract_host_information("TBD", summary)
        self.assertEqual(result, "Emma Stone")
        
        # Summary with "hosts" pattern
        summary = "<p>Saturday Night Live welcomes back Steve Martin who hosts tonight's show.</p>"
        result = HostExtractor.extract_host_information("", summary)
        self.assertEqual(result, "Steve Martin")
    
    def test_host_name_validation(self):
        """Test validation of potential host names."""
        # Valid names
        self.assertTrue(HostExtractor._is_valid_host_name("Ryan Gosling"))
        self.assertTrue(HostExtractor._is_valid_host_name("Ariana Grande"))
        self.assertTrue(HostExtractor._is_valid_host_name("The Rock"))
        
        # Invalid names
        self.assertFalse(HostExtractor._is_valid_host_name(""))
        self.assertFalse(HostExtractor._is_valid_host_name("123"))
        self.assertFalse(HostExtractor._is_valid_host_name("TBD"))
        self.assertFalse(HostExtractor._is_valid_host_name("Episode"))
        self.assertFalse(HostExtractor._is_valid_host_name("   "))
        self.assertFalse(HostExtractor._is_valid_host_name("!@#$%"))
    
    def test_musical_guest_detection_logic(self):
        """Test musical guest detection patterns."""
        # Should detect as musical guest
        self.assertTrue(HostExtractor._looks_like_musical_guest("Taylor Swift performs"))
        self.assertTrue(HostExtractor._looks_like_musical_guest("The band Coldplay"))
        self.assertTrue(HostExtractor._looks_like_musical_guest("Musical guest Billie Eilish"))
        
        # Should not detect as musical guest
        self.assertFalse(HostExtractor._looks_like_musical_guest("Ryan Reynolds"))
        self.assertFalse(HostExtractor._looks_like_musical_guest("Emma Stone"))
        self.assertFalse(HostExtractor._looks_like_musical_guest(""))
    
    def test_detailed_parsing_results(self):
        """Test detailed parsing results with parse_host_details method."""
        # Standard format with musical guest
        result = HostExtractor.parse_host_details("Ryan Gosling / Chris Stapleton", None)
        self.assertTrue(result['has_host'])
        self.assertEqual(result['host_name'], "Ryan Gosling")
        self.assertTrue(result['has_musical_guest'])
        self.assertEqual(result['musical_guest'], "Chris Stapleton")
        self.assertEqual(result['format_detected'], "standard_slash")
        self.assertEqual(result['confidence'], "high")
        
        # Single host
        result = HostExtractor.parse_host_details("Dave Chappelle", None)
        self.assertTrue(result['has_host'])
        self.assertEqual(result['host_name'], "Dave Chappelle")
        self.assertFalse(result['has_musical_guest'])
        self.assertEqual(result['format_detected'], "single_host")
        self.assertEqual(result['confidence'], "medium")
        
        # Invalid input
        result = HostExtractor.parse_host_details("", None)
        self.assertFalse(result['has_host'])
        self.assertEqual(result['format_detected'], "no_name")
        self.assertEqual(result['formatted_response'], "the host hasn't been announced yet")
    
    def test_complex_name_formats(self):
        """Test complex and unusual name formats."""
        # Names with special characters
        result = HostExtractor.extract_host_information("Dwayne 'The Rock' Johnson / Bad Bunny", None)
        self.assertEqual(result, "Dwayne 'The Rock' Johnson with musical guest Bad Bunny")
        
        # Names with Jr./Sr.
        result = HostExtractor.extract_host_information("Robert Downey Jr. / Imagine Dragons", None)
        self.assertEqual(result, "Robert Downey Jr. with musical guest Imagine Dragons")
        
        # Band names as hosts
        result = HostExtractor.extract_host_information("Foo Fighters / Foo Fighters", None)
        self.assertEqual(result, "Foo Fighters")
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in names."""
        # Extra whitespace
        result = HostExtractor.extract_host_information("  Ryan Gosling  /  Chris Stapleton  ", None)
        self.assertEqual(result, "Ryan Gosling with musical guest Chris Stapleton")
        
        # Mixed whitespace
        result = HostExtractor.extract_host_information("\tEmma Stone\n/\r\nTaylor Swift\t", None)
        self.assertEqual(result, "Emma Stone with musical guest Taylor Swift")
    
    def test_integration_with_episode_response_formatter(self):
        """Test integration with the main EpisodeResponseFormatter class."""
        formatter = EpisodeResponseFormatter()
        
        # Test that the main formatter uses the enhanced extraction
        result = formatter.extract_host_info("Ryan Gosling / Chris Stapleton", None)
        self.assertEqual(result, "Ryan Gosling with musical guest Chris Stapleton")
        
        # Test fallback behavior
        result = formatter.extract_host_info("", None)
        self.assertEqual(result, "the host hasn't been announced yet")
    
    def test_case_insensitive_processing(self):
        """Test that processing works regardless of case."""
        # Mixed case
        result = HostExtractor.extract_host_information("RYAN GOSLING / chris stapleton", None)
        self.assertEqual(result, "RYAN GOSLING with musical guest chris stapleton")
        
        # All lowercase
        result = HostExtractor.extract_host_information("emma stone / taylor swift", None)
        self.assertEqual(result, "emma stone with musical guest taylor swift")
    
    def test_long_name_handling(self):
        """Test handling of unusually long names."""
        # Very long name (should be rejected)
        long_name = "A" * 60
        result = HostExtractor.extract_host_information(long_name, None)
        self.assertEqual(result, "the host hasn't been announced yet")
        
        # Reasonable long name (should be accepted)
        reasonable_name = "Benedict Cumberbatch"
        result = HostExtractor.extract_host_information(reasonable_name, None)
        self.assertEqual(result, "Benedict Cumberbatch")
    
    def test_html_in_summary_extraction(self):
        """Test extraction from summaries containing HTML."""
        summary = "<p>Tonight's episode is hosted by <em>Ryan Reynolds</em> with musical guest Taylor Swift.</p>"
        result = HostExtractor.extract_host_information("TBD", summary)
        self.assertEqual(result, "Ryan Reynolds")
        
        # Complex HTML
        summary = """
        <div class="episode-info">
            <p>This week's Saturday Night Live is hosted by 
            <a href="#">Emma Stone</a> and features performances by 
            <span class="musical-guest">Billie Eilish</span>.</p>
        </div>
        """
        result = HostExtractor.extract_host_information("", summary)
        self.assertEqual(result, "Emma Stone")


if __name__ == '__main__':
    unittest.main()