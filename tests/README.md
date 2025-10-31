# Test Scripts

This directory contains development and debugging scripts used during development. These scripts are **not required** for normal operation of the financial research agent.

## Purpose

These test scripts were created to:
- Debug the edgartools integration
- Test MCP tool connectivity
- Verify financial statement extraction
- Compare different data extraction approaches

## Files

- `test_*.py` - Various integration tests for EDGAR data extraction
- `debug_*.py` - Debugging scripts for troubleshooting
- `*.json` - Sample API responses for testing

## Running Tests

These scripts are standalone and can be run directly:

```bash
cd tests
python test_edgartools_complete.py
```

**Note:** Tests require:
- Active virtual environment (`.venv`)
- `SEC_EDGAR_USER_AGENT` environment variable set
- Dependencies installed (`uv sync` or `pip install -r requirements.txt`)

## For Development Only

These files are not part of the main application and can be safely ignored or deleted for production deployments.
