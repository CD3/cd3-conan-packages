from pathlib import Path
import subprocess
import os
import sys
import pathlib
from argparse import ArgumentParser

parser = ArgumentParser(description="Export the conan package references contained in this repository.")

parser.add_argument("name",
                    action="store",
                    nargs='*',
                    help="Export packages with name 'name'.",)
parser.add_argument("--user-channel-string",
                    action="store",
                    default="cd3/devel",
                    help="Specify the user/channel string to export packages too.",)


args = parser.parse_args()

os.chdir( pathlib.Path(__file__).parent )


export_cmd = ['conan','export']

# this loop will export recipes that follow the conancenter convention
# on layout.
for file in Path("recipes").glob("*/config.yml"):
    if 'yaml' not in sys.modules:
        try:
            print("Importing `yaml` module to parse yaml config files.")
            import yaml
        except:
            print(f"ERROR: could not import pyyaml which is required to parse {str(file)}.")
            print(f"Please run `pip install pyyaml`")
            sys.exit(1)

    data = yaml.safe_load( file.read_text() )
    root_dir = file.parent
    name = root_dir.stem
    if len(args.name) == 0 or (name in args.name):
        for version in data.get("versions",{}):
            folder = data["versions"][version].get('folder',None)
            if folder:
                cmd = export_cmd + [str(root_dir/folder), name+"/"+version+"@"+args.user_channel_string]
                print(f"Exporting {name} version {version} with command '{' '.join(cmd)}'.")
                result = subprocess.run(cmd)


# this loop will export recpipes that follow our own custom convention
# on layout. We need to make sure the rhd_custom_generators recipes get exported first
# since the packages that use them will need then when they get exported
conanfiles = sorted(Path("recipes").glob("*/conanfile*.py"), key = lambda x : "rhd_custom_generators" in str(x), reverse=True)
for file in  conanfiles:
  name = file.parent.stem
  if len(args.name) == 0 or (name in args.name):
      cmd = export_cmd + [str(file)]
      cmd = cmd + [args.user_channel_string]

      print(f"Exporting {str(file)} with command '{' '.join(cmd)}'.")
      subprocess.run(cmd)

