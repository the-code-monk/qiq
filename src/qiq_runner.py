"""
You must call "**import qiq**" at the start of the main file
or prior to importing any installed packages in order to use
QiQ in a program.

It's a very minor restriction, but it won't prevent you from
publishing or shipping your project without QiQ.

When working locally, you can setup your Python IDE with a
straightforward approach.

For instance, you can create a custom Python build environment using this
[qiq_runner.py] file when using Sublime Text.

```json
{
    "cmd": ["C:\\qiq\\python\\python-win\\python-3.10.0\\python.exe", "-u", "c:\\qiq\\src\\qiq_runner.py", "$file"],
    "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
    "selector": "source.python",
    "encoding": "utf8",
    "env": {"PYTHONIOENCODING": "utf8"},
}
```

This will import qiq automatically before executing your main $file.
Likewise, you can configure other IDE's such as VS Code etc.
"""

__version__ = "0.0.1"

import qiq
import os
import runpy
import sys

# Add the directory of script_path to sys
script_path = sys.argv[1]
sys.path.insert(0, os.path.dirname(script_path))

runpy.run_path(sys.argv[1], run_name="__main__")