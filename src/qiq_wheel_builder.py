"""This class handles building of a wheel from tar.gz.

Example:
-------
qwb = QiQ_Wheel_Builder()
r = qwb.run(r"C:\antlr4-python3-runtime-4.9.3.tar.gz", r"d:\\temp")
print(r) # Returns wheel file name.

"""

__version__ = "0.0.1"

# python imports
import os
import sys
import tempfile
import tarfile
import subprocess
import glob
import shutil
import zipfile

# project imports
import qiq_config as C
import qiq_utils as utils


M1 = "{C.RED}Error: {C.RESET}Unable to build wheel. {C.YELLOW}{}"

class QiQ_Wheel_Builder:

    def _extract_zip(self, archive: str, extract_to: str):
        """Extract zip without top level folder.
        
        Parameters
        ----------
        archive : str
            The path of zip file.
        extract_to : str
            The directory in which zip should be extracted.
        """
        with zipfile.ZipFile(archive, 'r') as z:
            root = z.namelist()[0].split('/')[0]
            for member in z.namelist():
                if member.startswith(root + "/"):
                    relative_path = member[len(root) + 1:]  # strip root

                    if not relative_path:
                        continue

                    target_path = os.path.join(extract_to, relative_path)

                    if member.endswith("/"):
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with z.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())

    def _extract_tar(self, archive: str, extract_to: str):
        """Extract tarball without top level folder.
        
        Parameters
        ----------
        archive : str
            The path of tarball.
        extract_to : str
            The directory in which tarball should be extracted.
        """
        with tarfile.open(archive, "r:gz") as tar:
            top_level_folder = os.path.commonprefix(tar.getnames()).rstrip("/")
            members_to_extract = []
            
            # We look for files that start with "package-10.2.5/"
            prefix = top_level_folder.strip('/') + '/'
            
            for member in tar.getmembers():
                if member.name.startswith(prefix):
                    # Strip the prefix from the filename to extract 'cleanly'
                    member.name = os.path.relpath(member.name, prefix)
                    
                    # Skip the actual directory entry itself if it becomes '.'
                    if member.name != '.':
                        members_to_extract.append(member)

            # CHECK FOR FILTER SUPPORT (Python 3.12+)
            # We check if 'data' filter is available to avoid TypeErrors in 3.10
            if hasattr(tarfile, 'data_filter'):
                tar.extractall(path=extract_to, members=members_to_extract, filter='data')
            else:
                # Fallback for Python 3.10 and older
                tar.extractall(path=extract_to, members=members_to_extract)

    def run(self, archive: str, output_wheel_dir: str):
        """Summary
        
        Parameters
        ----------
        archive : str
            Path of tar.gz archive.
        output_wheel_dir : str
            Path to copy wheel file.
        
        Raises
        ------
        Exception
            If building wheel fails.
        """
        print(f"{C.YELLOW}Building wheel: {C.RESET}{archive}")
        os.makedirs(output_wheel_dir, exist_ok=True)
        qiq_cache_dir = utils.get_qiq_dir(C.QIQ_CACHE_DIR) 
        
        if not os.path.isfile(archive):
            utils.display_error(f"{C.RED}Error: {C.YELLOW}{archive} {C.RESET}does not exists.")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # print(f"Created temporary directory: {os.path.abspath(temp_dir)}")

            # Get python executable
            python_exe = os.path.basename(sys.executable)

            # Extract tarball
            if archive.endswith("tar.gz"):
                self._extract_tar(archive, temp_dir)
            else:
                self._extract_zip(archive, temp_dir)
                        
            # Default command to build wheel
            cmnd = [python_exe, "-m", "build", "--wheel"]
            
            # If pyproject.toml doesn't exists then build command.
            if not os.path.isfile(os.path.join(temp_dir, "pyproject.toml")):
                cmnd = [python_exe, "setup.py", "bdist_wheel"]
            
            # Run
            try:
                result = subprocess.run(
                    cmnd,   # your command
                    cwd=temp_dir,
                )
            except Exception as e:
                utils.trace_error()
                print(f"{C.RED}Command : {C.RESET}{' '.join(cmnd)}")
                print(f"{C.RED}Error   : {C.RESET}{str(e)}")
                exit()
            
            # The directory in which wheel would be produced
            dist_dir = os.path.join(temp_dir, "dist")
            
            # It should exists in case of successful build
            if os.path.exists(dist_dir):
                # Get all .whl files in 'dist' folder.
                # There should be one
                whl_files = glob.glob(os.path.join(dist_dir, "*.whl"))
                if whl_files:
                    shutil.copy(whl_files[0], output_wheel_dir)  # copy to qiq-cache
                    return os.path.basename(whl_files[0])
                else:
                    utils.display_error(M1, archive)
            else:
                utils.display_error(M1, archive)
        return None

if __name__ == "__main__":
    qwb = QiQ_Wheel_Builder()
    r = qwb.run(r"antlr4-python3-runtime-4.9.3.tar.gz", r"d:\\temp")
    print(r)
    