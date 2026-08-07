from distlib.scripts import ScriptMaker
import sysconfig

script_body = r'''
import qiq
import runpy
import sys
import code as _code

def main():
    argv = sys.argv[1:]

    if not argv:
        console = _code.InteractiveConsole({"qiq": qiq})
        console.interact(banner="qiqpy (qiq pre-imported)", exitmsg="")
        return

    if argv[0] == "-m":
        module = argv[1]
        sys.argv = [module] + argv[2:]
        # Add cwd to sys.path so local packages are findable, mirroring real python behaviour
        if sys.path[0] != '':
            sys.path.insert(0, '')
        runpy._run_module_as_main(module)

    elif argv[0] == "-c":
        code_str = argv[1]
        sys.argv = ["-c"] + argv[2:]
        exec(code_str, {"__name__": "__main__", "qiq": qiq})

    elif argv[0].startswith("-"):
        print(f"qiqpy: unknown option: {argv[0]}", file=sys.stderr)
        sys.exit(2)

    else:
        script_path = argv[0]
        sys.argv = argv
        # Insert the script's directory, mirroring real python behaviour
        import os
        script_dir = os.path.dirname(os.path.abspath(script_path))
        if sys.path[0] != script_dir:
            sys.path.insert(0, script_dir)
        runpy.run_path(script_path, run_name="__main__")

if __name__ == "__main__":
    main()
'''

scripts_dir = sysconfig.get_path("scripts")
maker = ScriptMaker(None, scripts_dir)
maker.variants = {''}  # Avoid generating qiqpy-3.11.exe etc.

# This is the key: distlib will prepend the correct shebang and
# wrap the script in a real Windows PE launcher (.exe stub)
maker._write_script(
    ['qiqpy'],
    maker._get_shebang('utf-8'),
    script_body.encode('utf-8'),
    [],          # no flags
    'py'
)

print(f"Installed qiqpy executable to {scripts_dir}")