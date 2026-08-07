"""This class parallelly download given URLs in a folder.

Example:
-------
downloader = QiQ_Parallel_Downloader()
downloader.run("c:/temp", [url1, url2, url3,...])
"""

__version__ = "0.0.2"

# python imports
from typing import List
import os
import time
import threading
from urllib.parse import urlparse
from urllib3.util.retry import Retry
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# pip imports
import rich
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
)
import requests

# Project Imports
import qiq_config as C
import qiq_utils as utils

MAX_WORKERS = 10
RETRIES = 2
CHUNK_SIZE = 8192

stop_event = threading.Event()

retry_strategy = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
)

# Shared session with connection pooling
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
        pool_connections=20,
        pool_maxsize=20,
        max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

class QiQ_Parallel_Downloader:

    def __init__(self):
        # Folder to download all URLs
        self.download_folder = None
        # Package and it's dependencies size in MB
        self.total_size = 0
        # Total download size in MB
        self.all_size = 0

    def _download(self, progress: rich.progress.Progress, task_id: int, url: str) -> int:
        """Download a file and update rich progress
        
        Parameters
        ----------
        progress : rich.progress.Progress
            rich.progress.Progress instance.
        task_id : int
            The integer task id of progress
        url : str
            URL of the file to dowload
        
        Returns
        -------
        int
            Task Id
        """
        self.total_size = 0
        filename = os.path.basename(urlparse(url).path)
        path = os.path.join(self.download_folder, filename)
        
        for attempt in range(RETRIES):
            try:
                with session.get(url, stream=True, timeout=(5, 15)) as r:
                    r.raise_for_status()

                    total = int(r.headers.get("content-length", 0))
                    self.total_size += total
                    self.all_size += total
                    progress.update(task_id, total=total)

                    with open(path, "wb") as f:
                        for chunk in r.iter_content(CHUNK_SIZE):
                            if stop_event.is_set():
                                progress.console.print(f"[red]Interrupted:[/] {progress.tasks[task_id].description}")
                                return
                            if chunk:
                                f.write(chunk)
                                progress.update(task_id, advance=CHUNK_SIZE)
                    return task_id

            except requests.exceptions.RequestException as e:
                print(f"{C.RED}Failed to download : {C.CYAN}{filename}. {C.RESET}Retrying {C.YELLOW}{attempt + 1}/{RETRIES}")
                if attempt == RETRIES - 1:
                    raise e
                time.sleep(2 ** attempt)  # ✅ exponential backoff
    
    def run(self, folder: str, urls: List[str]) -> None:
        """Download files in parallel
        
        Parameters
        ----------
        folder : str
            Folder to download files.
        urls : List[str]
            All urls
        """
        self.download_folder = folder

        progress = Progress(
            SpinnerColumn(),  # 🔄 spinner added,
            TextColumn("[cyan]{task.description}[/]"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            refresh_per_second=20
        )

        with progress:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(
                        self._download,
                        progress,
                        progress.add_task(utils.short_name(url), total=0),
                        url
                    ): url
                    for url in urls
                }

                try:
                    print()
                    overall_task = progress.add_task("[yellow]All Files[/]", total=len(urls))  # ✅ overall bar
                    for future in as_completed(futures):
                        name = futures[future]
                        future.result()
                        progress.update(overall_task, advance=1)
                        progress.console.print(f"[green]Downloaded:[/] {utils.short_name(name)}")
                    progress.console.print(f"\nPackage : [yellow]{self.total_size / (1024*1024):.2f} MB[/]\n")

                except Exception as e:
                    print(f"\n{e}\n") 
                    exit()
                except KeyboardInterrupt:
                    stop_event.set()
                    progress.console.print("[bold red]All downloads interrupted![/]")
                    
                    # ✅ wait for all threads to finish
                    for future in futures:
                        try:
                            future.result()  # wait for thread to exit
                        except:
                            pass
                    
                    # We must delete all the files in case of interruption.
                    # They are not fully downloaded and corrupted.
                    # ✅ now safe to delete files
                    for url in urls:
                        filename = os.path.basename(urlparse(url).path)
                        path = os.path.join(self.download_folder, filename)
                        if os.path.exists(path):
                            Path(path).unlink(missing_ok=True)
        print(f"\nTotal download : {C.YELLOW}{self.all_size / (1024*1024):.2f} MB")
        session.close()

if __name__ == "__main__":
    # Example
    urls = [
    'https://files.pythonhosted.org/packages/e7/05/c19819d5e3d95294a6f5947fb9b9629efb316b96de511b418c53d245aae6/cycler-0.12.1-py3-none-any.whl',
    'https://files.pythonhosted.org/packages/10/bd/c038d7cc38edc1aa5bf91ab8068b63d4308c66c4c8bb3cbba7dfbc049f9c/pyparsing-3.3.2-py3-none-any.whl',
    'https://files.pythonhosted.org/packages/ec/57/56b9bcc3c9c6a792fcbaf139543cee77261f3651ca9da0c93f5c1221264b/python_dateutil-2.9.0.post0-py2.py3-none-any.whl',
    'https://files.pythonhosted.org/packages/b1/3c/88af0040119209b9b5cb59485fa48b76f372c73068dbf9254784b975ac53/numpy-2.4.3-cp313-cp313-win_amd64.whl',
    'https://files.pythonhosted.org/packages/18/0b/0098c214843213759692cc638fce7de5c289200a830e5035d1791d7a2338/contourpy-1.3.3-cp313-cp313-win_amd64.whl',
    'https://files.pythonhosted.org/packages/38/60/35186529de1db3c01f5ad625bde07c1f576305eab6d86bbda4c58445f721/fonttools-4.62.1-cp313-cp313-win_amd64.whl',
    'https://files.pythonhosted.org/packages/b7/ce/149a00dd41f10bc29e5921b496af8b574d8413afcd5e30dfa0ed46c2cc5e/six-1.17.0-py2.py3-none-any.whl',
    'https://files.pythonhosted.org/packages/3f/eb/b0834ad8b583d7d9d42b80becff092082a1c3c156bb582590fcc973f1c7c/pillow-12.1.1-cp313-cp313-win_amd64.whl',
    'https://files.pythonhosted.org/packages/b7/b9/c538f279a4e237a006a2c98387d081e9eb060d203d8ed34467cc0f0b9b53/packaging-26.0-py3-none-any.whl',
    'https://files.pythonhosted.org/packages/be/8a/be60e3bbcf513cc5a50f4a3e88e1dcecebb79c1ad607a7222877becaa101/kiwisolver-1.5.0-cp313-cp313-win_amd64.whl']
    qpr = QiQ_Parallel_Downloader()
    qpr.run("d:/temp/downloads", urls)