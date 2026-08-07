"""This class handles qiq -r|--require command.

This is the most important command in qiq.
It parse the contents of requirements.txt and install packages in qiq's unified
package repository. It also creates pkg.json file in the current folder's .qiq
directory which is also the virtual environment directory for qiq.

Example:
--------
qiq --require requirements.txt
qiq --require --refresh --ttl 864000 requirements.txt
@ See QiQ_Package_Cache.py
--refresh -> Force refresh package cache
--ttl <seconds> -> If package in cache is older then ttl then refresh
"""

__version__ = "0.0.2"

# python imports
from typing import List
from pathlib import Path
import os
import glob
import json
from collections import defaultdict
from pprint import pprint

from packaging.version import Version

# Project Imports
import qiq_config as C
from qiq_cmnd_install import QiQ_Cmnd_Install
from qiq_req_txt_parser import QiQ_Req_Txt_Parser
from qiq_package_resolver import QiQ_Package_Resolver
from qiq_package_cache import QiQ_Package_Cache
import qiq_utils as utils

class QiQ_Cmnd_Require:

    def __init__(self):
        """"""
        self.qiq_rec_txt_parser  = QiQ_Req_Txt_Parser()
        self.qiq_cmnd_install = QiQ_Cmnd_Install()

    def _add_platform_json_path_to_projects(self, dir_name: str) -> None:
        """Add dir_name path to projects cache.
           
        Parameters
        ----------
        dir_name: str
            path of project directory
        """
  
        # Load all projects
        qpc = QiQ_Package_Cache()
        proj_paths = qpc.get_projects()
        # Add project path
        proj_paths.append(str(dir_name))
        proj_paths = list(set(proj_paths)) # No duplicate paths
        # Save projects in cache
        qpc.set_projects(proj_paths)
        
    def run(self, 
        file_name: str,
        ttl: float=0.0,
        refresh: bool=False
        ) -> None:
        """Parse requirements.txt and create qiq package importer.
        
        Parameters
        ----------
        file_name : str
            Path of requirements.txt
        ttl: float
            Seconds before a cached version list is considered stale
            default: 86400 or 24h
        force_refresh: bool
            Ignore cached PyPI version lists and re-check them now, regardless of --ttl.
            requires_dist entries are immutable and are never affected by this.
        """
        
        # 👉 Check if file exists
        if not os.path.isfile(file_name):
            utils.trace_error()
            print(f"{C.RED}Error : {C.YELLOW}{file_name} {C.RESET} does not exists.")
            exit()

        # 👉 Parse requirements.txt
        all_packages = self.qiq_rec_txt_parser.parse(Path(file_name))
        
        # 👉 Install all the packages
        all_pkgs_n_deps = self.qiq_cmnd_install.run(all_packages, ttl, refresh)
     
        # 👉 Create .qiq virtual environment directory
        os.makedirs(C.QIQ_VENV_DIR, exist_ok=True)
        qiqimporter_path = os.path.join(C.QIQ_VENV_DIR, C.QIQ_IMPORTER_FILE)

        version = utils.get_qiq_version()
        data = {
            "version" : version,
            "packages": all_pkgs_n_deps
        }

        # 👉 Write qiq.json file
        utils.save_json(data, qiqimporter_path)
    
        # 👉 Add directory to projects cache for this python environment.
        self._add_platform_json_path_to_projects(Path(__file__).resolve().parent)

        # 👉 Done
        print(f"\n{C.YELLOW}Message : {C.RESET}A qiq package importer has been created in {C.CYAN}.qiq {C.RESET}directory.\n")
        