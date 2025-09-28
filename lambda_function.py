# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

import requests
import datetime
from datetime import datetime as dt
import time
import json
from response_formatter import EpisodeResponseFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can say next episode."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class SNLIntentHandler(AbstractRequestHandler):
    """Handler for SNL Intent with comprehensive response generation."""
    
    def __init__(self):
        """Initialize the handler with response formatter."""
        self.formatter = EpisodeResponseFormatter()
    
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_intent_name("SNLIntent")(handler_input)
        
    def retrieve_data(self, url, max_retries=1, timeout=5):
        """
        Enhanced data retrieval with retry logic and comprehensive error handling.
        
        Args:
            url (str): The URL to fetch data from
            max_retries (int): Maximum number of retry attempts (default: 1)
            timeout (int): Request timeout in seconds (default: 5)
            
        Returns:
            dict or None: Parsed JSON data or None if all attempts fail
        """
        attempt = 0
        last_exception = None
        
        while attempt <= max_retries:
            try:
                logger.info(f"API call attempt {attempt + 1} to: {url}")
                
                response = requests.get(url, timeout=timeout)
                
                # Log response status
                logger.info(f"API response status: {response.status_code}")
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Validate content type
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    logger.warning(f"Unexpected content type: {content_type}")
                
                # Parse JSON response
                try:
                    data = response.json()
                    logger.info("Successfully retrieved and parsed API data")
                    return data
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response content: {response.text[:200]}...")
                    raise requests.exceptions.RequestException(f"Invalid JSON response: {json_error}")
                    
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response else "unknown"
                logger.error(f"HTTP error {status_code} on attempt {attempt + 1}: {e}")
                
                # Don't retry on client errors (4xx)
                if e.response and 400 <= e.response.status_code < 500:
                    logger.error(f"Client error {e.response.status_code}, not retrying")
                    break
                    
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                
            attempt += 1
            
            # Add delay before retry (exponential backoff)
            if attempt <= max_retries:
                delay = min(2 ** (attempt - 1), 5)  # Cap at 5 seconds
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
        
        # All attempts failed
        logger.error(f"All {max_retries + 1} attempts failed for URL: {url}")
        if last_exception:
            logger.error(f"Final error: {last_exception}")
        
        return None
    
    def handle(self, handler_input):
        """
        Enhanced handle method with comprehensive response generation and session caching.
        
        Implements:
        - Use of new formatting utilities
        - Integration of episode description and host information
        - Response prioritization for voice output length management
        - Session-based caching for repeated requests
        """
        # Check session cache first to avoid repeated API calls
        session_attributes = handler_input.attributes_manager.session_attributes
        cached_response = self._get_cached_response(session_attributes)
        if cached_response:
            logger.info("Using cached episode response")
            return (handler_input.response_builder
                    .speak(cached_response)
                    .response)
        
        # Retrieve show metadata with error handling
        show_metadata = self.retrieve_data("https://api.tvmaze.com/shows/361")
        if not show_metadata:
            logger.error("Failed to retrieve show metadata")
            speak_output = self.formatter.format_error_response("network")
            return (handler_input.response_builder
                    .speak(speak_output)
                    .response)
        
        # Check if next episode link exists
        if "_links" not in show_metadata or "nextepisode" not in show_metadata["_links"]:
            logger.warning("No next episode information available in show metadata")
            speak_output = self.formatter.format_error_response("missing_data")
            return (handler_input.response_builder
                    .speak(speak_output)
                    .response)
        
        # Retrieve episode metadata with error handling
        episode_url = show_metadata["_links"]["nextepisode"]["href"]
        episode_metadata = self.retrieve_data(episode_url)
        if not episode_metadata:
            logger.error("Failed to retrieve episode metadata")
            speak_output = self.formatter.format_error_response("missing_data")
            return (handler_input.response_builder
                    .speak(speak_output)
                    .response)
        
        # Validate required episode fields
        if "airdate" not in episode_metadata:
            logger.error("Episode metadata missing airdate field")
            speak_output = self.formatter.format_error_response("general")
            return (handler_input.response_builder
                    .speak(speak_output)
                    .response)
        
        try:
            # Generate comprehensive response using formatting utilities
            speak_output = self.format_episode_response(episode_metadata, show_metadata)
            
            # Cache the response for this session
            self._cache_response(session_attributes, speak_output, episode_metadata.get("airdate"))
            
            logger.info("Successfully generated comprehensive episode response")
            
        except (ValueError, KeyError) as e:
            logger.error(f"Error processing episode data: {e}")
            speak_output = self.formatter.format_error_response("general")

        return (handler_input.response_builder
                .speak(speak_output)
                .response
        )
    
    def format_episode_response(self, episode_data: dict, show_data: dict) -> str:
        """
        Format comprehensive episode response with prioritized information.
        
        Args:
            episode_data: Episode metadata from TVMaze API
            show_data: Show metadata from TVMaze API
            
        Returns:
            Formatted response string optimized for voice output
        """
        # Use the comprehensive formatter from response_formatter.py
        return self.formatter.format_next_episode_response(episode_data, show_data)
    
    def extract_host_info(self, episode_name: str, episode_summary: str = None) -> str:
        """
        Extract host information using the enhanced host extraction utilities.
        
        Args:
            episode_name: Episode name from TVMaze API
            episode_summary: Optional episode summary for additional context
            
        Returns:
            Formatted host information string
        """
        return self.formatter.extract_host_info(episode_name, episode_summary)
    
    def handle_api_error(self, error_type: str = "general") -> str:
        """
        Handle API errors with appropriate user-friendly messages.
        
        Args:
            error_type: Type of error encountered
            
        Returns:
            User-friendly error message
        """
        return self.formatter.format_error_response(error_type)
    
    def _get_cached_response(self, session_attributes: dict) -> str:
        """
        Retrieve cached response if available and still valid.
        
        Args:
            session_attributes: Session attributes dictionary
            
        Returns:
            Cached response string or empty string if not available/expired
        """
        if not session_attributes:
            return ""
        
        cached_response = session_attributes.get("cached_episode_response")
        cached_date = session_attributes.get("cached_episode_date")
        cache_timestamp = session_attributes.get("cache_timestamp")
        
        if not all([cached_response, cached_date, cache_timestamp]):
            return ""
        
        # Check if cache is still valid (within same session and same day)
        current_date = str(datetime.date.today())
        current_timestamp = time.time()
        
        # Cache expires after 30 minutes or if date changes
        cache_duration = 30 * 60  # 30 minutes in seconds
        
        if (cached_date == current_date and 
            current_timestamp - cache_timestamp < cache_duration):
            return cached_response
        
        # Cache expired, clear it
        self._clear_cache(session_attributes)
        return ""
    
    def _cache_response(self, session_attributes: dict, response: str, episode_date: str):
        """
        Cache the response for this session.
        
        Args:
            session_attributes: Session attributes dictionary
            response: Response string to cache
            episode_date: Episode air date for cache validation
        """
        session_attributes["cached_episode_response"] = response
        session_attributes["cached_episode_date"] = episode_date
        session_attributes["cache_timestamp"] = time.time()
        
        logger.info("Cached episode response for session")
    
    def _clear_cache(self, session_attributes: dict):
        """
        Clear cached response data.
        
        Args:
            session_attributes: Session attributes dictionary
        """
        session_attributes.pop("cached_episode_response", None)
        session_attributes.pop("cached_episode_date", None)
        session_attributes.pop("cache_timestamp", None)
        
        logger.info("Cleared episode response cache")

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(SNLIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()