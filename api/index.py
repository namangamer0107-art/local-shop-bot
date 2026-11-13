import os
import sys

# Ensure root directory is in sys.path for Vercel Serverless Function imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import app
