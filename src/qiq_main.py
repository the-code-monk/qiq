"""This file communicates in between batch/bash qiq script and python.

Commands handled by qiq.bat on windows & qiq on Linux
-----------------------------------------------------
qiq -ipy --install-python <version>
qiq -upy --uninstall-python <version>
qiq -envs --environments
qiq -venv --virtual-environment <version>

Commands handles by this file.
ℹ️ NOTE
These commands are only available in virtual environment prompt.
----------------------------------------------------------------
qiq -l --list
qiq -t --tree
qiq -r --require -f/--force
qiq -i --install -f/--force
qiq -u --uninstall
qiq -c --clean
qiq -d --detail
qiq -p --projects
qiq -a --about
"""

__author__ = "Prashant Saxena"
__copyright__ = "Copyright 2026, The QiQ Project"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Prashant Saxena"
__status__ = "Development"

import sys
import os
from pathlib import Path
import argparse

from qiq_cmnd_list import QiQ_Cmnd_List
from qiq_cmnd_tree import QiQ_Cmnd_Tree
from qiq_cmnd_detail import QiQ_Cmnd_Detail
from qiq_cmnd_install import QiQ_Cmnd_Install
from qiq_cmnd_require import QiQ_Cmnd_Require
from qiq_cmnd_uninstall import QiQ_Cmnd_UnInstall
from qiq_cmnd_output import QiQ_Cmnd_Output
from qiq_cmnd_projects import QiQ_Cmnd_Projects
from qiq_cmnd_purge import QiQ_Cmnd_Purge
from qiq_cmnd_about import QiQ_Cmnd_About
from qiq_package_cache import QiQ_Package_Cache

