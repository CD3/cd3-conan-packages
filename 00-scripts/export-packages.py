import glob
import os
import subprocess
import multiprocessing

from argparse import ArgumentParser

parser = ArgumentParser(description="Export conan packages to the local cache.")
parser.add_argument("--provider_and_channel", "-c",
                    action="store",
                    default="local/testing",
                    help="The provide/channel string to use for the packages that are exported. Default: local/testing" )
parser.add_argument("packages",
                    default="all",
                    nargs="*",
                    help="The packages to export. Default: all" )
parser.add_argument("--parallel",    dest='parallel', action='store_true', help="Run jobs in parallel")
parser.add_argument("--no-parallel", dest='parallel', action='store_false', help="Do not run jobs in parallel")
parser.set_defaults(parallel=True)
args = parser.parse_args()


def run(cmd):
  return subprocess.call(cmd,shell=True)


# a context manager for temperarily change the working directory.
class working_directory(object):
  def __init__(self,path):
    self.old_dir = os.getcwd()
    self.new_dir = path
  def __enter__(self):
    if self.new_dir is not None:
      os.chdir(self.new_dir)
  def __exit__(self,type,value,traceback):
    if self.new_dir is not None:
      os.chdir(self.old_dir)

def export(dir):
  print("Exporing conan recipie in "+dir)
  with working_directory(dir):
    run('conan export . {0}'.format(args.provider_and_channel))
if args.packages == "all":
  package_dirs = [ os.path.dirname(file) for file in  glob.glob("*/conanfile.py") ]
else:
  package_dirs = args.packages

if __name__ == '__main__':
  jobs = []
  for dir in package_dirs:
    if args.parallel:
      p = multiprocessing.Process(target=export,args=(dir,))
      jobs.append(p)
      p.start()
    else:
      export(dir)







