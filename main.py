#!/usr/bin/env python3
"""
"""
import sys
from lets_talk.pipeline import main
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    sys.exit(main())
