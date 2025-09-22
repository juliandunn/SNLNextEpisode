# Project Structure

## Root Directory Layout
```
├── lambda_function.py    # Main Alexa skill handler
├── utils.py             # Utility functions (S3 operations)
├── requirements.txt     # Python dependencies
├── Makefile            # Build automation
├── LICENSE             # Project license
├── .vscode/            # VSCode configuration
└── .kiro/              # Kiro AI assistant configuration
```

## Code Organization

### Main Entry Point
- **`lambda_function.py`**: Contains all Alexa skill handlers and main logic
  - Request handlers for different intents
  - Exception handling
  - Skill builder configuration

### Handler Classes
All handlers follow the Alexa Skills Kit pattern:
- `LaunchRequestHandler` - Skill launch/welcome
- `SNLIntentHandler` - Main SNL episode query logic
- `CancelOrStopIntentHandler` - Exit intents
- `FallbackIntentHandler` - Fallback responses
- `SessionEndedRequestHandler` - Session cleanup
- `IntentReflectorHandler` - Debug/testing handler
- `CatchAllExceptionHandler` - Global error handling

### Utilities
- **`utils.py`**: Helper functions for AWS services
  - S3 presigned URL generation
  - AWS client configuration

## Coding Conventions

### Handler Pattern
- Each handler implements `can_handle()` and `handle()` methods
- Type hints used for method signatures
- Handlers registered with SkillBuilder in specific order

### Error Handling
- Comprehensive exception handling at multiple levels
- Logging with appropriate log levels
- Graceful fallbacks for API failures

### API Integration
- External API calls wrapped in try-catch blocks
- HTTP status code validation
- JSON response parsing with error handling