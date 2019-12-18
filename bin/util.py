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
import glob
from pathlib import Path
from hashlib import sha1

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
  version_num = Word(nums) + Optional( (".") + Word(nums) + Optional( "." + Word(nums) + Optional( "." + Word(nums) ) ) )
  version_str = Combine(version_num)
  version_tag = Optional(Literal("v") ^ "ver-" ) + version_str

  name_re = '''(?P<name>[^/"']+)'''
  version_re = '''(?P<version>[^@"']+)'''
  owner_re = '''(?P<owner>[^/"']+)'''
  channel_re = '''(?P<channel>[^"']+)'''
  conan_reference_re = f"{name_re}/{version_re}@{owner_re}/{channel_re}"

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
    def __init__(self,delete=True):
      self.old_dir = os.getcwd()
      self.tmpdir = tempfile.mkdtemp()
      self.delete = delete

    def __enter__(self):
      os.chdir(self.tmpdir)
      return self.tmpdir

    def __exit__(self, type, value, traceback):
      os.chdir(self.old_dir)
      if self.delete:
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

class Package:
  '''Represents a conan package that can be exported. The package consists of:
       - A baseline conanfile that will be edited to create a conanfile to export the package.
       - A git url basename used to obtain the source.
       - A repo name used to obtain the source.
       - A checkout that will be used to checkout the commit to package.
       - A name that will be used for the conan package reference.
       - A version that will be used for the conan package reference.
       - An owner that will be used for the conan package referance.
       - A channel that will be used for the conan package reference.

     A Package knows how to:
       - Write a custom conan to export by editing the baseline conanfile and embedding
         information about the source URL, version number, etc. This requires the conan recipe
         to use variables for these parameters. See the conanfile.py recipes for an example.
       - Export the custom conan file to the local cache with a specific package reference id.
  '''


  def __init__(self):
    self.clear()

  def clear(self):
    self.baseline_conanfile = None
    self.git_url_basename = None
    self.repo_name = None
    self.checkout = None
    self.name = None
    self.version = None
    self.owner = None
    self.channel = None

    self.dependencies = None

    # self.setting_overrides = None
    # self.dependency_overrides = None

  def load(self,d):
    '''Load a package configuration from a dict. All current settings are erased. Any settings not contained by the dict will be left uninitialized.'''
    self.clear()
    self.update(d)
    
  def update(self,d):
    '''Update package configuration from a dict. All current settings that are not overwritten will remain.'''

    # we want support old parameter names
    # so we try them first, but overwrite them
    # with newer parameter names.
    self.baseline_conanfile = d.get("conanfile", self.baseline_conanfile)
    self.baseline_conanfile = d.get("baseline_conanfile", self.baseline_conanfile)

    self.git_url_basename = d.get("url_basename", self.git_url_basename )
    self.git_url_basename = d.get("git_url_basename", self.git_url_basename )

    self.repo_name = d.get("repo_name", self.repo_name)
    self.checkout = d.get("checkout", self.checkout)
    self.name = d.get("name", self.name)
    self.version = d.get("version", self.version)
    self.owner = d.get("group", self.owner)
    self.owner = d.get("owner", self.owner)
    self.channel = d.get("channel", self.channel)

    self.dependencies = d.get("dependencies", self.dependencies)

  @property
  def conan_package_name_and_version(self):
    return f"{self.name}/{self.version}"

  @property
  def conan_package_owner_and_channel(self):
    return f"{self.owner}/{self.channel}"

  @property
  def conan_package_reference(self):
    return f"{self.conan_package_name_and_version}@{self.conan_package_owner_and_channel}"

  @property
  def id(self):
    return sha1(json.dumps(self.__dict__).encode('utf-8')).hexdigest()

  @property
  def baseline_conanfile_path(self):
    return Path(self.baseline_conanfile)

  @property
  def instance_conanfile_path(self):
    return self.baseline_conanfile_path.parent / Path(self.baseline_conanfile_path.stem + "-" + self.id + self.baseline_conanfile_path.suffix)

  @property
  def instance_conanfile(self):
    return str(self.instance_conanfile_path)

  def write_instance_conanfile(self):
    # write an instance of the template conanfile for this package

    conanfile = self.instance_conanfile_path
    conanfile_text = None
    if self.baseline_conanfile_path.is_file():
      conanfile_text = self.baseline_conanfile_path.read_text()
    else:
      raise Exception( f"ERROR: baseline conanfile '{self.baseline_conanfile}' for package '{self.name}' does not exist. Check that it is accessible from '{os.getcwd()}'" )


    # replace package settings in recipe

    def replace_setting(key,value):
      if value is None:
        return

      nonlocal conanfile_text

      # first try to replace a setting named 'injected_{key}'
      # if that succeeds, then return to caller. if it does not
      # suceed, then try to replace the actual setting name
      # this gives the conan recipie a way to opt-out of having
      # a setting overwritten
      regex = re.compile(fr"^(\s*)injected_{key}\s*=\s*.*",re.MULTILINE)
      msg = "Note: this line was modified to make sure this setting is static."
      text,n = re.subn( regex, fr"\1injected_{key} = '{value}' # {msg}", conanfile_text)

      if n > 1:
        print(
              WARN
              + f"Replaced more than one instance of 'injected_{key}' in '{self.baseline_conanfile}'. Make sure you didn't use a local variable with the same name somewhere."
              + EOL )

      if n < 1:
        regex = re.compile(fr"^(\s*){key}\s*=\s*.*",re.MULTILINE)
        msg = "Note: this line was modified to make sure this setting is static."
        text,n = re.subn( regex, fr"\1{key} = '{value}' # {msg}", conanfile_text)
        if n < 1:
          print(
                WARN
                + f"Could not replace '{key}'. Parameter *must* be define a variable named '{self.baseline_conanfile}' file to replace."
                + EOL )

        if n > 1:
          print(
                WARN
                + f"Replaced more than one instance of '{key}' in '{self.baseline_conanfile}'. Make sure you didn't use a local variable with the same name somewhere."
                + EOL )
      

      conanfile_text = text



    replace_setting( "name", self.name )
    replace_setting( "version", self.version )
    replace_setting( "checkout", self.checkout )
    replace_setting( "git_url_basename", self.git_url_basename)
    replace_setting( "repo_name", self.repo_name)

    # replace package references with specific instances required by this instance
    print(INFO+f'''  Writing conan package reference instances for '{self.name}' instance recipe.''')
    if self.dependencies is not None:
      for instance in self.dependencies : # loop through instances
        instance_parse = re.match(fr'''(?P<conan_reference>{parsers.conan_reference_re})''',instance)
        if instance_parse is None:
          raise Exception(f"ERROR: it appears that a non-package reference (could not parse '{instance}' as a conan package reference) was listed in the 'dependencies' for '{self.name}'.")
        for reference_parse in re.finditer( fr'''["'](?P<conan_reference>{parsers.conan_reference_re})["']''', conanfile_text ): # loop to references in conanfile
          if reference_parse is not None:
            if instance_parse.group("name") == reference_parse.group("name"):
              print(INFO+f'''    replacing '{reference_parse.group("conan_reference")}' with '{instance}' ''')
              conanfile_text = conanfile_text.replace(reference_parse.group("conan_reference"),instance)
    print(EOL)




    conanfile.write_text( conanfile_text )

  def export(self, stdout=None):
    self.write_instance_conanfile()
    rc = run(f'''conan export "{self.instance_conanfile}" "{self.conan_package_owner_and_channel}" ''', stdout, stdout)
    if rc != 0:
      print(ERROR)
      print(f"There was an error exporting {self.name}.")
      if stdout is not None:
        print(f"You can view the output in {Path(stdout.name).resolve()}." )
      print(EOL)
      return 1
    return 0

  def build(self, stdout=None):
    rc = run(f'''conan install "{self.conan_package_reference}" --build="{self.name}" ''', stdout, stdout)
    if rc != 0:
      print(ERROR)
      print(f"There was an error building {self.name}.")
      if stdout is not None:
        print(f"You can view the output in {Path(stdout.name).resolve()}." )
      print(EOL)
      return 1
    return 0

  def test(self, stdout=None):
    test_folder = self.instance_conanfile_path.parent / "test_package"
    if test_folder.is_dir():
      rc = run(f'''conan test "{str(test_folder)}" "{self.conan_package_reference}"''', stdout, stdout)
      if rc != 0:
        print(ERROR)
        print(f"There was an error testing {self.name}.")
        if stdout is not None:
          print(f"You can view the output in {Path(stdout.name).resolve()}." )
        print(EOL)
        return 1
      return 0
    else:
      print(f"WARNING: no 'test_folder' found for {self.name} (looking for {str(test_folder)}). Package will not be tested")





  






