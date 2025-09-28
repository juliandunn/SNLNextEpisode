# -*- coding: utf-8 -*-

"""
Response formatting utilities for SNL Alexa skill.
Provides functions for formatting episode data into conversational responses.
"""

import re
from datetime import datetime
from typing import Optional


class EpisodeResponseFormatter:
    """Utility class for formatting SNL episode data into conversational responses."""
    
    def format_air_date(self, airdate: str) -> str:
        """
        Convert API date format (YYYY-MM-DD) to natural language format.
        
        Args:
            airdate: Date string in YYYY-MM-DD format
            
        Returns:
            Formatted date string (e.g., "December 15th, 2024")
        """
        try:
            date_obj = datetime.strptime(airdate, "%Y-%m-%d")
            day = date_obj.day
            
            # Add ordinal suffix to day
            if 10 <= day % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            
            return date_obj.strftime(f"%B {day}{suffix}, %Y")
        except (ValueError, TypeError):
            return "an upcoming date"
    
    def extract_host_info(self, episode_name: str, episode_summary: Optional[str] = None) -> str:
        """
        Extract host information from episode name and summary with comprehensive format handling.
        
        Args:
            episode_name: Episode name (various formats supported)
            episode_summary: Optional episode summary for additional context
            
        Returns:
            Formatted host information string
        """
        return HostExtractor.extract_host_information(episode_name, episode_summary)


