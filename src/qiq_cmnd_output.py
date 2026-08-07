"""This class handles qiq -o|--output command.

It outputs a new requirments based on existing one by sovling
package specfiers.

Let's assume the contents of requirements.txt are
numpy>=2.3.4
onnx>=2.0.0

This command resolves the package requirements and create a new 
file with fixed set of packages.

Example:
--------
qiq --output requirements.txt output.txt

The content of output.txt will some something like this:
numpy==2.3.4
onnx==2.0.2
"""

__version__ = "0.0.3"

# python imports
from typing import List
from pathlib import Path
import os

# Third Party imports
from packaging.requirements import Requirement

# project imports
import qiq_config as C
from qiq_package_cache import QiQ_Package_Cache
from qiq_req_txt_parser import QiQ_Req_Txt_Parser
from qiq_package_resolver import QiQ_Package_Resolver
import qiq_utils as utils

M1 = "{C.RED}\nError : {C.YELLOW}{} {C.RESET} does not exists.\n"
M2 = "{C.YELLOW}Resolving : {} {C.RESET}--> {C.CYAN}{}"
M3 = "{C.RED}Error: {} {C.RESET}Unable to find any suitable version."

class QiQ_Cmnd_Output:

    def __init__(self):
        """Constructor"""
        self.qiq_req_txt_parser = QiQ_Req_Txt_Parser()

    def _is_package_in_requirements(self, packages: list[Requirement], package:str) -> bool:
        """"""
        root_name, root_version = package.split("==")
        for pkg in packages:
            if root_name == pkg.name:
                return True
        return False

    def run(self, file_names: List[str]) -> None:
        """Parse requirements.txt and creates another one with exact package requirements.
        
        Parameters
        ----------
        file_names : List[str]
            Path of requirements.txt and output.txt
        """

        # 👉 Check if the requirements.txt exists
        if not os.path.isfile(file_names[0]):
            utils.display_error(M1, file_names[0])

        all_packages = self.qiq_req_txt_parser.parse(Path(file_names[0]))

        if not all_packages:
            print(f"{C.RED}\nNo packages found in {file_names[0]}.\n")
            return

        # Resolve package tree
        # {pkg:[deps], pkg:[deps], ...}
        resolve_packages = QiQ_Package_Resolver(QiQ_Package_Cache.DEFAULT_TTL, False).get(all_packages)

        output_txt = ""
        for pkg, deps in resolve_packages.items():
            if self._is_package_in_requirements(all_packages, pkg):
                output_txt += pkg + '\n'

        # Write to file
        utils.write_txt_file(file_names[1], output_txt.strip())
        print(f"{C.YELLOW}\nDone.")   
        