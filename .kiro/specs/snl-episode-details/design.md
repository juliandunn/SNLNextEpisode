# Design Document

## Overview

This design enhances the existing SNL Alexa skill by improving the `SNLIntentHandler` to provide comprehensive episode information including descriptions, host details, and better error handling. The solution leverages the TVMaze API to fetch rich episode metadata and presents it in a conversational format suitable for voice interaction.

## Architecture

### High-Level Flow
1. User invokes SNL intent through natural language
2. Enhanced `SNLIntentHandler` processes the request
3. TVMaze API calls retrieve show and episode data
4. Response formatter creates conversational output
5. Alexa delivers rich episode information to user

### API Integration
- **Primary Endpoint**: `https://api.tvmaze.com/shows/361` (SNL show metadata)
- **Episode Endpoint**: Retrieved dynamically from show metadata `_links.nextepisode.href`
- **Fallback Strategy**: Graceful degradation when API data is incomplete

## Components and Interfaces

### Enhanced SNLIntentHandler
```python
class SNLIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input) -> bool
    def handle(self, handler_input) -> Response
    def retrieve_data(self, url: str) -> dict | None
    def format_episode_response(self, episode_data: dict, show_data: dict) -> str
    def extract_host_info(self, episode_name: str, episode_summary: str) -> str
    def handle_api_error(self) -> str
```

### Response Formatter
```python
class EpisodeResponseFormatter:
    def format_next_episode_response(self, episode_data: dict) -> str
    def format_episode_description(self, summary: str) -> str
    def format_host_information(self, episode_name: str, summary: str) -> str
    def format_air_date(self, airdate: str) -> str
```

### Error Handler
```python
class APIErrorHandler:
    def handle_network_error(self, exception: Exception) -> str
    def handle_missing_data(self, data_type: str) -> str
    def should_retry(self, exception: Exception) -> bool
```

## Data Models

### TVMaze API Response Structure

#### Show Metadata
```json
{
  "id": 361,
  "name": "Saturday Night Live",
  "_links": {
    "nextepisode": {
      "href": "https://api.tvmaze.com/episodes/{episode_id}",
      "name": "Host Name / Musical Guest"
    }
  }
}
```

#### Episode Data
```json
{
  "id": 3245127,
  "name": "Bad Bunny / Doja Cat",
  "season": 51,
  "number": 1,
  "airdate": "2025-10-04",
  "airtime": "23:29",
  "summary": "<p>Episode description with HTML tags...</p>"
}
```

### Internal Data Processing
- **Host Extraction**: Parse episode name (format: "Host / Musical Guest")
- **Date Formatting**: Convert "YYYY-MM-DD" to natural language
- **Summary Cleaning**: Strip HTML tags and format for speech
- **Error States**: Handle missing fields gracefully

## Error Handling

### API Failure Scenarios
1. **Network Timeout**: Retry once, then fallback message
2. **Invalid Response**: Log error, provide generic response
3. **Missing Episode Data**: Indicate information not yet available
4. **Malformed JSON**: Handle parsing errors gracefully

### Fallback Responses
- "I'm having trouble getting the latest SNL information right now. Please try again later."
- "The next episode information isn't available yet. Check back soon!"
- "I can tell you there's an upcoming SNL episode, but details aren't available right now."

### Logging Strategy
- Log API response status codes
- Log parsing errors with context
- Log successful data retrieval for monitoring
- Avoid logging sensitive user data

## Testing Strategy

### Unit Tests
1. **API Response Parsing**: Test with various episode data formats
2. **Date Formatting**: Verify natural language date conversion
3. **Host Extraction**: Test different episode name formats
4. **Error Handling**: Mock API failures and verify responses
5. **HTML Cleaning**: Test summary text processing

### Integration Tests
1. **Live API Calls**: Test against actual TVMaze endpoints
2. **Response Formatting**: Verify complete response generation
3. **Error Scenarios**: Test with network disconnection
4. **Edge Cases**: Test with missing or incomplete data

### Voice Testing Considerations
- Verify response length is appropriate for voice
- Test pronunciation of host names and dates
- Ensure natural conversation flow
- Validate SSML compatibility if needed

## Implementation Notes

### Response Length Management
- Keep responses under 8 seconds of speech
- Prioritize most important information first
- Truncate long descriptions if necessary
- Provide option for more details

### Natural Language Processing
- Support variations: "next SNL", "upcoming Saturday Night Live", "next episode"
- Handle follow-up questions about the same episode
- Maintain conversational tone throughout

### Performance Considerations
- Cache episode data for repeated requests within session
- Implement request timeout (5 seconds max)
- Minimize API calls through efficient data retrieval
- Consider rate limiting for TVMaze API compliance