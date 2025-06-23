"""
Sonarr YT-DLP Application - Development Guide

## Project Structure

The application has been completely rewritten using Python best practices with a modular architecture:

```
app/
├── src/                    # Main source code
│   ├── __init__.py
│   ├── app.py             # Main application orchestrator
│   ├── config/            # Configuration management
│   │   └── __init__.py
│   ├── models/            # Data models
│   │   └── __init__.py
│   ├── services/          # External service clients
│   │   ├── __init__.py
│   │   ├── sonarr_client.py
│   │   └── ytdlp_service.py
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── date_utils.py
│       ├── logging_utils.py
│       └── text_utils.py
├── main.py                # Application entry point
├── config.yml.template    # Configuration template
├── sonarr_youtubedl.py   # Legacy script (deprecated)
└── utils.py              # Legacy utilities (deprecated)
```

## Key Improvements

### 1. Modular Architecture
- **Separation of Concerns**: Each module has a single responsibility
- **Loose Coupling**: Modules interact through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 2. Error Handling
- **Custom Exceptions**: Specific error types for different failure modes
- **Graceful Degradation**: Application continues running despite individual failures
- **Comprehensive Logging**: Detailed error information for debugging

### 3. Configuration Management
- **Validation**: Configuration is validated on startup
- **Type Safety**: Proper type handling for configuration values
- **Environment Variables**: Support for containerized deployments

### 4. Data Models
- **Type Hints**: Full type annotation throughout the codebase
- **Dataclasses**: Clean, readable data structures
- **Validation**: Input validation and sanitization

### 5. Service Layer
- **API Abstraction**: Clean interfaces for external services
- **Retry Logic**: Automatic retry for transient failures
- **Resource Management**: Proper cleanup of connections and files

### 6. Utility Functions
- **Single Purpose**: Each function has one clear responsibility
- **Reusability**: Common functionality extracted to utilities
- **Testing**: Functions designed for easy unit testing

## Development Workflow

### 1. Running the Application
```bash
# Using the new entry point
python app/main.py

# Or using the legacy script (deprecated)
python app/sonarr_youtubedl.py
```

### 2. Configuration
The application uses the same `config.yml` format as before, but with improved validation:

```yaml
sonarrytdl:
  scan_interval: 60  # minutes
  debug: false

sonarr:
  host: localhost
  port: 8989
  apikey: your_api_key
  ssl: false
  apiBasePath: api/v3

ytdl:
  default_format: "bestvideo[width<=1920]+bestaudio/best[width<=1920]"

series:
  - title: "Example Series"
    url: "https://youtube.com/channel/..."
    # ... other options
```

### 3. Logging
The new logging system provides:
- **Structured Logs**: Consistent format across all modules
- **Log Rotation**: Automatic log file rotation to prevent disk filling
- **Debug Mode**: Detailed debugging information when enabled
- **Multiple Handlers**: Console and file logging with different levels

### 4. Error Recovery
The application now handles errors more gracefully:
- **API Failures**: Continues processing other series if one fails
- **Download Errors**: Logs errors but doesn't crash the application
- **Configuration Errors**: Clear error messages with suggestions for fixes

## Migration from Legacy Code

### Key Changes
1. **Import Statements**: Update any custom code to use the new module structure
2. **Configuration**: No changes required to `config.yml`
3. **Docker**: Updated Dockerfile uses the new entry point
4. **Logging**: Improved log format and rotation

### Backward Compatibility
- **Configuration**: Existing `config.yml` files work without modification
- **Docker Volumes**: Same volume mounts as before
- **Environment Variables**: Same environment variables supported

## Extending the Application

### Adding New Video Sources
1. Create a new service class in `src/services/`
2. Implement the search and download interface
3. Register the service in the main application

### Custom Processing
1. Add new utility functions in `src/utils/`
2. Create new data models in `src/models/` if needed
3. Extend the main application logic in `src/app.py`

### Configuration Options
1. Update the configuration validation in `src/config/__init__.py`
2. Add new configuration fields to the template
3. Use the new options in the appropriate service classes

## Testing

The modular structure makes testing much easier:

```python
# Example unit test structure
import pytest
from src.services.sonarr_client import SonarrClient
from src.models import Series, Episode

def test_sonarr_client():
    # Test individual components in isolation
    pass

def test_episode_filtering():
    # Test business logic separately
    pass
```

## Performance Considerations

### Memory Usage
- **Lazy Loading**: Configuration loaded only when needed
- **Resource Cleanup**: Proper cleanup of HTTP connections and file handles
- **Generator Usage**: Memory-efficient processing of large lists

### Network Efficiency
- **Connection Reuse**: HTTP connections reused where possible
- **Timeout Handling**: Proper timeouts to prevent hanging
- **Retry Logic**: Intelligent retry with backoff

### Disk I/O
- **Log Rotation**: Prevents disk space issues
- **Atomic Operations**: File operations are atomic where possible
- **Path Validation**: Proper path handling across platforms

## Security Improvements

### Input Validation
- **Configuration Validation**: All configuration values validated
- **Path Sanitization**: File paths properly sanitized
- **URL Validation**: URLs validated before use

### Error Information
- **Sensitive Data**: API keys and sensitive information not logged
- **Error Details**: Sufficient detail for debugging without security risks
- **Exception Handling**: Proper exception handling prevents information leakage

This new architecture provides a solid foundation for future enhancements while maintaining compatibility with existing deployments.
"""
