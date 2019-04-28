import os
import sys
import subprocess

from argparse import ArgumentParser

parser = ArgumentParser(description="Exports all conan packages to the local cache.")
parser.add_argument("--provider_and_channel", "-c",
                    action="store",
                    default="cd3/devel",
                    help="The provide/channel string to use for the packages that are exported. Default: cd3/devel" )
parser.add_argument("--parallel",    dest='parallel', action='store_true', help="Run jobs in parallel")
parser.add_argument("--no-parallel", dest='parallel', action='store_false', help="Do not run jobs in parallel")
parser.set_defaults(parallel=True)
args = parser.parse_args()


def run(cmd):
  return subprocess.call(cmd,shell=True)


if __name__ == '__main__':
  export_script = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), "00-scripts", "export-packages.py" )
  cmd = " ".join([ sys.executable, export_script, "--provider_and_channel", args.provider_and_channel ])
  subprocess.call(cmd,shell=True)







