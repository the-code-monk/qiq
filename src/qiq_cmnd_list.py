"""This class handles qiq -l|--list command.

It prints all the installed packages.

Example:
--------
qiq --list  # Prints all the installed packages.
qiq --list onnx* torch*  # Prints all the installed packages starts with onnx & torch.
qiq --list onnx numpy  # Prints installed packages with exact name.
"""

__version__ = "0.0.2"

# python imports
from typing import List

# project imports
import qiq_config as C
import qiq_utils as utils


class QiQ_Cmnd_List:
    
    def run(self, packages: List[str]) -> None:
        """List installed packages.

        if packages is empty then it will list all the packages
        installed explicitly in current environment.

        if packages is not empty then it will list both types
        of packages. (explicit & implicit)

        Parameters
        ----------
        packages: List[str]
            Example: ['numpy', ''pytorch*' ...]
            numpy = Exact package name.
            pytorch* = Package name starts with.
        """
       
        installed_packages = sorted(utils.load_installed_packages())
       
        # List all packages if user is passing only list cmnd
        if not packages and installed_packages:
            print(C.GREEN + "\nListing all installed packages...")
            for pkg in installed_packages:
                name, op, ver = utils.get_requirement_info(pkg)
                print(f"{C.YELLOW}{name: <25}{C.CYAN}{ver: <5}")
            print(f"\n{C.YELLOW}Total packages : {C.RESET}{len(installed_packages)}")
            return
        
        # List filtered packages. Example: numpy* onnx
        filter_pkgs = []
        for pkg in packages:
            for instl_pkg in installed_packages:
                name, op, ver = utils.get_requirement_info(instl_pkg)
                if pkg.endswith('*') and name.startswith(pkg[0:-1]) or pkg == name:
                    filter_pkgs.append(instl_pkg)
          
        # Print filtered packages
        if filter_pkgs:
            print('\n' + C.GREEN + "Installed packages...")
            for p in filter_pkgs:
                utils.print_specifier(p)

        if not filter_pkgs:
            print(f"\n{C.YELLOW}Message : {C.RESET}No packages found.")
