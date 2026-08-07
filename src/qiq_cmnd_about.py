"""This class handles qiq -a|--about command.

It prints a short information about qiq.

Example:
qiq --about
"""

__version__ = "0.0.2"

# python imports
import os
import sys

# Project Imports
import qiq_config as C
from qiq_utils import display_error

class QiQ_Cmnd_About:

    def run(self):

        # 👉 This env var is set by qiq.bat on windows and qiq on linux.
        qiq_dir = os.getenv('QIQ_DIR')
        
        # Make sure it exists
        if not qiq_dir:
            display_error(f"{C.RED}Error : {C.RESET}QIQ_DIR environment variable not found.")  # 🔥
        
        # Get qiq version from VERSION file
        version_file = os.path.join(qiq_dir, "VERSION")
        print()
        print(f"{C.YELLOW}Python      : {C.RESET}{sys.version}")
        
        with open(version_file, 'r') as file:
            version = file.readline().strip()
            print(f"{C.YELLOW}QiQ Version : {C.RESET}{version}")
        
        print(f"{C.YELLOW}Web         : {C.RESET}https://github.com/the-code-monk/qiq")
        print(f"{C.YELLOW}Author      : {C.RESET}Prashant Saxena")
