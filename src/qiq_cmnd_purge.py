"""This class handles qiq -c|--clean command.

It purges unwanted packages or the packages not used so far
by any projects.

Example:
--------
qiq --clean
"""

__version__ = "0.0.1"

# python imports
from typing import List
import os
import shutil
import platform

# Project Imports
import qiq_config as C
import qiq_utils as utils

M1 = "{C.RED}Error : {C.RESET}{} is not writable. Please unable it's write access."

class QiQ_Cmnd_Purge:

    def run(self):
        """"""
        # ℹ️ NOTE
        # We can only uninstall packages those are explicitly
        # installed by qiq. User cannot install dependency
        # packages.
        
        # 👉 Load all installed packages from projects cache
        installed_packages = utils.load_installed_packages()
        
        # 👉 If no packages are installed
        if not installed_packages:
            print(f"{C.YELLOW}\nMessage: {C.RESET}No packages installed.\n")
            exit()
        
        # 👉 Load all project paths & check if any project path is missing.
        proj_paths = utils.load_projects()

        plat = platform.system().lower()

        all_packages = []
        num_projects = 0
        for project in proj_paths:
            json_config = os.path.join(project, '.qiq', plat + '.json')
            if os.path.isfile(json_config):
                data = utils.load_json(json_config)
                num_projects += 1
                all_packages.extend(data['packages'])

        all_packages = list(set(all_packages))

        unused_pkgs = [x for x in installed_packages if x not in all_packages]

        print()
        print(f"{C.YELLOW}Total installed packages : {C.RESET}{len(installed_packages)}")
        print(f"{C.YELLOW}Total packages in {C.RESET}{num_projects}{C.YELLOW} projects : {C.RESET}{len(all_packages)}")
        print(f"{C.YELLOW}Total unused packages : {C.RESET}{len(unused_pkgs)}")
        print()
        for pkg in sorted(unused_pkgs):
            utils.print_specifier(pkg, True)
      
        # 👉 Purge unused packages
        if unused_pkgs:
            print(C.GREEN + "\nUnused packages...\n")
            utils.delete_packages(unused_pkgs)          
