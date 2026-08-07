"""This class handles qiq -p|--projects command.

It prints all the list of paths (projects) where qiq has been initiated.
When ever you use the --require command, qiq stores the path of the folder
as a project. This is how qiq tracks of all the projects and maintains it's
packages used by various projects.

Example:
--------
qiq --projects
"""

__version__ = "0.0.2"

# python imports
import os

# Project Imports
import qiq_config as C
import qiq_utils as utils

class QiQ_Cmnd_Projects:

    def run(self) -> None:
                
        paths = utils.load_projects()
        
        missing_paths = []
        # Each path points to a qiq projects directory
        print(f"{C.GREEN}\nListing {len(paths)} projects.\n")
        for folder in paths:
            # Check if path exists
            if not os.path.isdir(folder):
                print(C.RED + "Missing : " + C.RESET + str(folder))
                missing_paths.append(folder)
            else:
                print(C.YELLOW + "Exists  : " + C.RESET + str(folder))
        print()

        if missing_paths:
            answer = input("Do you want to permanently purge missing paths in projects? (yes/no): ").lower()
            if answer == "yes" or answer == "y":
                # Creat ne paths without missing paths.
                new_paths = [item for item in paths if item not in missing_paths]
                # Update projects.json
                utils.save_projects(new_paths)
                