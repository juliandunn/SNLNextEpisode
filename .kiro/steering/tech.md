# Technology Stack

## Runtime Environment
- **Platform**: AWS Lambda
- **Language**: Python 3.x
- **Framework**: Alexa Skills Kit SDK for Python

## Dependencies
- `boto3==1.28.78` - AWS SDK for Python
- `ask-sdk-core==1.19.0` - Alexa Skills Kit SDK
- `requests==2.31.0` - HTTP library for API calls

## External APIs
- **TVMaze API**: Used to fetch SNL show and episode data
  - Show endpoint: `https://api.tvmaze.com/shows/361`
  - Episode data accessed via show metadata links

## Build System

### Packaging Commands
```bash
# Create deployment package
make pkg

# Clean build artifacts
make clean
```

### Manual Build Process
1. Install dependencies to `./package` directory
2. Create ZIP archive with dependencies
3. Add source files to ZIP
4. Deploy `SNLNextEpisode.zip` to AWS Lambda

## Development Environment
- VSCode with Kiro MCP configuration enabled
- Standard Python development tools

## Deployment
- AWS Lambda function deployment
- Requires appropriate IAM permissions for Lambda execution
- Optional S3 integration for persistence (utilities provided)