class PackageCollection:

    def __init__(self):
      self.clear()

    def clear(self):
      self.config = dict()
      self.packages = list()

    def load(self,d=None):
      if d is None:
        d = self.config
      self.clear()
      self.update(d)

    def update(self,d=None):
      if d is None:
        d = self.config

      update_dict(self.config,d)

      for pi in self.config.get("package_instances",[]):
        p = Package()
        p.load( self.config.get("package_defaults",{} ))
        p.update( self.config.get("package_overrides",{}).get(pi.get("name"),{} ) )
        p.update( pi )
        self.packages.append(p)

      for p in self.packages:
        p.dependencies = self._build_dependency_set(p.dependencies)

    def _build_dependency_set(self, config):

      if config is None:
        return self._build_dependency_set("collection")

      if isinstance(config,str):
        if config.lower() == "clear all" or config.lower() == "clear":
          return []
        if config.lower() == "collection instances" or config.lower() == "collection":
          return [p.conan_package_reference for p in self.packages]

        dependency_parse = re.match(fr'''(?P<conan_reference>{parsers.conan_reference_re})''',config)
        if dependency_parse:
          return [config]
        else:
          raise Exception(f"Error: Dependency specification '{config}' is not a known command or valid connan package reference.")



      if isinstance(config,list):
        dependencies = []
        for item in config:
          if item == "clear":
            dependencies = []
            continue

          dependencies += self._build_dependency_set(item)

        return dependencies


    def add_from_conan_recipe_collection(self,dir):
      '''Build a package collection from a set of directories containing conanfiles. For example, a recipe repository.'''
      cwd = Path(dir)
      if not cwd.is_dir():
        raise Exception(f"Cannot build package collection from '{dir}', directory does not exist")

      if 'package_instances' not in self.config:
        self.config['package_instances'] = []
      for file in cwd.glob( 'recipes/*/conanfile.py' ):
        self.config['package_instances'].append( { 'name': file.parent.name, 'baseline_conanfile' : str(file.absolute()) } )

      self.load() # recreate packages

    def export_packages(self,config='all',stdout=None):
      pks = filter_packages(config,self.packages)
      for p in pks:
        p.export(stdout)

    def build_packages(self,config='all',stdout=None):
      pks = filter_packages(config,self.packages)
      for p in pks:
        p.build(stdout)

    def test_packages(self,config='all',stdout=None):
      pks = filter_packages(config,self.packages)
      for p in pks:
        p.test(stdout)











