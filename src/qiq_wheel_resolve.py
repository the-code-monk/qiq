"""This class handles the finding of a correct wheel file on pypi server
based on various factors such as OS, python, architecture etc.

Example:
--------
packages = {
    'contourpy': '1.3.3', 
    'cycler': '0.12.1',
    'fonttools': '4.62.1',
    'kiwisolver': '1.5.0',
    'numpy': '2.4.3',
    'packaging': '26.0',
    'pillow': '12.1.1',
    'pyparsing': '3.3.2',
    'python-dateutil': '2.9.0.post0',
    'six': '1.17.0'}
    qwr = QiQ_Wheel_Resolve()
    print(qwr.run(packages))
"""

__version__ = "0.0.1"

# python imports
from typing import Dict
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# pip imports
import requests
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging import tags, utils

# project imports
import qiq_config as C

MAX_THREADS = 10  # parallel requests

class QiQ_Wheel_Resolve:

    def __init__(self):
        self.session = requests.Session()

    def _select_best_wheel(self, files: Dict) -> str | None:
        """Select best wheel from list of urls.
        
        Parameters
        ----------
        files : Dict
            URLs from PyPI server of a package.
        
        Returns
        -------
        str | None
            URL of best wheel or None.
        """
 
        for file in files:
            if file["packagetype"] != "bdist_wheel":
                continue

            filename = file["filename"]
            
            try:
                _, _, _, wheel_tags = utils.parse_wheel_filename(filename)
                if not wheel_tags.isdisjoint(set(tags.sys_tags())):
                    return file["url"]
            except utils.InvalidWheelFilename:
                continue

        return None

    def _check_sdist(self, file: Dict) -> str | None:
        """Check sdist package is supported by python
        
        Parameters
        ----------
        file : Dict
        
        Returns
        -------
        str | None
            Either file['url'] or None
        """

        # Get python version requirement for this sdist.
        # Sometimes it's null or None in that case "==0.0.0"
        # will return supported as False.
        spec = SpecifierSet(file["requires_python"] or "==0.0.0")
        # Is it matches with running python
        supported = spec.contains(".".join(map(str, sys.version_info[:3])))
        
        if supported:
            return file["url"]
        else: # 🔥 What if it's not supported?
            sdist = os.path.basename(file["url"])
            print(f"{C.RED}Error : {C.RESET}{sdist}")
            print("This sdist is not supported by current python.")
            answer = input("\nDo you still want to download & install it? (yes/no): ").lower()
            if answer == "yes" or answer == "y":
                return file["url"]

        return None

    def _get_best_wheel(self, name: str, version: str) -> str | None:
        """Get best wheel url of a package with version.
        
        Parameters
        ----------
        name : str
            Name of the package.
        version : str
            Version of the package.
        
        Returns
        -------
        str | None
            URL of best wheel/tarball or None.
        """
        url = f"https://pypi.org/pypi/{name}/{version}/json"
        data = self.session.get(url, timeout=(3, 3)).json()

        best_wheel = self._select_best_wheel(data["urls"])
        if best_wheel:
            return best_wheel

        # fallback to sdist
        for file in data["urls"]:
            if file["packagetype"] == "sdist":
                return file["url"]

        return None

    def _fetch_wheels_parallel(self, packages: Dict) -> Dict:
        """Fetch wheels/tarballs in parallel.
        
        Parameters
        ----------
        packages : Dict
            {name: version, name: version}
        
        Returns
        -------
        Dict
            {(name, version) : url...}
        """
        results = {}

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            future_to_pkg = {
                executor.submit(self._get_best_wheel, name, version): (name, version)
                for name, version in packages.items()
            }

            for future in as_completed(future_to_pkg):
                name, version = future_to_pkg[future]
                try:
                    results[(name, version)] = future.result()
                except Exception:
                    results[(name, version)] = None

        return results

    def run(self, packages: Dict) -> Dict:
        """Fetch packages wheels/tarballs.
        
        Parameters
        ----------
        packages : Dict
            {name: version, name: version, ...}
        
        Returns
        -------
        Dict
            {(name, version) : url, ...}
        """
        return self._fetch_wheels_parallel(packages)

if __name__ == "__main__":
    # Example
    packages = {
    'contourpy': '1.3.3', 
    'cycler': '0.12.1',
    'fonttools': '4.62.1',
    'kiwisolver': '1.5.0',
    'numpy': '2.4.3',
    'packaging': '26.0',
    'pillow': '12.1.1',
    'pyparsing': '3.3.2',
    'python-dateutil': '2.9.0.post0',
    'six': '1.17.0'}
    qwr = QiQ_Wheel_Resolve()
    print(qwr.run(packages))
    print(qwr._get_best_wheel("cycler", "0.12.1"))
