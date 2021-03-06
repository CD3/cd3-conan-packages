from pyparsing import *
import tempfile
import shutil
import subprocess
import util

from argparse import ArgumentParser

parser = ArgumentParser(description="Determine version number for the latest release.")

parser.add_argument("url",
                    action="store",
                    nargs='?',
                    default=".",
                    help="git repository to analyze" )

parser.add_argument("--branch",
                    action="store",
                    default="master",
                    help="Name of branch to look on." )

parser.add_argument("--major-series",
                    action="store",
                    default=None,
                    help="Return latest tagged release in given major series." )

args = parser.parse_args()



version_tag = util.get_latest_release(args.url,args.branch,args.major_series)
if version_tag is None:
  print("Could not find a version tag in repository.")
else:
  print(version_tag)




