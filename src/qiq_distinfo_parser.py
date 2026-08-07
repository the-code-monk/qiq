"""This class handles creation of console scripts if exists
inside dist-info folder of a package and used by qiq_cmnd_install.py.
"""

import os
from sys import platform
import configparser
from pathlib import Path
from distlib.scripts import ScriptMaker
from distlib.util import get_export_entry
import sysconfig

# Project Imports
import qiq_config as C
import qiq_utils as utils

class QiQ_Distinfo_Parser:

    def __init__(self):
        """Constructor"""
        self.package_folder = None
        self.files_to_delete = []

    def write_uninstaller(self):
        """Write the list of files in uninstall.txt"""

        if not self.files_to_delete or not self.package_folder:
            return

        # Join all the file names
        txt = "\n".join(self.files_to_delete)
        
        # Create file path of uninstaller
        uninstaller = os.path.join(self.package_folder, "uninstall.txt")
        
        # Write
        utils.write_txt_file(uninstaller, txt)
        
        # Clean
        self.files_to_delete = []

    def get_distinfo_folder(self, folder: str) -> None | str:
        """Get the name of the dist-info folder inside package folder.
        
        Parameters
        ----------
        folder : str
            Package folder inside qiq-packages
        
        Returns
        -------
        None | str
            Name of the dist-info folder if found or None
        """
        base = Path(folder)

        suffix = ".dist-info"

        dirs = [p for p in base.iterdir() if p.is_dir() and p.name.endswith(suffix)]

        return None if not dirs else dirs[0]

    def read_entry_points(self, dist_info_folder: str):
        """Read entry_points.txt and create console scripts
        
        Returns
        -------
        None
        """

        entry_points_txt = os.path.join(dist_info_folder, "entry_points.txt")
        if not os.path.exists(entry_points_txt):
            return

        cp = configparser.ConfigParser()

        try:
            cp.read(entry_points_txt, encoding="utf-8")
        except configparser.ParsingError as e:
            utils.display_error(f"{C.RED}Error : {e}")

        if not cp.has_section("console_scripts"):
            return

        for name, target in cp["console_scripts"].items():
            self.make_console_script(name, target)

    def make_console_script(self, name: str, target: str) -> None:
        """Create console scripts.
        
        Parameters
        ----------
        name : str
            Name of the script
        target : str
            Script path
        """

        scripts_dir = sysconfig.get_path("scripts")
        maker = ScriptMaker(None, scripts_dir)

        maker.clobber = True           # overwrite if exists
        if platform == "win32":
            maker.add_launchers = True     # 👈 THIS IS THE KEY
        maker.set_mode = True          # optional but recommended

        entry = get_export_entry(f"{name} = {target}")
        post_interp = b''
        shebang = maker._get_shebang('utf-8', post_interp)
        script = maker._get_script_text(entry).encode('utf-8')
        #scriptnames = maker.get_script_filenames(entry.name)
        scriptnames = [entry.name]

        new_script = []
        for s in script.decode().split('\n'):
            if s == "import sys":
                new_script.append("import qiq")
                new_script.append("import sys")
                new_script.append(f'sys.path.append("{self.package_folder}")')
            else:
                new_script.append(s)

        script = "\n".join(new_script).encode("utf-8")
        maker._write_script(scriptnames, shebang, script, [], 'py')

        # Add file to delete list which will be used at the time of uninstallation
        ext = ".exe" if platform == "win32" else ""
        self.files_to_delete.append(os.path.join(scripts_dir, entry.name + ext ))

    def run(self, package_folder: str) -> None:
        """Execute
        
        Parameters
        ----------
        package_folder : str
            The path of the package folder inside qiq-packages

        """
        self.package_folder = package_folder.replace("\\", "/")
        dist_info_folder = self.get_distinfo_folder(self.package_folder)
        
        if dist_info_folder:
            self.read_entry_points(dist_info_folder)

        self.write_uninstaller()

