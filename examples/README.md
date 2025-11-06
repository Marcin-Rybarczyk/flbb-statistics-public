# FLBB Statistics - Examples

This directory contains example scripts demonstrating various features of the FLBB Statistics application.

## Available Examples

### MongoDB Integration

**File:** `mongodb_usage_example.py`

Demonstrates how to use the MongoDB integration to store and query basketball game data.

**Usage:**
```bash
python examples/mongodb_usage_example.py
```

**Requirements:**
- pymongo installed (`pip install pymongo`)
- Optional: MongoDB running locally or MongoDB Atlas connection

**What it demonstrates:**
- Checking if MongoDB is available
- Basic connection handling
- For full examples, see `tests/test_mongodb.py`

## Additional Resources

- **Full Test Suite**: `tests/test_mongodb.py` - Comprehensive MongoDB integration tests
- **Documentation**: `docs/MONGODB_INTEGRATION.md` - Complete setup and usage guide
- **Configuration**: See `.env.example` for environment variable setup

## Creating New Examples

When adding new examples:

1. Create a descriptive filename (e.g., `feature_name_example.py`)
2. Add comprehensive docstrings
3. Handle cases where optional dependencies are missing
4. Update this README with the new example
5. Make the file executable: `chmod +x examples/your_example.py`
