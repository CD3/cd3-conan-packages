from pathlib import Path
import subprocess
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



export_cmd = ['conan','export']
for file in Path("recipes").glob("*/config.yml"):
    try:
        import yaml
    except: print(f"ERROR: could not import pyyaml which is required to parse {str(file)}.")

    data = yaml.safe_load( file.read_text() )
    root_dir = file.parent
    name = root_dir.stem
    if len(args.name) == 0 or (name in args.name):
        for version in data.get("versions",{}):
            folder = data["versions"][version].get('folder',None)
            if folder:
                cmd = export_cmd + [str(root_dir/folder), name+"/"+version+"@"+args.user_channel_string]
                print(f"Exporting {name} version {version} with command '{' '.join(cmd)}'.")
                subprocess.run(cmd)

for file in Path("recipes").glob("*/conanfile*.py"):
  name = file.parent.stem
  if len(args.name) == 0 or (name in args.name):
      cmd = export_cmd + [str(file)]
      cmd = cmd + [args.user_channel_string]

      print(f"Exporting {str(file)} with command '{' '.join(cmd)}'.")
      subprocess.run(cmd)

