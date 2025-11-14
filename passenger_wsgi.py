import sys, os

# Ensure the parent directory is in the path for package imports
sys.path.insert(0, os.path.dirname(__file__))

from src.app import app as application
