"""This file has various utility or helper functions."""

__version__ = "0.0.5"

# python imports
from typing import List, Tuple, Dict
import os
import sys
import json
import glob
import shutil
import platform
import traceback
from collections import Counter
from pathlib import PurePath, Path

# pip imports
import requests
import certifi
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from packaging.requirements import InvalidRequirement
from packaging.version import parse as parse_version_safe

# project imports
import qiq_config as C
from qiq_package_cache import QiQ_Package_Cache

session = requests.Session()

def trace_error(stack_pos: int = -2, line_add: int = 0):
    """Print traceback error (file and line number)
    
    Parameters
    ----------
    stack_pos : int, optional
        Stack position or file name.
    line_add : int, optional
        Line number of error
    """
    print()
    stack = traceback.extract_stack()[stack_pos]
    print(f"{C.RED}Trace : {C.YELLOW}{stack.filename}, line {C.CYAN}{stack.lineno+line_add}")

def display(var, *args):
    """Print formatted string with arguments.
    
    Parameters
    ----------
    var : Formatted string.
        Description
    *args
        Arguments in formatted string.
    """
    print(var.format(*args, C=C))

def display_error(var, *args):
    """Display formatted string as error & exit.
    
    Parameters
    ----------
    var : Formatted string
        Description
    *args
        Arguments in formatted string.
    """
    trace_error(-3, 0)
    print(var.format(*args, C=C))
    exit()    

def handle_error(func, path, exc_info):
    """shutil.rmtree handling error
    
    Parameters
    ----------
    func : TYPE
        Description
    path : TYPE
        Description
    exc_info : TYPE
        Description
    """
    trace_error()
    print(f"{C.RED}Error : {C.RESET}Unable to remove path")
    print(f"{C.RED}Path  : {C.RESET}{path}")
    print(f"{C.RED}Cmnd  : {C.RESET}shutil.rmtree")
    #subprocess.run(["lsof", "+D", path])
    exit()

