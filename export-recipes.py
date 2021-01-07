from pathlib import Path
import subprocess
from argparse import ArgumentParser

parser = ArgumentParser(description="Export the conan package references contained in this repository.")

parser.add_argument("--all",
                    action="store_true",
                    default=False,
                    help="Export all recipes in the repository, including recipes for old library versions." )

parser.add_argument("--no-user-channel-string",
                    action="store_true",
                    default=False,
                    help="Export packages WITHOUT a user/channel. Requires Conan >= 1.18" )

parser.add_argument("--user-channel-string",
                    action="store",
                    default="cd3/devel",
                    help="Specify the user/channel string to export packages too.",)


args = parser.parse_args()



export_cmd = ['conan','export']
for file in Path("recipes").glob("*/conanfile*.py"):
  cmd = export_cmd + [str(file)]
  if not args.no_user_channel_string:
    cmd = cmd + [args.user_channel_string]

  print(f"Exporting {str(file)} with command '{' '.join(cmd)}'.")
  subprocess.run(cmd)
