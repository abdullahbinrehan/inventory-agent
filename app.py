# This file is the entry point for Hugging Face Spaces.
# It simply runs the Streamlit app inside the ui/ folder.

import sys
import os

# Add the current directory to the path so we can import from ui/
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ui.app import * 