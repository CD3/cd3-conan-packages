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
import textwrap
import inspect
from fspathdict import pdict
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

def override_dependency( dependency, overrides ):
  name_re = '''(?P<name>[^/"']+)'''
  version_re = '''(?P<version>[^@"']+)'''
  owner_re = '''(?P<owner>[^/"']+)'''
  channel_re = '''(?P<channel>[^"']+)'''
  conan_reference_re = f"{name_re}/{version_re}@{owner_re}/{channel_re}"

  import re
  new_dependency = dependency
  dependency_match = re.match(conan_reference_re,dependency)
  for override in overrides:
    override_match = re.match(conan_reference_re,override)

    dep = None
    if override_match['name'] == dependency_match['name'] or override_match['name'].find("[name]") >= 0:
      dep = dict()
      for item in ["name", "version","owner","channel"]:
        dep[item] = override_match[item].replace(f'[{item}]',dependency_match[item])

    if dep is not None:
      new_dependency = "{name}/{version}@{owner}/{channel}".format(**dep)

  return new_dependency
  

class PackageInstance:
  '''Represents a instance of a conan package that can be exported. The package instance consists of:
       - A conanfile that will be used as the basis of the recipe that will be generated.
       - A set of setting overrides that will override settings in the conanfile.
       - A set of requires overrides that will override package requirments in the conanfile.

     A PackageInstance knows how to:
       - Write a modified conan recipe to export by editing the conanfile with the settings_overrides,
         dependency_overrides, etc.
       - Export the custom conan file to the local cache with a specific package reference id.
  '''


  def __init__(self):
    self.clear()

  def clear(self):
    self.conanfile = None
    self.setting_overrides = None
    self.dependency_overrides = None

    self._name = None

  def load(self,d):
    '''Load a package configuration from a dict. All current settings are erased. Any settings not contained by the dict will be left uninitialized.'''
    self.clear()
    self.update(d)
    
  def update(self,d):
    '''Update package configuration from a dict. All current settings that are not overwritten will remain.'''

    # if we want support old parameter names
    # we should try them first, but overwrite them
    # with newer parameter names.

    self._name     = d.get("name", "unknown")
    self.conanfile = d.get("conanfile", self.conanfile)
    self.setting_overrides = d.get("setting_overrides", self.setting_overrides)
    self.dependency_overrides = d.get("dependency_overrides", self.dependency_overrides)

  @property
  def name(self):
    return self._name
    
  @property
  def id(self):
    return sha1(json.dumps(self.__dict__).encode('utf-8')).hexdigest()

  @property
  def conanfile_path(self):
    return Path(self.conanfile)

  @property
  def instance_conanfile_path(self):
    return self.conanfile_path.parent / Path(self.conanfile_path.stem + "-" + self.id + self.conanfile_path.suffix)

  @property
  def instance_conanfile(self):
    return str(self.instance_conanfile_path)

  def write_instance_conanfile(self):
    # write an instance of the template conanfile for this package

    conanfile = self.instance_conanfile_path
    conanfile_text = None
    if self.conanfile_path.is_file():
      conanfile_text = self.conanfile_path.read_text()
    else:
      raise Exception( f"ERROR: baseline conanfile '{self.conanfile}' for package '{self.name}' does not exist. Check that it is accessible from '{os.getcwd()}'" )

    instance_conanfile_text = f'''
{inspect.getsource(override_dependency)}
# creating a local scope to put the original conanfile into
def Wrapper():
{textwrap.indent(conanfile_text,prefix='    ')}

    import inspect
    for name,obj in locals().items():
      if inspect.isclass(obj):
        for base in obj.__bases__:
          if base.__name__ == "ConanFile":
            return ConanPackage
    raise Exception("ERROR: Could not find a class subclassing from the ConanFile class.")

class ConanPackageInstance(Wrapper()):
'''

    text_to_add = ""
    if self.setting_overrides is not None:
      for setting,value in self.setting_overrides.items():
        if isinstance(value,str):
          text_to_add += f"{setting} = '{value}'\n"
        else:
          text_to_add += f"{setting} = {value}\n"

    if self.dependency_overrides is not None:
      text_to_add += f'''dependency_overrides = ['{"','".join(self.dependency_overrides)}']\n'''

    def requirements(self):
        if hasattr(self,'dependency_overrides'):
          old_requirements = self.requires.copy()
          self.requires.clear()
          for name,reference in old_requirements.iteritems():
            self.requires( override_dependency(str(reference), self.dependency_overrides))
    text_to_add += textwrap.dedent(inspect.getsource(requirements))
    if text_to_add == "":
      text_to_add = "pass\n"





    instance_conanfile_text += textwrap.indent(text_to_add,'    ')





    conanfile.write_text( instance_conanfile_text )

  def export(self, owner, channel, stdout=None):
    self.write_instance_conanfile()
    print(f"Exporting {self.instance_conanfile} to {owner}/{channel}")
    rc = run(f'''conan export "{self.instance_conanfile}" {owner}/{channel}''', stdout, stdout)
    if rc != 0:
      print(ERROR)
      print(f"There was an error exporting {self.conanfile}.")
      if stdout is not None:
        print(f"You can view the output in {Path(stdout.name).resolve()}." )
      print(EOL)
      return 1
    return 0

  def create(self, owner, channel, stdout=None):
    self.write_instance_conanfile()
    rc = run(f'''conan create "{self.instance_conanfile}" {owner}/{channel}''', stdout, stdout)
    if rc != 0:
      print(ERROR)
      print(f"There was an error creating {self.conanfile}.")
      if stdout is not None:
        print(f"You can view the output in {Path(stdout.name).resolve()}." )
      print(EOL)
      return 1
    return 0




  






class PackageCollection:

    def __init__(self):
      self.clear()

    def clear(self):
      self.config = dict()
      self.package_instances = list()

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
        p = PackageInstance()
        p.load( self.config.get("global",{} ))
        p.update( pi )
        self.package_instances.append(p)

    def add_conanfile(self,conanfile):
      if 'package_instances' not in self.config:
        self.config['package_instances'] = []

      file = Path(conanfile)
      self.config['package_instances'].append( { 'name': file.parent.name, 'conanfile' : str(file.absolute()) } )

    def add_from_conan_recipe_collection(self,dir):
      '''Build a package collection from a set of directories containing conanfiles. For example, a recipe repository.'''
      cwd = Path(dir)
      if not cwd.is_dir():
        raise Exception(f"Cannot build package collection from '{dir}', directory does not exist")

      for file in cwd.glob( '*/conanfile.py' ):
        self.add_conanfile(str(file.absolute()))

      self.load() # recreate packages

    def export_packages(self,config='all',stdout=None):
      pks = filter_packages(config,self.package_instances)
      config = pdict(self.config)
      owner = config.get("/global/export/owner","Unknown")
      channel = config.get("/global/export/channel","Unknown")
      for p in pks:
        p.export(owner=owner,channel=channel,stdout=stdout)

    def create_packages(self,config='all',stdout=None):
      pks = filter_packages(config,self.package_instances)
      config = pdict(self.config)
      owner = config.get("/global/export/owner","Unknown")
      channel = config.get("/global/export/channel","Unknown")
      for p in pks:
        p.create(owner=owner,channel=channel,stdout=stdout)










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

