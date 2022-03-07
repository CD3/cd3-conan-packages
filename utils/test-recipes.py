from pathlib import Path
import subprocess
import itertools
from argparse import ArgumentParser

parser = ArgumentParser(description="Test some or all of the conan package references contained in this repository.")

parser.add_argument("--user-channel-string",
                    action="store",
                    default="cd3/devel",
                    help="Specify the user/channel string to export packages too.",)


args = parser.parse_args()

results = []

for file in Path("recipes").glob("*/config.yml"):
    try:
        import yaml
    except: print(f"ERROR: could not import pyyaml which is required to parse {str(file)}.")

    data = yaml.safe_load( file.read_text() )
    root_dir = file.parent
    name = root_dir.stem
    for version in data.get("versions",{}):
        folder = data["versions"][version].get('folder',None)
        if folder:
            folder = root_dir/folder
            if (folder/"test_package").exists():
                cmd = ['conan','test',str(folder/"test_package"),f"{name}/{version}@{args.user_channel_string}",'--build','missing']
                r = subprocess.run(cmd)
                if r.returncode:
                    results.append(f"FAIL: {' '.join(cmd)}")
                else:
                    results.append(f"PASS: {' '.join(cmd)}")

for test_dir in Path("recipes").glob("*/test_package"):
    name = test_dir.parent
    while name.parent.stem != "recipes":
        name = name.parent
    name = name.stem


for r in results:
    print(r)
