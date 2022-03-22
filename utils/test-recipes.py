from pathlib import Path
import subprocess
import itertools
import os
from argparse import ArgumentParser

parser = ArgumentParser(description="Test some or all of the conan package references contained in this repository.")

parser.add_argument("name",
                    action="store",
                    nargs='*',
                    help="Test packages with name 'name'.",)
parser.add_argument("--user-channel-string",
                    action="store",
                    default="cd3/devel",
                    help="Specify the user/channel string to export packages too.",)


args = parser.parse_args()

results = []

profiles = subprocess.check_output(['conan', 'profile', 'list'])
if profiles.startswith(b"No profiles defined"):
    print("Creating default profile")
    subprocess.run(['conan','profile','new','default','--detect'])
    subprocess.run(['conan','profile','update','settings.compiler.libcxx=libstdc++11','default'])

for file in Path("recipes").glob("*/config.yml"):
    try:
        import yaml
    except: print(f"ERROR: could not import pyyaml which is required to parse {str(file)}.")

    data = yaml.safe_load( file.read_text() )
    root_dir = file.parent
    name = root_dir.stem
    if len(args.name) > 0 and (name not in args.name):
        continue
    for version in data.get("versions",{}):
        name = root_dir.stem
        folder = str(data["versions"][version].get('folder',None))
        if folder:
            folder = root_dir/folder

            cmd = ['conan', 'export', str(folder), f"{name}/{version}@{args.user_channel_string}"]
            print(f"Exporting {name} version {version} with command '{' '.join(cmd)}'.")
            result = subprocess.run(cmd)
            if result.returncode:
                name = name.lower()
                cmd = ['conan', 'export', str(folder), f"{name}/{version}@{args.user_channel_string}"]
                print(f"Export failed. Trying again with command '{' '.join(cmd)}'.")
                result = subprocess.run(cmd)


            test_dirs = filter(lambda x: x.is_dir(),  (folder/"_test_package").glob("*"))
            if (folder/"test_package").exists():
                test_dirs = itertools.chain(test_dirs, [folder/"test_package"])

            for test_dir in test_dirs:
                cmd = ['conan','test',str(test_dir),f"{name}/{version}@{args.user_channel_string}",'--build','missing']
                print(cmd)
                r = subprocess.run(cmd)
                if r.returncode:
                    results.append(f"FAIL: {' '.join(cmd)}")
                else:
                    results.append(f"PASS: {' '.join(cmd)}")




for r in results:
    print(r)
