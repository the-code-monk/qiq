"""The main qiq package importer.

When you use "import qiq" at the top of your main python file,
This file executes and add path of all the packages defined in qiq.json
in .qiq directory.
"""

__version__ = "0.2.0"

# python imports
import sys
import os
import site
import glob
import json
import configparser

import qiq_config as C
import qiq_utils as utils
from qiq_cmnd_require import QiQ_Cmnd_Require


class QiQ:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.qiq_cmnd_require = QiQ_Cmnd_Require()

    def get_package_path(self, package: str) -> [bool , str]:
        """Create package path from name.
        
        Parameters
        ----------
        package : str
            Name of the package. Example: numpy==2.3.4
        
        Returns
            [bool, str]
            True, if a .pth file exists in package direcrory else False &
            the path of the package in qiq-packages directory. 
        """
        python_path = sys.prefix
        try:
            name, version = package.split("==")
        except Exception as e:
            print("Error : Unable to parse package specifier.")
            print("Error : It must be in <name>==<version> format.")
            print(f"Error : Package found = {package}")
            sys.exit()

        package_path = os.path.join(python_path, 'qiq', 'qiq-packages', name, version)
        # If a .pth file exists in the package directory then 
        # at the time of importing this package,
        # it's path will be added to  site.addsitedir
        pth_files = glob.glob(os.path.join(package_path, "*.pth"))
        status = True if pth_files else False
        return status, package_path

    def remove_site_packages(self):
        """Remove site-packages to prevent importing modules.

        site-packages contains only modules required to run qiq.
        If you need any of those modules in your project then install
        using qiq and use them.
        """
        
        # Step 1: Remove site-packages from paths
        sys.path = [p for p in sys.path if 'site-packages' not in p]
        
        # Step 2: Clear already imported modules
        for name, module in list(sys.modules.items()):
            try:
                if hasattr(module, '__file__') and module.__file__ and 'site-packages' in module.__file__:
                    del sys.modules[name]
            except Exception:
                pass
        
        # Step 3: Clear importer cache
        sys.path_importer_cache.clear()

    def save_req_txt_time(self) -> None:
        """Save requirements.txt modified time"""
        mtime = str(os.stat(self.req_txt_path).st_mtime)
        utils.write_txt_file(self.req_txt_time_path, mtime)

    def load_req_txt_time(self) -> float:
        """Load requirements.txt modified time"""
        mtime = 0.0
        with open(self.req_txt_time_path, "r", encoding="utf-8") as f:
            mtime = f.readline()
        mtime = 0.0 if mtime == '' else mtime
        try:
            mtime = float(mtime)
        except ValueError as e:
            utils.display_error(f"{C.RED}Error: {C.RESET}{e}")
            exit()
        return mtime

    def is_req_txt_changed(self) -> bool:
        """Check if requirements.txt has changed since last save.
        
        Returns
        -------
        bool
            True if changed else False
        """
        old_time = self.load_req_txt_time()
        new_time = os.stat(self.req_txt_path).st_mtime
        return old_time != new_time

    def auto_load_requirements_txt(self):
        """Auto load requirements.txt"""

        # If auto requirement.txt parsing is True
        auto_require = self.config["DEFAULT"].get("QIQ_AUTO_REQUIRE", "1")
        if auto_require == "0":
            return

        # requirements.txt doesn't exists then return
        if not os.path.exists(self.req_txt_path):
            return

        # requirements.txt exists but qiq.json doesn't. First auto import
        qiq_json = os.path.join(os.getcwd(), C.QIQ_VENV_DIR, C.QIQ_IMPORTER_FILE)
        if os.path.exists(self.req_txt_path) and not os.path.exists(qiq_json):
            print(f"\n{C.YELLOW}Message: {C.RESET}{self.req_txt} found. Creating package importer...")            
            self.qiq_cmnd_require.run(self.req_txt_path)
            self.save_req_txt_time()
            return

        # requirements.txt exists but req_time.txt doesn't. First auto import
        if os.path.exists(self.req_txt_path) and not os.path.exists(self.req_txt_time_path):
            print(f"\n{C.YELLOW}Message: {C.RESET}{self.req_txt} found. Creating package importer...")            
            self.qiq_cmnd_require.run(self.req_txt_path)
            self.save_req_txt_time()
            return

        # requirements.txt & req_time.txt exists and req_time.txt has changed
        if os.path.exists(self.req_txt_time_path) and os.path.exists(self.req_txt_path) and self.is_req_txt_changed():
            print(f"\n{C.YELLOW}Message: {C.RESET}{self.req_txt} has changed.  Creating package importer...")            
            self.qiq_cmnd_require.run(self.req_txt_path)
            self.save_req_txt_time()
            return

    def load_qiq_ini(self):
        """Load qiq.ini file
        """

        qiq_ini_path = os.path.join(os.getcwd(), C.QIQ_VENV_DIR, C.QIQ_INI_FILE)
        
        # Check if qiq.ini exists or not
        if not os.path.exists(qiq_ini_path):
            return False
        
        # Load qiq.ini
        try:
            self.config.read(qiq_ini_path)
        except configparser.ParsingError as e:
            utils.display_error(f"{C.RED}Error : {e}")

        self.req_txt = self.config["DEFAULT"].get("QIQ_REQUIREMENTS_TXT", "requirements.txt")
        self.req_txt_path = os.path.join(os.getcwd(), self.req_txt)
        self.req_txt_time_path = os.path.join(os.getcwd(), C.QIQ_VENV_DIR, C.QIQ_REQ_TIME_TXT_FILE)

        return True

    def version_check(self, version:str):
        """Match QiQ version vs qiq.json version"""
        qiq_version = utils.get_qiq_version()
        if version != qiq_version:
            print(f"\n{C.RED}Error : {C.RESET}Version mismatch")
            print(f"\n{C.YELLOW}QiQ Version : {C.RESET} {qiq_version}")
            print(f"\n{C.YELLOW}Project Version : {C.RESET} {version}")
            print(f"\n{C.YELLOW}Info : {C.RESET} Please run qiq -r requirements.txt")
            exit()

    def validate_project_json(self, data: dict):
        """Validate project's qiq.json"""
        if not "version" in data.keys():
            print(f"\n{C.RED}Error : {C.RESET}Please update QiQ.")
            exit()
        self.version_check(data["version"])

    def run(self):
        """Summary"""

        # Load qiq.ini
        if not self.load_qiq_ini():
            print(f"\n{C.RED}Error : {C.RESET}Missing {C.QIQ_INI_FILE}")
            print(f"{C.RED}Error : {C.RESET}Please create the virtual environment again.\n")
            exit()

        # Auto create qiq.json based on requirements.txt changes
        self.auto_load_requirements_txt()

        loader_path = os.path.join(os.getcwd(), C.QIQ_VENV_DIR, C.QIQ_IMPORTER_FILE)

        if not os.path.isfile(loader_path):
            print("Error: qiq package importer qiq.json not found.")
            print("You can create a qiq package importer using:")
            print("qiq --require requirements.txt")
            exit()

        if os.path.isfile(loader_path):
            pth_exists = False
            missing_pkgs = []
            data = utils.load_json(loader_path)
            self.validate_project_json(data)
            for pkg in data['packages']:
                pth_exists, pkg_path = self.get_package_path(pkg)
                if os.path.exists(pkg_path):
                    sys.path.append(pkg_path)
                    if pth_exists:
                        site.addsitedir(pkg_path)
                else:
                    missing_pkgs.append(pkg)
                pth_exists = False

            if missing_pkgs:
                print("Error: These packages must have been removed from qiq but this project requires them.")
                print("       Please install them again.")
                for p in missing_pkgs:
                    print(p)

            # Check if we should remove site_packages import
            #if self.config["DEFAULT"].get("QIQ_IMPORT_FROM_SITE_PACKAGES", "0") == "0":
                #self.remove_site_packages()

def get_package_dir(name: str, version: str) -> str:
    """Return package path from name & version.
    
    Parameters
    ----------
    name : str
        Name of the package. Example: numpy
    version: str
        Version of the package. Example: 2.3.4
    
    Returns
        The path of the package in qiq-packages directory. 
    """
    python_path = sys.prefix
    directory =  os.path.join(python_path, C.QIQ_DIR, C.QIQ_PACKAGES_DIR, name, version, name)
    if not os.path.exists(directory):
        print("Error : Path does not exists.")
        print(f"Error : {directory}")
        sys.exit()

    return directory

# Run package importer
QiQ().run()
