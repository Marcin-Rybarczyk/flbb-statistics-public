#!/usr/bin/env python3
"""
Example script demonstrating MongoDB integration usage

This script shows how to use the MongoDB helper to store and query
basketball game data.

Usage:
    python examples/mongodb_usage_example.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mongodb_helper import (
    is_mongodb_available,
    MongoDBHelper
)


def example_check_availability():
    """Check if MongoDB is available."""
    print("\n" + "="*60)
    print("Example: Check MongoDB Availability")
    print("="*60)
    
    print(f"pymongo installed: {is_mongodb_available()}")
    
    if is_mongodb_available():
        import pymongo
        print(f"pymongo version: {pymongo.__version__}")


def main():
    """Run examples."""
    print("="*60)
    print("MongoDB Integration Usage Example")
    print("="*60)
    
    example_check_availability()
    
    print("\n" + "="*60)
    print("For more examples, see:")
    print("- tests/test_mongodb.py - Full test suite")
    print("- docs/MONGODB_INTEGRATION.md - Complete documentation")
    print("="*60)


if __name__ == '__main__':
    main()
