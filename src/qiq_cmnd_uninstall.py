"""This class handles qiq -u|--uninstall command.

It uninstalls python pacakges from repository.

Example:
--------
qiq --uninstall numpy==2.3.4 onnx==2.2.2

ℹ️ NOTE
QiQ manages multiple versions of same packages. That's why you must specify
the exact installed version which you are trying to uninstall.
"""

__version__ = "0.0.1"

# python imports
from typing import List
import os

# project import
import qiq_config as C
import qiq_utils as utils

class QiQ_Cmnd_UnInstall:

    def run(self, packages: List[str]):
        """"Uninstall a list of packages.

        Parameters
        ----------
        packages: List[str]
            Example: ['numpy==2.3.2', ''pytorch==2.3.4' ...]
        """
        
        # ℹ️ NOTE
        # We can only uninstall packages those are explicitly
        # installed by qiq. User cannot install dependency
        # packages.

        # 👉 First check for all package's requirement string.
        # User must provide package with version in order to remove.
        for pkg in packages:
            name, operator, version = utils.get_requirement_info(pkg)
            if operator != "==":
                utils.trace_error()
                print(f"{C.RED}Error : {C.RESET}Please use == operator only.")
                print(f"{C.YELLOW}Tip   : {C.RESET}numpy==2.4.3")
                exit()

        # 👉 Load all the installed packages from installed.json
        data = utils.load_installed_packages()

        # 👉 Nothing is installed so far
        if not data:
            print(f"{C.YELLOW}\nMessage: {C.RESET}No packages installed.\n")
            exit()
            
        # 👉 Check if the packages we are about to uninstall, must exists
        # in main packages.
        pkg_to_delete = []
        newline = ''
        for pkg in packages:
            if pkg not in data:
                newline = '\n'
                print(f"{C.YELLOW}Message : {utils.print_specifier(pkg, False)} {C.RESET}is not installed.")
            else:
                pkg_to_delete.append(pkg)

        # 👉 Load all project paths & check if any project path is missing.
        proj_paths = utils.load_projects()

        # 👉 Check if packages or their dependencies are not used
        # in any project. Only then we can remove it.
        final_delete_pkgs = []
        for pkg in pkg_to_delete:
            status = utils.can_package_uninstalled(pkg, proj_paths)
            if status:
                final_delete_pkgs.append(pkg)
        
        # 👉 Finally delete them.
        if final_delete_pkgs:
            print(newline + C.GREEN + "Uninstalling packages...\n")
            utils.delete_packages(final_delete_pkgs)