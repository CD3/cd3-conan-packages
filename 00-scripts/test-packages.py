import glob
import os
import subprocess
import multiprocessing
import shutil
import sys


from argparse import ArgumentParser

parser = ArgumentParser(description="Test all conan packages in the local cache.")
parser.add_argument("--provider_and_channel", "-c",
                    action="store",
                    default="local/testing",
                    help="The provide/channel string of the packages to be tested. Default: local/testing" )
parser.add_argument("packages",
                    action="store",
                    nargs='*',
                    default="all",
                    help="The packages to test. Default: all" )
parser.add_argument("--parallel",    dest='parallel', action='store_true', help="Run jobs in parallel")
parser.add_argument("--no-parallel", dest='parallel', action='store_false', help="Do not run jobs in parallel")
parser.set_defaults(parallel=True)
args = parser.parse_args()


def run(cmd,stdout=None,stderr=None):
  return subprocess.call(cmd,shell=True,stdout=stdout,stderr=stderr)


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

def test(dir):
  print("Testing conan package in "+dir)
  with working_directory(dir):
    tmpdir = "_test-client-build"
    outfile = "conan-ouput.txt"
    if os.path.exists(tmpdir):
      shutil.rmtree(tmpdir)
    os.mkdir( tmpdir )
    with working_directory(tmpdir):
      with open(outfile,'w') as f:
        cmd = "conan install ../test_package --build missing"
        ec = run(cmd,f,f)
        if ec != 0:
          print("There was a problem installing dependencies for {}".format(dir))
          print("The output of '{cmd}' was written to {file}".format( cmd=cmd,file=os.path.join(dir,tmpdir,outfile) ) )
          return

        cmd = "conan build ../test_package"
        ec = run(cmd,f,f)
        if ec != 0:
          print("There was a problem building {}".format(dir))
          print("The output of '{cmd}' was written to {file}".format( cmd=cmd,file=os.path.join(dir,tmpdir,outfile) ) )
          return


    shutil.rmtree(tmpdir)
    print(dir+" PASSED")


package_dirs = [ os.path.dirname(file) for file in  glob.glob("*/conanfile.py") ]
if __name__ == '__main__':
  export_script = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), "export-packages.py" )
  cmd = " ".join([ sys.executable, export_script, "--provider_and_channel", args.provider_and_channel ])
  print("Exporting all packages to {} channel".format(args.provider_and_channel))
  run( cmd )
  jobs = []
  for dir in package_dirs:
    if args.parallel:
      p = multiprocessing.Process(target=test,args=(dir,))
      jobs.append(p)
      p.start()
    else:
      test(dir)