def get_qiq_version():
    """Get QiQ version from version file at project root"""
    version = Path(__file__).resolve().parent.parent / "VERSION"
    with open(version, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines[0]

def get_python_path() -> str:
    """Get current python executable path.

    Returns: str
        Current python executable path.
    """
    return sys.prefix

def write_txt_file(file_name: str, txt: str) -> None:
    """Write text to file.
    
    Parameters
    ----------
    file_name : str
        Name of the file to write.       
    txt : str
        Text to write in file.
    """
    # Open a file named file_names[1] in write mode ('w') with UTF-8 encoding
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(txt)

def load_json(file_name: str) -> List:
    """Load json file and return data.
    
    Parameters
    ----------
    file_name : str
        JSON file to load.

    Raises:
        JSONDecodeError
    """
    data = []
    with open(file_name, 'r', encoding='utf-8') as file:
            # Deserialize the file content into a Python dictionary
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                trace_error()
                print(C.RED + "Error : " + C.RESET + "Unable to parse " + file_name)
                print(C.RED + "Error : " + C.RESET + str(e))
                exit()
    return data    

def save_json(data: Dict, file_name: str) -> None:
    """Write data in a json file. 
    
    Parameters
    ----------
    data : Dict
        Data to write as json.
    file_name : str
        In file to write.
    """

    with open(file_name, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)      

def load_installed_packages():
    """Load the list of all installed packages from cache"""
    qpc = QiQ_Package_Cache()
    return qpc.get_packages()

def update_installed_packages(packages: list) -> None:
    """Update installed packages list in cache.

    Parameters
        ----------
        packages: list
            Example: ['hello==1.1.1', 'world==2.2.2', ...]
    """

    # Load packages installation info.
    data = load_installed_packages()

    # Add package and it's dependencies
    data.extend(packages)

    # Make sure no duplicates
    data = list(set(data))

    # Update packages in cache
    qpc = QiQ_Package_Cache()
    qpc.set_packages(data)

def load_projects() -> List:
    """Load the list of all projects managed by qiq"""
    qpc = QiQ_Package_Cache()
    proj_paths = qpc.get_projects()
    return proj_paths

    is_proj_missing = False
    for path in proj_paths:
        # Check if path exists
        if not os.path.isfile(path):
            print(C.RED + "Missing : " + C.RESET + path)
            is_proj_missing = True

    if is_proj_missing:
        print()
        print(C.YELLOW + "Message : " + C.RESET + "Please fix the missing project paths first using:")
        print(C.YELLOW + "Message : " + C.RESET + "qiq -p")
        exit()

    return proj_paths

def save_projects(projects: list[str]):
    """"""
    qpc = QiQ_Package_Cache()
    qpc.set_projects(projects)

def get_package_path(specifier: str):
    """Get package directory in qiq-packages.

    Args:
        specifier: str
        Example: numpy==2.2.0
    """
    name, _, version = get_requirement_info(specifier)
    # Get current python path
    python_path = get_python_path()
    # Get package directory
    return os.path.join(
        python_path, C.QIQ_DIR, C.QIQ_PACKAGES_DIR, name, version)

def short_name(url: str):
    """Return short name of package from url.

    Example:
        url = http://www.example.com/charset_normalizer-3.4.7-cp310-cp310-macosx_10_9_universal2.whl
        returns charset_normalizer-3.4.7
    
    Parameters
    ----------
    url : str
        package url.
    """

    name_version_ext = "-".join(os.path.basename(url).split('-')[0:2])
    exts = {".whl": 4, ".zip": 4, ".tar.gz": 7}
    for e, l in exts.items():
        if name_version_ext.endswith(e):
            s = len(name_version_ext)
            return name_version_ext[0:s-l]
    # Fallback
    return name_version_ext

def get_requirement_info(specifier: str) -> Tuple[str, str, str]:
    """Get nane, operator & version from package specifier.

    Parameters
    ----------
    specifier: str
        Example: numpy==2.2.0

    Returns
    -------
    Tuple(str, str, str)
        (name, operator, version)

    Raises
    ------ 
    InvalidRequirement
        If invalid specifier is passed. Example: numpy==
    """
    try:
        req = Requirement(specifier)
    except InvalidRequirement as e:
        trace_error()
        print(f"{C.RED}Error : {C.RESET}Invalid requirement string: {specifier}")
        print(str(e))
        exit()
    name = req.name
    operator = ''
    version = ''
    if req.specifier:
        operator = list(req.specifier)[0].operator
        version = list(req.specifier)[0].version
    else:
        trace_error()
        print(f"{C.RED}Error : {C.RESET}Invalid requirement string: {specifier}")
        print(f"{C.YELLOW}Tip   : {C.RESET}Provide like this: numpy==2.3.4")
        exit()
    return name, operator, version    

def is_valid_specifier(specifier: str, msg: str) -> str | None:
    """Check if specifier is valid.

    Parameters
    ----------
    specifier: str
        Example: numpy==2.4.2
    msg: str
        Print msg in case exception is raised.

    Raises
    ------
    InvalidRequirement
    """
    try:
        Requirement(specifier)
    except InvalidRequirement as e:
        trace_error()
        print(C.RED + msg)
        print(C.RED + "Error : " + C.RESET + str(e))
        exit()

def print_specifier(specifier: str, print_it: bool=True) -> None:
    """Print or return package specifier or requirement string.
    
    Parameters
    ----------
    specifier : str
        Example: numpy==2.3.4
    print_it : bool, optional
        print or return as string.
    """
    name, operator, version = get_requirement_info(specifier)
    msg = (C.YELLOW + name + C.RESET + operator + C.CYAN + version)
    if print_it:
        print(msg)
    else:
        return msg

def print_package(name: str, operator: str, version: str, print_it: bool=True) -> None:
    """Print in colors
    
    Parameters
    ----------
    name : str
        Name of the package
    operator : str
        Operator
    version : str
        Version of the package
    print_it: bool
        If true print it else return it.

    Returns
    -------
    str | None
        Colored output.
    """

    msg = (C.YELLOW + name + C.RESET + operator + C.CYAN + version)
    if print_it:
        print(msg)
    else:
        return msg

def fetch_json(url: str) -> Dict:
    """Fetch package json from PyPI.

    Parameters
    ----------
    url: str
        Url of the python package json on PYPI.

    Returns
    -------
        Session responce as json.

    Raises
    ------
    IOError
        An error occurred accessing the smalltable.
    """
    try:
        resp = session.get(url, timeout=(3, 3), verify=certifi.where())
    except Exception as e:
        trace_error()
        print(f"{C.RED}Error : {C.RESET}Failed to fetch {url}.")
        print(f"{C.RED}Error : {C.RESET}Check you internet connection.")
        print(f"{C.RED}Error : {C.RESET}{e}")
        exit()
    if resp.status_code != 200:
        trace_error()
        pkg = PurePath(url).parts[-2]
        print(f"{C.RED}Error : {C.CYAN}{pkg} {C.RESET}package does not exists.")
        print(f"{C.RED}Error : {C.RESET}Failed to fetch {url}.")
        print(f"{C.RED}Error : {C.RESET}Response status code : {resp.status_code}")
        exit()
    return resp.json()    

def get_package_info_json(package_name: str, version: str) -> Dict:
    """Get package info json data from pypi server.
    
    Parameters
    ----------
    package_name : str
        Name of the package. Example: numpy
    version : str
        Version of the package. Example: 2.3.2
    
    Returns
    -------
    Dict
        Package json data.
    """
    if not version:
        url = f"https://pypi.org/pypi/{package_name}/json"
    else:
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"

    data = fetch_json(url)
    return data    

def get_qiq_dir(directory: str) -> str:
    """Returns full path of three qiq's directory.

    Parameters
    ----------
    directory: str
        The name of the directory.

    Returns: str
        Full path of given qiq directory.
    """

    if directory not in [C.QIQ_CONFIG_DIR,
                        C.QIQ_CACHE_DIR,
                        C.QIQ_PACKAGES_DIR]:
        trace_error()
        print(f"{C.RED}Error: {C.RESET}Inavalid qiq directory to fetch. {directory}")
        exit()

    # Get current python path
    python_path = get_python_path()

    # qiq directory
    return os.path.join(python_path, C.QIQ_DIR, directory)

def is_wheel_in_qiq_cache(name: str, version: str) -> str | None:
    """"Check if wheel is present in qiq-cache or not.

    # ℹ️ NOTE
        package name contains - antlr4-python3-runtime
        wheel name contains _ antlr4_python3_runtime-4.9.3-py3-none-any.whl

    Parameters
    ----------
    name: str
        Name of the package.
    version: str
        Version of the package.

    Returns
    ------- 
    str | None
        Wheel name if exists in qiq-cache or None.
    """
    qiq_cache_dir = get_qiq_dir(C.QIQ_CACHE_DIR) 
    all_wheels = glob.glob(os.path.join(qiq_cache_dir, "*.whl"))
    basenames = [os.path.basename(f) for f in all_wheels]
    name = name.replace("-", "_")  # See doc string
    for whl in basenames:
        if whl.startswith(name) and version in whl:
            return whl

    return None

def delete_empty_directories_in_qiq_packages() -> None:
    """Delete all empty directories in qiq-packages.

    When uninstalling a package version, it may possible
    that it's the only version available in the directory.
    For example: qiq-packages/nummy/1.2.3
    When 1.2.3 is getting uninstalled 'qiq-packages/numpy'
    is empty now. This method checks all the empty directories 
    in qiq-packages and removes them.
    """
    
    # Get current python path
    python_path = get_python_path()

    # Create package directory name
    qiq_packages_dir = get_qiq_dir(C.QIQ_PACKAGES_DIR)

    if os.path.exists(qiq_packages_dir):
        for name in os.listdir(qiq_packages_dir):
            full = os.path.join(qiq_packages_dir, name)
            if os.path.isdir(full):
                try:
                    os.rmdir(full)  # succeeds only if empty
                except OSError:
                    # directory wasn't empty
                    print(f"{C.RED}Error : {C.RESET}Directory is not empty: {C.YELLOW}{full}")
                    print(f"{C.RED}Error : {C.RESET}Not able to remove it.")

def can_package_uninstalled(specifier: str, proj_paths: List, print_info: bool = True) -> bool:
    """Check if package can be uninstalled.

    QiQ manages a projects.json file in qiq-config that stores the full
    path of QIQ_IMPORTER for every project.
    When user uninstall a package(explicit), we must sure that the neither the package 
    nor it's any of the dependent package is used by any project or else uninstalling the
    package will break other projects because qiq is single unified package manager.
    This function open each QIQ_IMPORTER path in QIQ_PROJECTS json, parse and count the appearence of
    package(specfier) and it's dependency packages, if either is used then we cannot remove the package. 
    
    Parameters
    ----------
    specifier: str
        Example: numpy==2.2.0
    proj_paths: List
        All project paths
    print_info: bool
        Print information
    Returns
    ------- 
    bool
        If specifier can be safely removed.
    """
    plat = platform.system().lower()
            
    all_packages = {}
    for project_dir in proj_paths:
        pkg_json = os.path.join(project_dir, '.qiq', plat + ".json")
        if not os.path.isfile(pkg_json):
            continue
        data = load_json(pkg_json)
        if not "packages" in data:
            print(f"{C.RED}Old format {C.YELLOW}{project_dir}, {C.RESET}please update it.")
            continue
        # Iterate over package in the file
        for pkg in data['packages']:
            pkg = pkg.strip()
            if not pkg in all_packages.keys():
                all_packages[pkg] = set()
            all_packages[pkg].add(project_dir)

    if specifier in all_packages.keys():
        print(f"\nCannot delete {print_specifier(specifier, False)}.\n")
        print(f"{print_specifier(specifier, False)} {C.RESET}is required in these projects:\n")
        for idx, p in enumerate(all_packages[specifier]):
            print(f"{C.YELLOW}{idx+1:<3}{C.RESET}{p}")
        return False
    else:
        return True
    
    return False

def _delete_package(package: str) -> None:
    """Delete package folder in qiq-packages.

    ℹ️ NOTE:
    When two installed packages share the same dependencies and you try
    to uninstall them both, at the time of deletion of second package
    the directories of it's dependencies won't exists because they were
    deleted with the first one.
    It's because of this reason we are not using else condition for the 
    if to print warning about diectory doesn't exists.
    
    Parameters
    ----------
    package : str
        Example: numpy==2.3.4
    """
    
    # Get package directory
    package_dir = get_package_path(package)
    
    # Make sure it exists
    if not os.path.isdir(package_dir):
        print(f"{C.RED} Missing package directory : {C.RESET}{package_dir}")
        return
    
    # Check if uninstall.txt exists. If yes then it has
    # all the list of files to delete along with package.
    # For example: console scripts
    uninstaller = os.path.join(package_dir, "uninstall.txt")
    if os.path.exists(uninstaller):
        with open(uninstaller, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f]
            for line in lines:
                if os.path.exists(line):
                    os.remove(line)

    # Delete package folder
    if os.path.exists(package_dir):
        print(f"{C.RED}Removing : {print_specifier(package, False)}...")
        shutil.rmtree(package_dir, onerror=handle_error)

def delete_packages(packages: List) -> None:
    """Delete packages from qiq-packages and update installed info.
    
    Parameters
    ----------
    packages : List
        ['numpy==2.2.6', librosa='0.11.0', ...]
    """

    answer = input("\nDo you want to permanently remove these packages? (y/n): ").lower()
    if answer not in ["y", "yes"]:
        return

    # Remove all the packages from disk in qiq-packages directory of current python.
    for pkg in packages:
        # Delete main package
        _delete_package(pkg)

    data = load_installed_packages()
    
    print(f"{C.YELLOW}Updating packages info...")
    # Update installed json by removing deleted packages
    new_data = []
    for main_pkg in data:
        # Ignore deleted packages
        if main_pkg in packages:
            continue
        else:
            new_data.append(main_pkg)

    # Write new data to disk    
    qpc = QiQ_Package_Cache()
    qpc.set_packages(new_data)

    # Now delete empty directories in qiq-packages
    delete_empty_directories_in_qiq_packages()
    
    print(f"{C.YELLOW}Done.")

def is_package_installed(name: str, version: str) -> bool:
    """Check if package is installed in qiq-packages.

    Parameters
    ----------
    name : str
        Name of the package. Example: numpy
    version : str
        Version of the package. Example: 2.3.4
    
    Returns
    -------
    bool
        True if package exists else false.
    """
    return os.path.exists(get_package_path(name + "==" + version))