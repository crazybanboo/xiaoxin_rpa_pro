# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based RPA (Robotic Process Automation) software called "Xiaoxin RPA Pro" that supports image recognition, mouse automation, window management, and workflow execution. The project is designed to run on Windows and uses Win32 APIs for system interaction.

## Environment Setup

- **Virtual Environment**: Use `.env\Scripts\activate.ps1` to activate the virtual environment (PowerShell)
- **Python Version**: 3.8+
- **Platform**: Windows 10/11 (Win32 API support required)
- **Important**: All bash operations should be converted to PowerShell operations

## Common Commands

### Development Commands
```powershell
# Activate virtual environment
.env\Scripts\activate.ps1

# Run the application (interactive mode)
python main.py

# Run specific workflow
python main.py -w basic_example
python main.py -w wxwork_auto --config config/wxwork_strategy.yaml

# Enable debug mode
python main.py -d --log-level DEBUG
```

### Testing Commands
```powershell
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Generate test coverage report
pytest --cov=core --cov-report=html
```

### Code Quality Commands
```powershell
# Code formatting
black .

# Linting
flake8

# Type checking
mypy core/
```

### Build Commands
```powershell
# Build standalone executable
.\build.ps1

# Build optimized version
.\build_optimized.ps1
```

## Architecture Overview

### Core Modules (`core/`)
- **config.py**: Configuration management (YAML/JSON support)
- **logger.py**: Logging system with rotation support and relative path display
- **vision.py**: Computer vision engine using OpenCV for template matching
- **mouse.py**: Mouse automation controller with failsafe mechanisms
- **window.py**: Windows window management using Win32 APIs
- **template.py**: Multi-resolution template management system
- **workflow.py**: Workflow engine with step-based execution framework
- **utils.py**: Utility functions including cache cleaning and sleep functions

### Workflow System
- **Base Classes**: `BaseWorkflow` and `WorkflowStep` provide the foundation
- **Step Types**: Support for loops, conditional jumps, and custom steps
- **Execution Context**: Shared context between workflow steps
- **Error Handling**: Built-in retry mechanisms and error screenshots

### Template Management
- **Multi-Resolution Support**: Automatic template selection based on screen resolution
- **Directory Structure**: `templates/{workflow_name}/{resolution}/` organization
- **Supported Formats**: PNG, JPG, JPEG, BMP
- **Auto-Resolution**: Automatically selects best matching template for current resolution

### Configuration System
- **File Formats**: Supports both YAML and JSON configurations
- **Hierarchical**: Nested configuration with section-based organization
- **Runtime Override**: Command-line arguments can override config values
- **Validation**: Built-in configuration validation

## Key Workflows

### Built-in Workflows (`workflows/`)
- **basic_example.py**: Simple demonstration workflow
- **wxwork.py**: Enterprise WeChat automation workflows (includes cache cleaning, auto/semi-auto modes)

### Workflow Development Pattern
1. Inherit from `BaseWorkflow`
2. Define `workflow_name` class attribute
3. Implement `_setup()` method to define workflow steps
4. Each step inherits from `WorkflowStep` and implements `execute()` method

## Template Structure

```
templates/
├── {workflow_name}/
│   ├── 1920x1080/          # Full HD templates
│   ├── 3840x2160/          # 4K templates
│   ├── template_config.json
│   └── README.md
```

## Development Guidelines

### Adding New Workflows
1. Create new Python file in `workflows/` directory
2. Follow the naming convention: `{workflow_name}.py`
3. Implement required workflow steps as separate classes
4. Create corresponding template directories with appropriate resolutions

### Configuration Updates
- Default configuration is in `config/default.yaml`
- Use hierarchical structure for new config sections
- Update documentation when adding new configuration options

### Testing Strategy
- Unit tests for individual components
- Integration tests for workflow execution
- GUI tests marked with `@pytest.mark.gui`
- Slow tests marked with `@pytest.mark.slow`

### Error Handling
- All modules inherit from `LoggerMixin` for consistent logging
- Use structured error messages with context
- Implement graceful degradation where possible
- Screenshot capture on workflow errors when enabled

## Important Notes

- **Windows-Specific**: Project uses Win32 APIs and is designed for Windows
- **PowerShell Environment**: All command-line operations should use PowerShell syntax
- **F12 Hotkey**: Built-in emergency stop functionality via F12 key
- **Resolution Awareness**: Templates and workflows should consider multiple screen resolutions
- **Cache Management**: Enterprise WeChat workflows include automatic cache cleaning functionality