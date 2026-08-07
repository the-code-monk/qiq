"""This class handles qiq -i|--install command.

It installs python pacakges from pypi server.

Example:
--------
qiq --install numpy onnx  # Install latest version of numpy & onnx
qiq --install numpy==2.3.4  # Install 2.3.4 version
"""

__version__ = "0.0.3"

# Python Imports
from typing import List, Dict
import os
import glob
import zipfile

# pip imports
from packaging.requirements import InvalidRequirement, Requirement

# Project Imports
from qiq_wheel_resolve import QiQ_Wheel_Resolve
from qiq_parallel_downloader import QiQ_Parallel_Downloader
from qiq_wheel_builder import QiQ_Wheel_Builder
from qiq_distinfo_parser import QiQ_Distinfo_Parser
from qiq_package_resolver import QiQ_Package_Resolver
import qiq_config as C
import qiq_utils as utils

M1 = "{C.YELLOW}Installing : {C.RESET}{}"
M2 = "{C.RED}Error: {} {C.RESET}Unable to find any suitable version."
M3 = "{C.RED}Ignoring : {} {C.RESET}already installed."
M4 = "{C.RED}Error   : {C.RESET} A higher version of {C.CYAN}{}, {}{C.RESET} is already installed."
M5 = "{C.YELLOW}Message : {C.RESET} Use -f or --force flag to install lower version."
M6 = "{C.YELLOW}Message : {C.RESET} Example : qiq -i -f {}"
M7 = "{C.RED}Ignoring : {}{C.RESET}, already installed."
M8 = "{C.YELLOW}Message : {C.RESET}Not able to find wheel or sdist for the following packages"
M9 = "{C.YELLOW}Message : {C.RESET}or user has denied to download sdist."

