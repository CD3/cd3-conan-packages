import subprocess
import shutil
import os
import collections
import copy
import yaml
import json
import re
import sys
import pprint
import tempfile
from pathlib import Path

from types import SimpleNamespace

from pyparsing import *
from conans.client.generators.virtualenv import VirtualEnvGenerator

try:
    from colorama import Fore, Back, Style

    INFO = Fore.WHITE
    EMPH = Fore.GREEN
    GOOD = Fore.GREEN
    WARN = Fore.YELLOW
    ERROR = Fore.RED
    EOL = Style.RESET_ALL
except:
    INFO = ""
    EMPH = ""
    GOOD = ""
    WARN = ""
    ERROR = ""
    EOL = ""


def run(cmd, stdout=None, stderr=None):
    return subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)

class parsers:
  version_str = Combine(Word(nums) + Optional( "." + Word(nums) + Optional( "." + Word(nums) + Optional( "." + Word(nums) ) ) ) )
  version_tag = Optional(Literal("v") ^ "ver-" ) + version_str

# a context manager for temperarily change the working directory.
class working_directory(object):
    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        if self.new_dir is not None:
            os.chdir(self.new_dir)

    def __exit__(self, type, value, traceback):
        if self.new_dir is not None:
            os.chdir(self.old_dir)

class in_temporary_directory(object):
    def __init__(self):
      self.old_dir = os.getcwd()
      self.tmpdir = tempfile.mkdtemp()

    def __enter__(self):
      os.chdir(self.tmpdir)

    def __exit__(self, type, value, traceback):
      os.chdir(self.old_dir)
      shutil.rmtree(self.tmpdir)


def update_dict(d, u):
    '''update a data tree. i.e. a nested dict/list.'''

    if isinstance( u, collections.Mapping ):
    # if u is a dict, loop through all items and set corresponding
    # items in d. if any of the items in u are dict's, recursively update
    # items in d.
      if not isinstance(d, collections.Mapping):
        d = dict()
      for k, uv in u.items():
          if isinstance(uv, collections.Mapping):
              d[k] = update_dict(d.get(k, {}), uv)
          else:
              d[k] = uv
      return d
    else:
    # if u is not a dict, set d to the value of u
    # in other words, its possible to replace a dict with
    # a scalar, or a list.
      d = u
      return d


