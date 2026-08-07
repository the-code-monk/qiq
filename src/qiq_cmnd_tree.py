"""This class handles qiq -t|--tree command.

It prints all the dependencies of given package.

Example:
--------
qiq --tree numpy==2.2.6
"""

__version__ = "0.0.2"

# pip imports
from packaging.requirements import InvalidRequirement, Requirement
from qiq_package_resolver import QiQ_Package_Resolver

# Project Imports
import qiq_config as C
import qiq_utils as utils

class QiQ_Cmnd_Tree:

    def run(self, package: str, ttl: float) -> None:
        """List all packages and their dependencies in current environment."""
        try:
            req = Requirement(package)
        except InvalidRequirement as e:
            utils.display_error("{C.RED}Error : {C.RESET}{}", e)

        utils.get_requirement_info(package)

        print(f"{C.GREEN}Info : {C.YELLOW}Fetching package and it's dependencies...")
        print()
        
        # Resolve package tree
        # {pkg:[deps], pkg:[deps], ...}
        tree = QiQ_Package_Resolver(ttl, False).show_tree(req)

        print(tree)