def filter_packages( config, packages ):

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
          if package.name in config:
            add = True

        if isinstance( config, dict ):
          if 'include' in config:
            patterns = config['include'] if isinstance(config['include'],list) else [config['include']]
            for pattern in patterns:
              if re.match( pattern, package.name ):
                add = True

          if 'exclude' in config:
            patterns = config['exclude'] if isinstance(config['exclude'],list) else [config['exclude']]
            for pattern in patterns:
              if re.match( pattern, package.name ):
                add = False

          if 'depends_on' in config:
            deps = config['depends_on'] if isinstance(config['depends_on'],list) else [config['depends_on']]
            for dep in deps:
              if a_deps_on_b( get_full_package_name(package), get_full_package_name(dep) ):
                add = True
                break

        if add:
          fpackages.append(package)
    return fpackages
    

def a_deps_on_b( ref_a, ref_b ):
  '''Return true if package reference a (first argument) depends on package reference b (second argument).'''

  with tempfile.TemporaryDirectory() as dir:
    json_file = Path(dir)/"conan-info.json"
    stdout = Path(dir)/"conan-info.out"
    f = stdout.open('w')
    res = run( f'''conan info "{ref_a}" --json "{str(json_file)}" ''',f,f )
    if res != 0:
      json_file.write_text("{}")
    data = json.loads( (json_file.read_text()) )
    for p in data:
      if ref_b in p.get( 'requires', [] ):
        return True


  return False


def get_latest_version_tag(ref="HEAD"):
    '''Returns the most recent version tag on the branch containing @ref.
       
       This function works by calling git describe on @ref to get the latest tag.
       If the tag does not look like a version tag, it recursively calls itself
       on the tag, which will then look at the second oldest tag. This is repeated
       until a version tag is found, or no more tags exist.
    '''
    querry_cmd = f'''git describe --tags --abbrev=0 "{ref}"'''
    result = subprocess.run(querry_cmd, shell=True, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8').strip()
    if output == "":
      return None
    try:
      parsers.version_tag.parseString(output)
      return output
    except:
      print(f"'{output}' does not appear to be a version tag. Looking at previous tag.")
      return get_latest_version_tag( output+"^" )

    return None


def get_latest_release( url, branch="master", major_series = None, predicates = None ):
  '''Returns the latest release tag on the @branch branch of a repository.
  
     This function works by cloning the repository into a temporary directory,
     checking out @branch, and calling `git_version_tag` on the head.
  '''
  if predicates is None:
    predicates = []

  if not isinstance(predicates,list):
    predicates = [predicates]

  if major_series:
    def is_in_major_series( version_tag ):
      version_parse = parsers.version_tag.parseString(version_tag)
      version_str = version_parse[-1]
      version_parse = parsers.version_num.parseString(version_str)
      major_num = version_parse[0]

      return major_num == str(major_series)
    predicates.append(is_in_major_series)



  version_tag = None
  with in_temporary_directory():
    cmd = f'''git clone --single-branch --branch "{branch}" "{url}" repo'''
    result = subprocess.run(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode != 0:
      print("There was an error trying to clone the repository. Make sure the branch exists on the remote")
      print(f"Clone command: '{cmd}'")
      raise Exception()
    with working_directory("repo"):
      version_tag = get_latest_version_tag()
      if predicates is not None and len(predicates) > 0:
        while version_tag is not None and not any([ p(version_tag) for p in predicates ]):
          version_tag = get_latest_version_tag(f'{version_tag}^')


  

  return version_tag

def is_exe(path):
    if sys.platform.startswith('win32'):
        return str(path).endswith(".exe")
    if sys.platform.startswith("linux"):
        return os.access(str(path), os.X_OK)
    return False