class QiQ_Cmnd_Install:

    def __init__(self):
        """Constructor"""
        self.qiq_wheel_resolve = QiQ_Wheel_Resolve()
        self.qiq_parallel_downloader = QiQ_Parallel_Downloader()
        self.qiq_wheel_builder = QiQ_Wheel_Builder()
        self.qiq_distinfo_parser = QiQ_Distinfo_Parser()

    def _extract_wheels(self, wheels: Dict)-> None:
        """Extract wheel files in qiq-packages.
        
        Parameters
        ----------
        wheels : Dict
            {(name, version): wheel file name in qiq-cache,...}
        """

        qiq_packages_dir = utils.get_qiq_dir(C.QIQ_PACKAGES_DIR)
        qiq_cache_dir = utils.get_qiq_dir(C.QIQ_CACHE_DIR)
        print()
        for (name, version), wheel in wheels.items():
            
            utils.display(M1, utils.short_name(wheel))
            
            wheel_file = os.path.join(qiq_cache_dir, wheel)
            package_dir = os.path.join(qiq_packages_dir, name, version) 
            
            # Create package directory in qiq-packages directory
            os.makedirs(package_dir, exist_ok=True)
            
            # Extract wheel into
            with zipfile.ZipFile(wheel_file, "r") as z:
                z.extractall(package_dir)
            
            # Run dist-info parser
            self.qiq_distinfo_parser.run(package_dir)
        
        print()

    def _install_package(self, packages: list):
        """Download and install a package with all it's dependencies.

        Parameters
        ----------
        packages: list
            Example: ['hello==1.1.1', 'world==2.2.2', ...]

        """

        to_be_installed = {}

        for pkg in packages:

            root_name, root_version = pkg.split("==")

            # Find if this package is already installed either explicitly
            # or implicitly with another package.
            if utils.is_package_installed(root_name, root_version):
                utils.display(M3, utils.print_specifier(pkg, False))
            else:
                to_be_installed[root_name] = root_version

        if not to_be_installed:
            return

        # Now find the correct wheels for all the deps and the package.
        wheels = self.qiq_wheel_resolve.run(to_be_installed)

        # Check if all the wheels are fetched.
        if None in wheels.values():
            utils.display(M8); utils.display(M9)
            for (name, version), whl in wheels.items():
                if not whl:
                    utils.print_specifier(name + "==" + version)
            return []

        # We might have some wheels/tarballs/zips avaiilable in qiq-cache because of 
        # previous installation. Intersect the two lists and find the correct ones to download.
        qiq_cache_dir = utils.get_qiq_dir(C.QIQ_CACHE_DIR) 

        # Get all .whl/.tar.xz/.zip in qiq-cache directory
        all_archives = glob.glob(os.path.join(qiq_cache_dir, "*.*"))
        basenames = [os.path.basename(f) for f in all_archives]
    
        # Check if .whl/.tar.gz/.zip is already available in qiq-cache.
        # If it's present then we are not going to download it again.        
        in_cache = 0
        all_downloads = []
        for (name, version), url in wheels.items():
            whl_name = os.path.basename(url)
            if whl_name not in basenames:
                all_downloads.append(url)
            else:
                in_cache = in_cache + 1

        print(f"{C.MAGENTA}{'Packages are about to be installed':<35}{C.CYAN}{len(to_be_installed): <5}")
        print(f"{C.MAGENTA}{'Packages are available in cache':<35}{C.CYAN}{in_cache: <5}")
        print(f"{C.MAGENTA}{'Packages are about to download':<35}{C.CYAN}{len(all_downloads): <5}")
        
        # Download them all in parallel
        if all_downloads:
            self.qiq_parallel_downloader.run(qiq_cache_dir, all_downloads)

        install_wheels = {}
        # Now we have all wheels/tars/zips available in qiq-cache. First we are going to check for
        # tar.gz & .zip that a previously built wheel is available or not. I don't know if there is any function 
        # available that creates a wheel name from tar.gz. Just using a hack. For example
        # wheel = "antlr4_python3_runtime-4.9.3-py3-none-any.whl"
        # name = "antlr4
        # version = "4.9.3"
        # if tar.startswith(name) & version in tar
        for (name, version), url in wheels.items():
            if url.endswith(".tar.gz") or url.endswith(".zip"):
                whl = utils.is_wheel_in_qiq_cache(name, version)
                if whl is not None: # Use existing wheel for extraction
                    install_wheels[(name, version)] = whl
                else:  # Build the wheel from tar.gz|zip
                    whl = self.qiq_wheel_builder.run(
                        os.path.join(qiq_cache_dir, os.path.basename(url)), qiq_cache_dir)
                    install_wheels[(name, version)] = whl
            else: # Use newly fetch wheel for extraction
                install_wheels[(name, version)] = os.path.basename(url)

        # Extract wheels to qiq-packages
        self._extract_wheels(install_wheels)

        # Create a flat list of package specifiers to store
        store_pkgs = []
        for pkg_name, pkg_version in to_be_installed.items():
            store_pkgs.append(pkg_name + "==" + pkg_version)
        
        # Update installed info json by addding this package information
        utils.update_installed_packages(store_pkgs)

    def run(self, 
        packages: list,
        ttl: float=0.0,
        refresh: bool=False
        ) -> List[str]:
        """Install a single or list of packages.

        Parameters
        ----------
        packages: List[Requirement] or List[str]
            Example: ['numpy==2.3.2', 'pytorch>=2.3.4' ...]
            Example: [Requirement('numpy==2.3.2'), Requirement('pytorch>=2.3.4') ...]
        ttl: float
            Seconds before a cached version list is considered stale
            default: 86400 or 24h
        force_refresh: bool
            Ignore cached PyPI version lists and re-check them now, regardless of --ttl.
            requires_dist entries are immutable and are never affected by this.
        """

        if not packages:
            return []

        # If packages is a list of str,
        # Convert them to Requirement object
        # CLI has a command:
        # qiq -i numpy==2.2.2 soundfile
        # The packages list comes from it
        if isinstance(packages[0], str):
            new_packages = []
            for pkg in packages:
                try:
                    req = Requirement(pkg)
                except InvalidRequirement as e:
                    utils.display_error("{C.RED}Error : {C.RESET}{}", e)
                new_packages.append(req)
            packages = new_packages

        all_pkgs_n_deps = []

        print(f"{C.GREEN}Info : {C.YELLOW}Fetching package/s and dependencies...")
        print()
        
        # Resolve package tree
        # {pkg:[deps], pkg:[deps], ...}
        resolve_packages = QiQ_Package_Resolver(ttl, refresh).get(packages)

        # Create a flat list of packages
        for pkg, deps in resolve_packages.items():
            all_pkgs_n_deps.append(pkg)
            all_pkgs_n_deps.extend(deps)
  
        # Make sure no duplicates and sort them
        all_pkgs_n_deps = sorted(list(set(all_pkgs_n_deps)))

        self._install_package(all_pkgs_n_deps)

        return all_pkgs_n_deps
