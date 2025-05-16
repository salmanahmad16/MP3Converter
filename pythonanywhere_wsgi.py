import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/mp3Converter'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import your Flask app
from app import app as application  # noqa

# This is important for PythonAnywhere
application = app
