"""This class parse the requirements.txt.

ℹ️ NOTE
It's a very simple parser that only parses packages, 
not as advance as pip's parsing.

Example:
-------
parser = QiQ_Req_Txt_Parser()
parser.parse("requirements.txt")
"""

__version__ = "0.0.3"

# Python Imports
from pathlib import Path
import os

# pip imports
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

# Project Imports
import qiq_config as C
import qiq_utils as utils

M1 = "{C.RED}Error : {C.YELLOW}{} {C.RESET} does not exists."
M2 = "{C.RED}Error : {C.RESET}Not allowed."
M3 = "{C.RED}Error : {C.RESET}Package {C.CYAN}{} {C.RESET}has been used twice in {}."
M4 = M2 + '\n' + M3

class RequirementsFileError(Exception):
    """The requirements file has invalid syntax or duplicate package entries."""

class QiQ_Req_Txt_Parser:

    def parse(self, path: Path) -> list[Requirement]:
        roots = []
        parsed_lines = []  # (lineno, raw_line, Requirement) for successfully-parsed lines
        errors = []

        for lineno, raw_line in enumerate(path.read_text().splitlines(), start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                req = Requirement(line)
            except InvalidRequirement as e:
                errors.append(f"  {path}:{lineno}: {raw_line.strip()!r} -- {e}")
                continue
            roots.append(req)
            parsed_lines.append((lineno, raw_line.strip(), req))

        # A package listed more than once as a root (e.g. numpy==2.3.3 on one
        # line, numpy==2.3.6 on another) would otherwise resolve silently --
        # resolvelib just intersects both constraints -- hiding what's likely a
        # copy-paste mistake in the file. Flag it explicitly instead.
        by_name = {}
        for lineno, raw_line, req in parsed_lines:
            by_name.setdefault(canonicalize_name(req.name), []).append((lineno, raw_line))
        for name, occurrences in by_name.items():
            if len(occurrences) > 1:
                where = ", ".join(f"line {ln} ({text!r})" for ln, text in occurrences)
                errors.append(f"  {path}: {name!r} is declared {len(occurrences)} times: {where}")

        if errors:
            raise RequirementsFileError(
                f"{len(errors)} problem(s) in {path}:\n" + "\n".join(errors)
            )
        return roots