class HostExtractor:
    """Specialized class for extracting host information from SNL episode data."""
    
    # Common patterns for host/musical guest separators
    SEPARATOR_PATTERNS = [
        r'\s*/\s*',           # " / "
        r'\s*&\s*',           # " & "
        r'\s*and\s*',         # " and "
        r'\s*with\s*',        # " with "
        r'\s*featuring\s*',   # " featuring "
        r'\s*,\s*',           # " , "
    ]
    
    # Patterns to identify musical guest indicators
    MUSICAL_GUEST_INDICATORS = [
        r'musical\s+guest',
        r'music\s+by',
        r'performs',
        r'singing',
        r'musician',
        r'band',
        r'artist'
    ]
    
    @classmethod
    def extract_host_information(cls, episode_name: str, episode_summary: Optional[str] = None) -> str:
        """
        Main method to extract host information with comprehensive format handling.
        
        Args:
            episode_name: Episode name from TVMaze API
            episode_summary: Optional episode summary for additional context
            
        Returns:
            Formatted host information string
        """
        if not episode_name or not episode_name.strip():
            # Try summary extraction even if name is empty
            host_info = cls._extract_from_summary(episode_summary)
            if host_info:
                return host_info
            return cls._get_fallback_response("no_name")
        
        episode_name = episode_name.strip()
        
        # Try different extraction strategies
        host_info = cls._extract_from_standard_format(episode_name)
        if host_info:
            return host_info
        
        host_info = cls._extract_from_alternative_formats(episode_name)
        if host_info:
            return host_info
        
        host_info = cls._extract_from_summary(episode_summary)
        if host_info:
            return host_info
        
        # Fallback: treat entire name as host only if it's valid
        if cls._is_valid_host_name(episode_name):
            return cls._format_single_host(episode_name)
        else:
            return cls._get_fallback_response("invalid_format")
    
    @classmethod
    def _extract_from_standard_format(cls, episode_name: str) -> Optional[str]:
        """
        Extract host info from standard "Host / Musical Guest" format.
        
        Args:
            episode_name: Episode name to parse
            
        Returns:
            Formatted host string or None if format doesn't match
        """
        # Handle the most common format: "Host / Musical Guest"
        if "/" in episode_name:
            parts = [part.strip() for part in episode_name.split("/")]
            
            if len(parts) >= 2:
                host = parts[0]
                musical_guest = parts[1]
                
                # Validate host name
                if not cls._is_valid_host_name(host):
                    return None
                
                # Check if musical guest is meaningful
                if not musical_guest or host.lower() == musical_guest.lower():
                    return cls._format_single_host(host)
                elif cls._is_valid_host_name(musical_guest):
                    return cls._format_host_with_musical_guest(host, musical_guest)
                else:
                    return cls._format_single_host(host)
            elif len(parts) == 1:
                host = parts[0]
                return cls._format_single_host(host) if cls._is_valid_host_name(host) else None
        
        return None
    
    @classmethod
    def _extract_from_alternative_formats(cls, episode_name: str) -> Optional[str]:
        """
        Extract host info from alternative separator formats.
        
        Args:
            episode_name: Episode name to parse
            
        Returns:
            Formatted host string or None if no valid format found
        """
        for pattern in cls.SEPARATOR_PATTERNS[1:]:  # Skip "/" as it's handled separately
            if re.search(pattern, episode_name, re.IGNORECASE):
                parts = re.split(pattern, episode_name, flags=re.IGNORECASE)
                parts = [part.strip() for part in parts if part.strip()]
                
                if len(parts) >= 2:
                    host = parts[0]
                    potential_guest = parts[1]
                    
                    if cls._is_valid_host_name(host):
                        # Check if second part looks like a musical guest or if separator suggests it
                        if cls._looks_like_musical_guest(potential_guest) or "with" in pattern or "featuring" in pattern:
                            return cls._format_host_with_musical_guest(host, potential_guest)
                        else:
                            # Might be co-hosts
                            if cls._is_valid_host_name(potential_guest):
                                return cls._format_co_hosts(host, potential_guest)
                            else:
                                return cls._format_single_host(host)
                
                elif len(parts) == 1:
                    host = parts[0]
                    return cls._format_single_host(host) if cls._is_valid_host_name(host) else None
        
        return None
    
    @classmethod
    def _extract_from_summary(cls, episode_summary: Optional[str]) -> Optional[str]:
        """
        Extract host information from episode summary as fallback.
        
        Args:
            episode_summary: Episode summary text
            
        Returns:
            Formatted host string or None if no host found
        """
        if not episode_summary:
            return None
        
        # Clean HTML first - need to import re for this method
        import re
        # Remove HTML tags
        clean_summary = re.sub(r'<[^>]+>', '', episode_summary) if episode_summary else ""
        
        # Look for host patterns in summary
        host_patterns = [
            r'hosted?\s+by\s+([A-Za-z\s\'\.]+?)(?:\s+and|\s+with|\s+featuring|\s+for|\.|$)',
            r'host\s+is\s+([A-Za-z\s\'\.]+?)(?:\s+and|\s+with|\s+featuring|\s+for|\.|$)',
            r'Join\s+host\s+([A-Za-z\s\'\.]+?)(?:\s+and|\s+with|\s+featuring|\s+for|\.|$)',
            r'host\s+([A-Za-z\s\'\.]+?)(?:\s+and|\s+with|\s+featuring|\s+for|\.|$)',
            r'welcomes\s+back\s+([A-Za-z\s\'\.]+?)\s+who\s+hosts?',
            r'([A-Za-z\s\'\.]+?)\s+hosts?(?:\s+tonight|\s+today|\s+this|\s|$)',
            r'with\s+host\s+([A-Za-z\s\'\.]+?)(?:\s+and|\s+with|\s+featuring|\s+for|\.|$)',
        ]
        
        for pattern in host_patterns:
            match = re.search(pattern, clean_summary, re.IGNORECASE)
            if match:
                potential_host = match.group(1).strip()
                # Clean up common artifacts
                potential_host = re.sub(r'\s+', ' ', potential_host)
                potential_host = potential_host.strip(' .,')
                
                if cls._is_valid_host_name(potential_host):
                    return cls._format_single_host(potential_host)
        
        return None
    
    @classmethod
    def _is_valid_host_name(cls, name: str) -> bool:
        """
        Validate if a string looks like a valid host name.
        
        Args:
            name: Potential host name
            
        Returns:
            True if name appears to be a valid host name
        """
        if not name or len(name.strip()) < 2:
            return False
        
        name = name.strip()
        
        # Check for obvious non-names
        invalid_patterns = [
            r'^\d+$',                    # Just numbers
            r'^[^a-zA-Z]*$',            # No letters
            r'episode|show|snl|tbd|tba', # Common placeholders
            r'^\s*$',                    # Just whitespace
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', name):
            return False
        
        # Reasonable length check (2-50 characters)
        if len(name) > 50:
            return False
        
        return True
    
    @classmethod
    def _looks_like_musical_guest(cls, text: str) -> bool:
        """
        Determine if text likely refers to a musical guest.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if text appears to be musical guest reference
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for musical guest indicators
        for indicator in cls.MUSICAL_GUEST_INDICATORS:
            if re.search(indicator, text_lower):
                return True
        
        # Check for common musical terms
        musical_terms = ['band', 'singer', 'rapper', 'musician', 'artist', 'group']
        for term in musical_terms:
            if term in text_lower:
                return True
        
        return False
    
    @classmethod
    def _format_single_host(cls, host: str) -> str:
        """Format response for single host."""
        return host.strip()
    
    @classmethod
    def _format_host_with_musical_guest(cls, host: str, musical_guest: str) -> str:
        """Format response for host with musical guest."""
        # Remove "musical guest" prefix if it already exists in the guest name
        guest_clean = musical_guest.strip()
        if guest_clean.lower().startswith('musical guest '):
            guest_clean = guest_clean[14:]  # Remove "musical guest " prefix
        
        return f"{host.strip()} with musical guest {guest_clean}"
    
    @classmethod
    def _format_co_hosts(cls, host1: str, host2: str) -> str:
        """Format response for co-hosts."""
        return f"{host1.strip()} and {host2.strip()}"
    
    @classmethod
    def _get_fallback_response(cls, reason: str = "general") -> str:
        """
        Get appropriate fallback response when host extraction fails.
        
        Args:
            reason: Reason for fallback ("no_name", "invalid_format", "general")
            
        Returns:
            Appropriate fallback message
        """
        fallback_responses = {
            "no_name": "the host hasn't been announced yet",
            "invalid_format": "the host hasn't been announced yet",
            "general": "the host hasn't been announced yet"
        }
        
        return fallback_responses.get(reason, fallback_responses["general"])
    
    @classmethod
    def parse_host_details(cls, episode_name: str, episode_summary: Optional[str] = None) -> dict:
        """
        Parse host information and return detailed breakdown.
        
        Args:
            episode_name: Episode name from TVMaze API
            episode_summary: Optional episode summary
            
        Returns:
            Dictionary with detailed host information:
            {
                'has_host': bool,
                'host_name': str,
                'has_musical_guest': bool,
                'musical_guest': str,
                'format_detected': str,
                'confidence': str,
                'formatted_response': str
            }
        """
        result = {
            'has_host': False,
            'host_name': '',
            'has_musical_guest': False,
            'musical_guest': '',
            'format_detected': 'unknown',
            'confidence': 'low',
            'formatted_response': cls._get_fallback_response()
        }
        
        if not episode_name or not episode_name.strip():
            result['format_detected'] = 'no_name'
            return result
        
        episode_name = episode_name.strip()
        
        # Try standard format first
        if "/" in episode_name:
            parts = [part.strip() for part in episode_name.split("/")]
            if len(parts) >= 2:
                host = parts[0]
                potential_guest = parts[1]
                
                if cls._is_valid_host_name(host):
                    result['has_host'] = True
                    result['host_name'] = host
                    result['format_detected'] = 'standard_slash'
                    result['confidence'] = 'high'
                    
                    if potential_guest and cls._is_valid_host_name(potential_guest):
                        result['has_musical_guest'] = True
                        result['musical_guest'] = potential_guest
                        result['formatted_response'] = cls._format_host_with_musical_guest(host, potential_guest)
                    else:
                        result['formatted_response'] = cls._format_single_host(host)
                    
                    return result
        
        # Try alternative formats
        for i, pattern in enumerate(cls.SEPARATOR_PATTERNS[1:], 1):
            if re.search(pattern, episode_name, re.IGNORECASE):
                parts = re.split(pattern, episode_name, flags=re.IGNORECASE)
                parts = [part.strip() for part in parts if part.strip()]
                
                if len(parts) >= 2:
                    host = parts[0]
                    potential_guest = parts[1]
                    
                    if cls._is_valid_host_name(host):
                        result['has_host'] = True
                        result['host_name'] = host
                        result['format_detected'] = f'alternative_{i}'
                        result['confidence'] = 'medium'
                        
                        if cls._looks_like_musical_guest(potential_guest):
                            result['has_musical_guest'] = True
                            result['musical_guest'] = potential_guest
                            result['formatted_response'] = cls._format_host_with_musical_guest(host, potential_guest)
                        elif cls._is_valid_host_name(potential_guest):
                            result['formatted_response'] = cls._format_co_hosts(host, potential_guest)
                        else:
                            result['formatted_response'] = cls._format_single_host(host)
                        
                        return result
        
        # Try single host
        if cls._is_valid_host_name(episode_name):
            result['has_host'] = True
            result['host_name'] = episode_name
            result['format_detected'] = 'single_host'
            result['confidence'] = 'medium'
            result['formatted_response'] = cls._format_single_host(episode_name)
            return result
        
        # Try summary extraction
        summary_host = cls._extract_from_summary(episode_summary)
        if summary_host:
            result['has_host'] = True
            result['host_name'] = summary_host
            result['format_detected'] = 'summary_extraction'
            result['confidence'] = 'low'
            result['formatted_response'] = summary_host
            return result
        
        return result


class EpisodeResponseFormatterMethods:
    """Additional methods for EpisodeResponseFormatter - will be moved back to main class."""
    
    def clean_html_summary(self, summary: str) -> str:
        """
        Remove HTML tags and format text for voice output.
        
        Args:
            summary: Raw HTML summary text
            
        Returns:
            Clean text suitable for voice output
        """
        if not summary:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', summary)
        
        # Replace HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&mdash;': '—',
            '&ndash;': '–',
            '&hellip;': '...',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™'
        }
        
        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)
        
        # Clean up extra whitespace and normalize punctuation
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Improve readability for voice by adding pauses after sentences
        clean_text = re.sub(r'\.([A-Z])', r'. \1', clean_text)
        
        return clean_text
    
    def extract_episode_summary(self, episode_data: dict) -> str:
        """
        Extract and process episode summary from TVMaze API response.
        
        Args:
            episode_data: Episode data dictionary from TVMaze API
            
        Returns:
            Processed episode summary suitable for voice output
        """
        if not episode_data or not isinstance(episode_data, dict):
            return ""
        
        summary = episode_data.get("summary", "")
        if not summary:
            return ""
        
        # Clean HTML and format for voice
        clean_summary = self.clean_html_summary(summary)
        
        # Apply voice-specific length management
        return self.manage_response_length(clean_summary)
    
    def manage_response_length(self, text: str, max_length: int = 300) -> str:
        """
        Manage text length for optimal voice output.
        
        Args:
            text: Input text to manage
            max_length: Maximum character length (default: 300 for ~6-8 seconds speech)
            
        Returns:
            Text truncated appropriately for voice output
        """
        if not text or len(text) <= max_length:
            return text
        
        # Try to find a natural break point
        truncated = text[:max_length]
        
        # Look for sentence endings first
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        # Find the latest sentence ending
        sentence_end = max(last_period, last_exclamation, last_question)
        
        # If we found a sentence ending and it's not too early in the text
        if sentence_end > max_length * 0.6:
            return truncated[:sentence_end + 1]
        
        # Look for comma or semicolon as backup
        last_comma = truncated.rfind(',')
        last_semicolon = truncated.rfind(';')
        clause_end = max(last_comma, last_semicolon)
        
        if clause_end > max_length * 0.7:
            return truncated[:clause_end + 1] + "..."
        
        # Find last complete word
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:
            return truncated[:last_space] + "..."
        
        # Fallback: hard truncation with ellipsis
        return truncated + "..."
    
    def format_next_episode_response(self, episode_data: dict, show_data: dict = None) -> str:
        """
        Format a complete response for next episode information.
        
        Args:
            episode_data: Episode data from TVMaze API
            show_data: Optional show data for additional context
            
        Returns:
            Complete formatted response string
        """
        if not episode_data:
            return "I'm having trouble getting the latest SNL information right now. Please try again later."
        
        # Get basic episode info
        airdate = episode_data.get("airdate", "")
        episode_name = episode_data.get("name", "")
        summary = episode_data.get("summary", "")
        
        # Check if episode is today
        from datetime import date
        today = str(date.today())
        
        if airdate == today:
            host_info = self.extract_host_info(episode_name)
            response = f"Yes, there's a new Saturday Night Live episode tonight with {host_info}."
            
            # Add description if available
            processed_summary = self.extract_episode_summary(episode_data)
            if processed_summary:
                response += f" {processed_summary}"
        else:
            # Future episode
            formatted_date = self.format_air_date(airdate)
            host_info = self.extract_host_info(episode_name)
            
            response = f"The next Saturday Night Live episode is on {formatted_date} with {host_info}."
            
            # Add description if available
            processed_summary = self.extract_episode_summary(episode_data)
            if processed_summary:
                response += f" {processed_summary}"
        
        return response
    
    def format_episode_description_only(self, episode_data: dict) -> str:
        """
        Format response focusing only on episode description.
        
        Args:
            episode_data: Episode data from TVMaze API
            
        Returns:
            Description-focused response string
        """
        if not episode_data:
            return "I don't have episode details available right now."
        
        # Extract and process the episode summary
        processed_summary = self.extract_episode_summary(episode_data)
        episode_name = episode_data.get("name", "")
        
        if processed_summary:
            return f"Here's what the episode is about: {processed_summary}"
        
        # Fallback if no summary
        if episode_name:
            host_info = self.extract_host_info(episode_name)
            return f"The episode details aren't available yet, but it will feature {host_info}."
        
        return "The episode details aren't available yet. Check back soon!"
    
    def process_episode_description(self, episode_data: dict) -> dict:
        """
        Process episode description data for conversational output.
        
        Args:
            episode_data: Episode data from TVMaze API
            
        Returns:
            Dictionary containing processed description information:
            {
                'has_description': bool,
                'processed_summary': str,
                'original_length': int,
                'processed_length': int,
                'truncated': bool
            }
        """
        result = {
            'has_description': False,
            'processed_summary': '',
            'original_length': 0,
            'processed_length': 0,
            'truncated': False
        }
        
        if not episode_data or not isinstance(episode_data, dict):
            return result
        
        original_summary = episode_data.get("summary", "")
        if not original_summary:
            return result
        
        result['has_description'] = True
        result['original_length'] = len(original_summary)
        
        # Process the summary
        processed_summary = self.extract_episode_summary(episode_data)
        result['processed_summary'] = processed_summary
        result['processed_length'] = len(processed_summary)
        
        # Check if content was truncated
        clean_full = self.clean_html_summary(original_summary)
        result['truncated'] = len(processed_summary) < len(clean_full)
        
        return result
    
    def format_error_response(self, error_type: str = "general") -> str:
        """
        Format appropriate error response based on error type.
        
        Args:
            error_type: Type of error ("network", "missing_data", "general")
            
        Returns:
            User-friendly error message
        """
        error_responses = {
            "network": "I'm having trouble connecting to get the latest SNL information. Please try again in a moment.",
            "missing_data": "The next episode information isn't available yet. Check back soon!",
            "general": "I'm having trouble getting the latest SNL information right now. Please try again later."
        }
        
        return error_responses.get(error_type, error_responses["general"])