class PrettyParser(argparse.ArgumentParser):
    def error(self, message):
        print(f"\n❌ Error: {message}\n")
        print("Use -h or --help for help.")
        #self.print_help()
        sys.exit(2)

    def print_help(self):
        help_file = os.path.join(Path(__file__).resolve().parent.parent, "help", "help-utf8.txt")
        with open(help_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.replace(r"\033", "\033")
                print(line, end="")

class QiQ_Main:

    def __init__(self):
        self.qiq_cmnd_about = QiQ_Cmnd_About()
        self.qiq_cmnd_list = QiQ_Cmnd_List()
        self.qiq_cmnd_tree = QiQ_Cmnd_Tree()
        self.qiq_cmnd_detail = QiQ_Cmnd_Detail()
        self.qiq_cmnd_install = QiQ_Cmnd_Install()
        self.qiq_cmnd_require = QiQ_Cmnd_Require()
        self.qiq_cmnd_uninstall = QiQ_Cmnd_UnInstall()
        self.qiq_cmnd_output = QiQ_Cmnd_Output()
        self.qiq_cmnd_projects = QiQ_Cmnd_Projects()
        self.qiq_cmnd_purge = QiQ_Cmnd_Purge()

    def get_args(self, arg):
        """Summary
        
        Parameters
        ----------
        arg : TYPE
            Description
        
        Returns
        -------
        TYPE
            Description
        """
        return [x for x in arg if x != "-f" and x != "--force"]

    def get_force(self, arg):
        """Summary
        
        Parameters
        ----------
        arg : TYPE
            Description
        
        Returns
        -------
        TYPE
            Description
        """
        return True if "-f" in arg or "--force" in arg else False

    def create_arg_parser(self) -> argparse.ArgumentParser:
        """Creats an argument parser.

        Returns:
            argparse.ArgumentParser Instance.
        """
        parser = PrettyParser(
            prog="qiq",
            description="🚀 Project Management CLI",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

        # =========================
        # Command Groups
        # =========================
        main_group = parser.add_argument_group("📦 Main Commands")

        main_group.add_argument("-l", "--list", nargs="*", default=None, metavar=".", help="List items")
        main_group.add_argument("-t", "--tree", nargs=argparse.REMAINDER, default=None, help="Show tree structure")

        main_group.add_argument("-r", "--require", nargs=argparse.REMAINDER, default=None, help="Require packages")
        main_group.add_argument("-i", "--install", nargs=argparse.REMAINDER, default=None, help="Install packages")
        main_group.add_argument("-u", "--uninstall", nargs=argparse.REMAINDER, default=None, help="Uninstall packages")
        main_group.add_argument("-o", "--output", nargs=argparse.REMAINDER, default=None, help="Ouput requirements.txt")

        main_group.add_argument("-c", "--clean", action="store_true", default=None, help="Clean project")
        main_group.add_argument("-d", "--detail", nargs="*", default=None, metavar=".", help="Show details")
        main_group.add_argument("-p", "--projects", action="store_true", default=None, help="List projects")

        # =========================
        # Info Commands
        # =========================
        info_group = parser.add_argument_group("ℹ️ Info")

        info_group.add_argument("-a", "--about", action="store_true", default=None, help="About this tool")
        #info_group.add_argument("-v", "--version", action="store_true", default=None, help="Show version")

        # =========================
        # Options
        # =========================
        opt_group = parser.add_argument_group("⚙️ Options")

        opt_group.add_argument("-f", "--force", action="store_true", help="Force operation")

        # =========================
        # No args → show help
        # =========================
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)

        return parser

    def create_install_parser(self) -> argparse.ArgumentParser:
        install_parser = argparse.ArgumentParser(add_help=False)

        install_parser.add_argument(
            "--ttl",
            type=float,
            default=argparse.SUPPRESS,
            help=f"Seconds before a cached version list is considered stale "
             f"(default: {QiQ_Package_Cache.DEFAULT_TTL:.0f}s = 24h).",
        )

        install_parser.add_argument("-refresh", "--refresh", 
            action="store_true",
            help="Ignore cached PyPI version lists and re-check them now, regardless of --ttl. "
                 "(requires_dist entries are immutable and are never affected by this.)",
        )

        return install_parser

    def load_arg_parser(self):
        """Summary"""
        parser = self.create_arg_parser()

        args = parser.parse_args()

        # =========================
        # Validate "one command only"
        # =========================
        commands = {
            "list": args.list is not None,       # True if flag used
            "tree": args.tree is not None,
            "require": args.require is not None,
            "install": args.install is not None,
            "uninstall": args.uninstall is not None,
            "output": args.output is not None,
            "clean": args.clean is not None,
            "detail": args.detail is not None,
            "projects": args.projects is not None,
            "about": args.about is not None,
            #"version": args.version is not None,
        }

        active_commands = [name for name, used in commands.items() if used]

        if len(active_commands) == 0:
            parser.error("You must specify a command.")

        if len(active_commands) > 1:
            parser.error(f"Please use only ONE command at a time: {', '.join(active_commands)}")

        # =========================
        # Validate force usage
        # =========================
        if args.force and not (args.install or args.require):
            parser.error("--force can only be used with --install or --require")

        command = active_commands[0]

        # =========================
        # Command handling
        # =========================
        if command == "list":
            self.qiq_cmnd_list.run(args.list)

        elif command == "tree":
            package = self.get_args(args.tree)

            if not package or len(package) >= 2:
                msg = "-t|--tree requires a single package specifier.\n"
                msg += "Example : qiq --tree numpy==2.2.3"
                parser.error(msg)

            self.qiq_cmnd_tree.run(package[0], QiQ_Package_Cache.DEFAULT_TTL)

        elif command == "require":
            
            require_parser = self.create_install_parser()

            require_parser.add_argument("filename")

            require_args = require_parser.parse_args(args.require)

            refresh = require_args.refresh
            ttl = require_args.ttl if hasattr(require_args, "ttl") else QiQ_Package_Cache.DEFAULT_TTL
            filename = require_args.filename

            self.qiq_cmnd_require.run(filename, ttl, refresh)

        elif command == "install":

            install_parser = self.create_install_parser()
            install_parser.add_argument("packages", nargs=argparse.REMAINDER)

            install_args = install_parser.parse_args(args.install)

            refresh = install_args.refresh
            ttl = install_args.ttl if hasattr(install_args, "ttl") else QiQ_Package_Cache.DEFAULT_TTL
            packages = install_args.packages

            # Get packages
            if not packages:
                msg = "-i|--install requires a package name.\n"
                msg += "Example : qiq --install numpy"
                parser.error(msg)
                
            # Get force
            self.qiq_cmnd_install.run(packages, ttl, refresh)

        elif command == "uninstall":
            # Get packages
            packages = self.get_args(args.uninstall)
            
            if not packages:
                msg = "-u|--uninstall requires a package specifier.\n"
                msg += "Example : qiq --uninstall numpy==2.3.4"
                parser.error(msg)
            self.qiq_cmnd_uninstall.run(packages)

        elif command == "output":
            # Extract filename (anything not -f/--force)
            filename_list = self.get_args(args.output)

            if not filename_list:
                parser.error("--output requires a filename")

            if len(filename_list) != 2:
                msg = "-o|--output requires an input and output file.\n"
                msg += "Example : qiq --output requirements.txt output.txt"
                parser.error(msg)

            self.qiq_cmnd_output.run(filename_list)

        elif command == "clean":
            self.qiq_cmnd_purge.run()

        elif command == "detail":
            self.qiq_cmnd_detail.run(args.detail)

        elif command == "projects":
            self.qiq_cmnd_projects.run()

        elif command == "about":
            self.qiq_cmnd_about.run()

if __name__ == "__main__":

    qiq = QiQ_Main()
    qiq.load_arg_parser()            
