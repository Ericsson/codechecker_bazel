"""
Setup module paths and environment variables for the functional tests.
"""

import os
import sys

# Setup the required environment variables for the tests.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
