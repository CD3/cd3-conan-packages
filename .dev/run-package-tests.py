from pathlib import Path
import subprocess
import os
import sys
import re
from argparse import ArgumentParser
from multiprocessing import Pool
import concurrent.futures

parser = ArgumentParser(description="Run conan package tests for the recipes that have one.")

parser.add_argument("name",
                    action="store",
                    nargs='*',
                    help="Export packages with name 'name'.",)
parser.add_argument("--user-channel-string",
                    action="store",
                    default="cd3/devel",
                    help="Specify the user/channel string to export packages too.",)
parser.add_argument("--jobs",
                    action="store",
                    default=None,
                    help="Run tests in parallel.",)


args = parser.parse_args()

class colors:
    PASS = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


top_dir = Path(subprocess.check_output(['git','rev-parse','--show-toplevel']).strip().decode('utf-8'))
os.chdir(top_dir)
log_dir = top_dir/"test-output"
log_dir.mkdir(exist_ok=True)

def run_test(spec):
    package_reference = spec['package_reference']
    test_folder = spec['test_folder']
    log_dir = spec['log_dir']

    log_file = package_reference
    for char in [".","/","@"]:
        log_file = log_file.replace(char,"_")

    build_dir = log_dir/(log_file+".build.d")

    cmd = ['conan', 'test', str(test_folder), package_reference, '-tbf', build_dir, '--build', 'missing']
    with open(log_dir/log_file,'w') as f:
        f.write(f"Running test for {package_reference} using {test_folder}\n")
        f.flush()
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT)

    return {'package_reference':spec['package_reference'], 'result':result}


tests = []
# this loop will export recipes that follow the conancenter convention
# on layout.
for file in Path("recipes").glob("*/config.yml"):
    try:
        import yaml
    except: print(f"ERROR: could not import pyyaml which is required to parse {str(file)}.")

    data = yaml.safe_load( file.read_text() )
    root_dir = file.parent
    name = root_dir.stem
    if len(args.name) == 0 or (name in args.name):
        for version in data.get("versions",{}):
            recipe_folder = root_dir/data["versions"][version].get('folder',None)
            if recipe_folder:
                test_folder = (recipe_folder/"test_package").absolute()
                package_reference = name+"/"+version+"@"+args.user_channel_string
                if test_folder.exists():
                    tests.append({'package_reference':package_reference,'test_folder':test_folder,'log_dir':log_dir})









# this loop will export recpipes that follow our own custom convention
# on layout.
conanfiles = Path("recipes").glob("*/conanfile*.py")
for file in  conanfiles:
  name = file.parent.stem
  if len(args.name) == 0 or (name in args.name):
      test_folder = (file.parent/"test_package").absolute()
      if test_folder.exists():
          text = file.read_text()
          match = re.search('''^\s*version\s*=\s*"([^"]*)"$''',text,flags=re.MULTILINE)
          if match:
              version = match.group(1)
          else:
              print(f"Could not determine version number for {file}. skipping")
              continue

          package_reference = name+"/"+version+"@"+args.user_channel_string
          tests.append({'package_reference':package_reference,'test_folder':test_folder,'log_dir':log_dir})


sys.stdout.write("Running tests...\n")
with Pool(args.jobs) as p:
    for result in p.imap_unordered( run_test, tests ):
        sys.stdout.write(result['package_reference']+": ")
        if result['result'].returncode == 0:
            sys.stdout.write(colors.PASS+"Pass\n"+colors.ENDC)
        else:
            sys.stdout.write(colors.FAIL+"Fail\n"+colors.ENDC)

sys.stdout.write("Done\n")
