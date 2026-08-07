"""This class handles qiq -d|--detail command.

It prints details about packages passed as arguments.
Deatils:
--------
Latest version
Summary
Installed versions (Explixit & Implicit)
Installed versions used in projects.

Example:
--------
qiq --detail numpy onnx
"""

__version__ = "0.0.3"

# Python Imports
from typing import List
import os
import json
from pathlib import Path
from pathlib import PurePath

# Project Imports
import qiq_config as C
import qiq_utils as utils

class QiQ_Cmnd_Detail:
    
    def _print_installed_versions(self, name: str, version: str) -> None:
        """Print all the installed versions of package with name.
        
        Parameters
        ----------
        name : str
            Name of the package.
        version : str
            Latest version of the package from PyPI.
        """

        qiq_packages_dir = utils.get_qiq_dir(C.QIQ_PACKAGES_DIR)
        pkg_path = os.path.join(qiq_packages_dir, name)
        qiq_config_dir = utils.get_qiq_dir(C.QIQ_CONFIG_DIR)
        
        main_pkgs = utils.load_installed_packages()    

        # 👉 If package in not installed
        if not os.path.exists(pkg_path):
            print(f"{C.YELLOW}Message : {C.CYAN}{name}{C.RESET} is not installed.")
            return
        
        # 👉 If package in installed
        dirs = sorted([p.name for p in Path(pkg_path).iterdir() if p.is_dir()])
        if dirs:
            print(f"{C.GREEN}In qiq-packages...")
            for d in dirs:
                is_inst = "Installed" if (name+"=="+d) in main_pkgs else "Dependency"
                latest = "(Latest)" if d == version else ''
                print(f"{C.YELLOW}{name}{C.RESET}=={C.CYAN}{d}{C.RESET} {is_inst} {latest}")

    def _is_package_in_project(self, file_name: str, name: str) -> str:
        """Return if package by name exists in pkg.json importer file.
        
        Parameters
        ----------
        file_name : str
            pkg.json file.
        name : str
            Name of the package.

        Returns:
            name==version if exists in file else ''
        """
        data = utils.load_json(file_name)

        if not "packages" in data:
            print(f"{C.RED}Old format error : {C.YELLOW}{file_name}, {C.RESET}Please update it.")
            return

        for pkg in data['packages']:
            pkg = pkg.strip()
            pkg_name, version = pkg.split("==")
            if name == pkg_name:
                return pkg
        return ''

    def _print_pacakage_used_in_projects(self, name: str) -> None:
        """Print package uses in all the projects handled by qiq.
        
        Parameters
        ----------
        name : str
            Name of the package.
        """

        all_pkgs = {}
        proj_paths = utils.load_projects()
        for p in proj_paths:
            if not os.path.isfile(p):
                print(f"{C.RED}Error: {C.RESET}Path {p} does not exists in projects.json")
                continue
            pkg = self._is_package_in_project(p, name)
            if pkg:
                if pkg not in list(all_pkgs.keys()):
                    all_pkgs[pkg] = [p]
                else:
                    all_pkgs[pkg].append(p)                    
        
        if all_pkgs:
            print(f"{C.GREEN}Used in projects...")
            for pkg, projs in all_pkgs.items():
                name, version = pkg.split("==")
                print(f"{C.YELLOW}{name}{C.RESET}=={C.CYAN}{version}{C.RESET} ({len(projs)})")
                for path in projs:
                    pp = PurePath(path.strip())
                    folder = os.sep.join(list(pp.parts[0:-2]))
                    print(folder)

    def run(self, packages: List[str]) -> None:
        """List various information about packages.
        
        Parameters
        ----------
        packages : List[str]
            Example: ['numpy', ''pytorch' ...]
        """

        # 👉 At least one package is rquired.
        if not packages:
            utils.trace_error()
            print(f"{C.RED}Error : {C.RESET}No packages found for detail.")
            print(f"{C.YELLOW}Tip   : {C.RESET}qiq -detail numpy requests")

        for pkg in packages:
            json = utils.get_package_info_json(pkg, "")
            if not json:
                continue
            version = json["info"]["version"]
            summary = json["info"]["summary"]
            print(f"\n{C.YELLOW}{pkg}{C.RESET}=={C.CYAN}{version}{C.RESET} (Latest)")
            print(f"{C.YELLOW}Summary : {C.RESET}{summary}")
            print()
            self._print_installed_versions(pkg, version)
            print()
            self._print_pacakage_used_in_projects(pkg)
            if len(packages) >= 2:
                print("\n-------------------------------------------------------")
