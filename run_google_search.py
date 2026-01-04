#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick launcher for Google Image Search"""

import os
import sys

# Set credentials
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDrYrPPriGEzBRqetNEhjMDR4g27xAIubo'
os.environ['GOOGLE_CX'] = 'e70dd3e1776df4ad1'

# Import and run the main script
sys.path.insert(0, 'scripts')
from google_image_search import main

if __name__ == "__main__":
    main()