class PackageCollection:
    baseline_config = {
        "package_defaults": {
            "url_basename": "git@github.com:CD3",
            "checkout": "master",
            "version": None,
            "group": "cd3",
            "channel": None,
            "conanfile": "conanfile.py",
        },
        "package_overrides": {},
        "package_configs": {},
        "use_cache": []
    }

    def __init__(self, profile='default'):
        self.config = dict()
        self.packages = list()
        self.profile = profile

        name = '''(?P<name>[^/"']+)'''
        version = '''(?P<version>[^@"']+)'''
        group = '''(?P<group>[^/"']+)'''
        channel = '''(?P<channel>[^"']+)'''
        self.conan_reference_re = f"{name}/{version}@{group}/{channel}"

    def load_configs(self, files):
        self.config = copy.deepcopy(self.baseline_config)
        for file in files:
            with open(file, "r") as f:
                update_dict(self.config, yaml.load(f, Loader=yaml.SafeLoader))

    def get_package_name(self, p_path):
        return p_path.name

    def add_package(self, p_path):
        p_config = copy.deepcopy(self.config["package_defaults"])
        p_name = self.get_package_name(p_path)
        self.packages.append(p_name)
        p_config["folder"] = str(p_path)
        p_config["name"] = p_name
        update_dict(p_config, self.config["package_overrides"].get(p_name, {}))
        # check if package version was given as 'latest-release'
        # if so, determine what the latest release tag is
        if p_config["version"] == 'latest-release':
          print(f"Determining latest release for '{p_path}'")
          repo_name = p_config.get("repo_name", p_config.get("name") )
          url = f"{p_config['url_basename']}/{repo_name}"
          tag = get_latest_release( url, p_config["checkout"] )
          if tag is not None:
            print(f"\tFound '{tag}'")
            print(f"\tupdating 'checkout' and 'version' properties.")
            p_config["checkout"] = tag
            p_config["version"] = parsers.version_str.searchString(tag)[0][0]
          else:
            print("\tNo valid release tags found. Changing version to 'devel'")
            p_config["version"] = "devel"

        self.config["package_configs"][p_name] = p_config

    def add_packages(self, p_paths):
        for p_path in p_paths:
            self.add_package(p_path)

    def get_full_package_name(self, p_name):
        if p_name in self.config["package_configs"]:
            p_config = self.config["package_configs"][p_name]
            p_name = p_config["name"]
            p_version = p_config["version"]
            p_group = p_config["group"]
            p_channel = p_config["channel"]
            full_name = f"{p_name}/{p_version}@{p_group}/{p_channel}"
            return full_name
        else:
            return None

    def write_static_conanfile(self, p_name):
        """Writes a static conanfile with explicit references to each package in set
        set."""

        p_config = self.config["package_configs"][p_name]

        folder = Path(p_config["folder"])
        file = p_config["conanfile"]
        sfile = "conanfile-static.py"

        conanfile_text = (folder/file).read_text()

        # replace version and checkout settings for *this* package
        for setting in ["version", "checkout"]:
          regex = re.compile(f"^(\s*){setting}\s*=\s*.*",re.MULTILINE)
          value = p_config[setting]
          msg = "Note: this line was modified to make sure this setting is static."
          conanfile_text = re.sub( regex, fr"\1{setting} = '{value}' # {msg}", conanfile_text)
        # replace references to *dependencies*
        for m in re.finditer( fr'''["'](?P<conan_reference>{self.conan_reference_re})["']''', conanfile_text ):
          dep_reference = self.get_full_package_name( m.group('name'))
          if dep_reference is not None:
            pat = m.group("conan_reference")
            rep = dep_reference
            print(INFO+f"  replacing '{pat}' with '{rep}' in '{p_name}' package for static recipe")
            conanfile_text = conanfile_text.replace(pat,rep)

        (folder/sfile).write_text(conanfile_text)

        return folder/sfile




    def export_package(self, p_name, stdout):
        full_name = self.get_full_package_name(p_name)

        print(INFO + f"Exporting {p_name} to {full_name}" + EOL)
        use_cache_packages = self.filter_packages( self.config.get("use_cache", "none") )
        if p_name in use_cache_packages:
            print(
                INFO
                + f"  using cached package (if it exists) for {p_name}. {full_name} will NOT be removed from local cache."
                + EOL
            )
        else:
            print(INFO + f"  removing {full_name} from local cache" + EOL)
            rc = run(f"conan remove -f {full_name}", stdout, stdout)




        static_conanfile = self.write_static_conanfile(p_name)



        rc = run(f"conan export {static_conanfile} {full_name}", stdout, stdout)
        if rc != 0:
            print(
                ERROR
                + f"There was an error exporting {p_name}. You can view the output in {stdout.name}."
                + EOL
            )
            return 1
        return 0


    def create_packages(self):
        pass

    def a_deps_on_b( self, ref_a, ref_b ):
      '''Return true if package reference a (first argument) depends on package reference b (second argument.'''

      with tempfile.TemporaryDirectory() as dir:
        json_file = Path(dir)/"conan-info.json"
        stdout = Path(dir)/"conan-info.out"
        f = stdout.open('w')
        run( f"conan info {ref_a} --json {str(json_file)}",f,f )
        data = json.loads( (json_file.read_text()) )
        for p in data:
          if ref_b in p.get( 'requires', [] ):
            return True


      return False







    def filter_packages(self, config, packages=None):
        if packages is None:
            packages = self.packages

        fpackages = list()
        for package in packages:
            add = False

            if isinstance( config, str ):
              if config.lower() == "all":
                add = True
              elif config.lower() == "none":
                add = False
              else:
                raise Exception(f"Unknown filter string '{config}'")


            if isinstance( config, list ):
              if package in config:
                add = True

            if isinstance( config, dict ):
              if 'include' in config:
                patterns = config['include'] if isinstance(config['include'],list) else [config['include']]
                for pattern in patterns:
                  if re.match( pattern, package ):
                    add = True
              if 'exclude' in config:
                patterns = config['exclude'] if isinstance(config['exclude'],list) else [config['exclude']]
                for pattern in patterns:
                  if re.match( pattern, package ):
                    add = False

              if 'depends_on' in config:
                deps = config['depends_on'] if isinstance(config['depends_on'],list) else [config['depends_on']]
                for dep in deps:
                  if self.a_deps_on_b( self.get_full_package_name(package), self.get_full_package_name(dep) ):
                    add = True
                    break

            if add:
              fpackages.append(package)
        return fpackages

    


def get_version_tag(ref="HEAD"):
    querry_cmd = f"git describe --tags --abbrev=0 {ref}"
    result = subprocess.run(querry_cmd, shell=True, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8').strip()
    if output == "":
      return None
    try:
      parsers.version_tag.parseString(output)
      return output
    except:
      print(f"'{output}' does not appear to be a version tag. Looking at previous tag.")
      return get_version_tag( output+"^" )

    return None

def get_latest_release( url, branch="master"):
  version_tag = None
  with in_temporary_directory():
    cmd = f'git clone --single-branch --branch {branch} {url} repo'
    result = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode != 0:
      print("There was an error trying to clone the repository. Make sure the branch exists on the remote")
      print(f"Clone command: '{cmd}'")
      raise Exception()
    with working_directory("repo"):
      version_tag = get_version_tag()
  

  return version_tag
