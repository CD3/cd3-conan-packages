import util
import re
import subprocess
import yaml
import pytest
from pathlib import Path

def test_Package_configuration():

  config = {"key" : "val"}

  p = util.Package()

  p.load(config)

  assert( p.name is None )

  config["name"] = "MyPackage"

  p.update(config)

  assert p.name == "MyPackage"
  assert p.version  is None

  config = {"version" : "2.0"}

  p.load(config)
  assert p.name is None
  assert p.version == "2.0"

  config = {"version" : "2.0",
            'dependencies' : ["PackageA/1.0@initech/stable","PackageB/2.3@initech/devel"]}

  p.load(config)
  assert p.name is None
  assert p.version == "2.0"
  assert len(p.dependencies) == 2
  assert p.dependencies[0] == "PackageA/1.0@initech/stable"
  assert p.dependencies[1] == "PackageB/2.3@initech/devel"

def test_Package_conan_package_reference():
  config = {"name" : "MyPackage",
            "version" : "2.0",
            "group" : "Initech",
            "channel" : "unstable" }

  p = util.Package()
  p.load(config)

  assert p.conan_package_reference == "MyPackage/2.0@Initech/unstable"

  assert p.id is not None
  id = p.id
  assert type(id) == str
  assert p.id == id

  pp = util.Package()
  pp.load(config)

  assert pp.id == p.id

  p.update({"name":"myPackage"})

  assert p.id != id

  p.update({"name":"MyPackage"})

  assert p.id == id

  p.update({"repo_name":"example.com"})

  assert p.id != id

  p.update({"repo_name":None})

  assert p.id == id

def test_Package_write_conanfile():

  baseline_conanfile_text = '''
from conans import ConanFile, CMake
import os, glob

class ConanPackage(ConanFile):
    name = "Name Here"
    version = "master"
    checkout = "master"
    generators = "virtualenv"
    requires = "boost/1.69.0@conan/stable"
    build_requires = "cmake_installer/3.13.0@conan/stable"
    git_url_basename = "Missing"
    repo_name = None
    

    def source(self):
      pass

    def build(self):
      pass

    def package(self):
      pass

    def package_info(self):
      pass
'''

  def setting_regex(setting,value):
    # helper function that builds a regex to check that
    # a setting was written by the Package
    return re.compile(rf'''^\s*{setting}\s*=\s*['"]{value}['"]\s*#.*$''',re.MULTILINE)

  with util.in_temporary_directory() as d:

    p = util.Package()
    p.load( {"name" : "MyPackage",
              "version" : "2.0",
              "group" : "Initech",
              "channel" : "unstable",
              "conanfile" : "./conanfile.py",
              "dependencies" : ["PackageA/2.0@initech/devel",
                                     "boost/1.70@conan/stable",
                                    ],
            }
          )

    with open("conanfile.py",'w') as f:
      f.write(baseline_conanfile_text)
   
    assert not p.instance_conanfile_path.is_file()
    p.write_instance_conanfile()
    assert p.instance_conanfile_path.is_file()
    text = p.instance_conanfile_path.read_text()

    assert setting_regex("version","2.0").search(text)
    assert re.compile(r'''^\s*checkout = "master"$''',re.MULTILINE).search(text)
    assert re.search("boost/1.70@conan/stable",text)


  with util.in_temporary_directory() as d:

    p = util.Package()
    p.load( {"name" : "my_project",
              "version" : "2.0",
              "group" : "Initech",
              "channel" : "unstable",
              "conanfile" : "./conanfile.py",
              "checkout" : "v2.0",
              "git_url_basename" : "git://example.com",
              "repo_name" : "MyProject",
              }
          )

    with open("conanfile.py",'w') as f:
      f.write(baseline_conanfile_text)
   
    assert not p.instance_conanfile_path.is_file()
    p.write_instance_conanfile()
    assert p.instance_conanfile_path.is_file()
    text = p.instance_conanfile_path.read_text()

    assert setting_regex("name","my_project").search(text)
    assert setting_regex("version","2.0").search(text)
    assert setting_regex("checkout","v2.0").search(text)
    assert setting_regex("git_url_basename","git://example.com").search(text)
    assert setting_regex("repo_name","MyProject").search(text)

    assert re.search("boost/1.69.0@conan/stable",text)



def test_Package_export_package():
  baseline_conanfile_text = '''
from conans import ConanFile, CMake
import os, glob

class ConanPackage(ConanFile):
    name = "Name Here"
    version = "master"
    checkout = "master"
    generators = "virtualenv"
    requires = "boost/1.69.0@conan/stable"
    build_requires = "cmake_installer/3.13.0@conan/stable"
    git_url_basename = "Missing"
    repo_name = None

    def source(self):
      pass

    def build(self):
      pass

    def package(self):
      pass

    def package_info(self):
      pass
'''

  with util.in_temporary_directory() as d:

    p = util.Package()
    p.load( {"name" : "MyPackage",
              "version" : "2.0",
              "group" : "initech",
              "channel" : "unstable",
              "conanfile" : "./conanfile.py"}
          )

    with open("conanfile.py",'w') as f:
      f.write(baseline_conanfile_text)

    res = subprocess.run("conan remove -f MyPackage/*", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with open("export.out",'w') as f:
      p.export(f)
    res = subprocess.run("conan search MyPackage", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert re.match( ".*MyPackage/2.0@initech/unstable", str(res.stdout) )


def test_PackageCollection_configuration():

  config = yaml.load('''
package_defaults:
  owner : initech
  channel : devel
  version : devel
  checkout : master
package_overrides:
  PackA:
    version : master
package_instances:
  - name : PackA
  - name : PackB
    dependencies:
      - 'PackA/2.6@initech/stable'
  - name : PackC
    version : '1.1'
    checkout : 'v1.1'
  - name : PackA
    version : '2.6'
    checkout : 'v2.6'
    channel : 'stable'
    dependencies: []
  ''',Loader=yaml.SafeLoader)

  pc = util.PackageCollection()

  pc.load(config)

  assert len(pc.packages) == 4
  assert pc.packages[0].name == 'PackA'
  assert pc.packages[0].owner  == 'initech'
  assert pc.packages[0].channel == 'devel'
  assert pc.packages[0].version == 'master'
  assert pc.packages[0].checkout == 'master'
  assert pc.packages[0].conan_package_reference == 'PackA/master@initech/devel'
  assert len(pc.packages[0].dependencies) == 4
  assert pc.packages[0].dependencies[0] == "PackA/master@initech/devel"

  assert pc.packages[1].name == 'PackB'
  assert pc.packages[1].owner  == 'initech'
  assert pc.packages[1].channel == 'devel'
  assert pc.packages[1].version == 'devel'
  assert pc.packages[1].checkout == 'master'
  assert len(pc.packages[1].dependencies) == 1
  assert pc.packages[1].dependencies[0] == "PackA/2.6@initech/stable"

  assert pc.packages[2].name == 'PackC'
  assert pc.packages[2].owner  == 'initech'
  assert pc.packages[2].channel == 'devel'
  assert pc.packages[2].version == '1.1'
  assert pc.packages[2].checkout == 'v1.1'
  assert len(pc.packages[2].dependencies) == 4
  assert pc.packages[2].dependencies[0] == "PackA/master@initech/devel"

  assert pc.packages[3].name == 'PackA'
  assert pc.packages[3].owner  == 'initech'
  assert pc.packages[3].channel == 'stable'
  assert pc.packages[3].version == '2.6'
  assert pc.packages[3].checkout == 'v2.6'
  assert len(pc.packages[3].dependencies) == 0





def test_PackageCollection_build():
  config = yaml.load('''
package_defaults:
  owner : initech
  channel : integration-testing
  version : devel
  checkout : master
package_overrides:
  PackA:
    version : master
''',Loader=yaml.SafeLoader)

  pc = util.PackageCollection()
  pc.load(config)

  with util.in_temporary_directory() as d:
    path_a = Path('PackA')
    path_b = Path('PackB')
    path_c = Path('PackC')

    conan_a = path_a / 'conanfile.py'
    conan_b = path_b / 'conan-recipe.py' # should NOT get picked up
    conan_c = path_c / 'conanfile.py'

    path_a.mkdir()
    conan_a.touch()
    path_b.mkdir()
    conan_b.touch()
    path_c.mkdir()
    conan_c.touch()

    with pytest.raises(Exception):
      pc.add_from_conan_recipe_collection('/missing')

    names = [ p.parent.name for p in Path('.').glob('*/conanfile.py') ]

    pc.add_from_conan_recipe_collection('.')

    assert len(pc.packages) == 2

    idx = names.index('PackA')
    assert pc.packages[idx].name == 'PackA'
    assert pc.packages[idx].owner  == 'initech'
    assert pc.packages[idx].channel == 'integration-testing'
    assert pc.packages[idx].version == 'master'
    assert pc.packages[idx].checkout == 'master'
    assert len(pc.packages[idx].dependencies) == 2

    idx = names.index('PackC')
    assert pc.packages[idx].name == 'PackC'
    assert pc.packages[idx].owner  == 'initech'
    assert pc.packages[idx].channel == 'integration-testing'
    assert pc.packages[idx].version == 'devel'
    assert pc.packages[idx].checkout == 'master'
    assert len(pc.packages[idx].dependencies) == 2

    pc.add_from_conan_recipe_collection('.')

    assert len(pc.packages) == 4
    idx = names.index('PackA')
    assert pc.packages[idx].name == 'PackA'
    assert pc.packages[idx+2].name == 'PackA'
    idx = names.index('PackC')
    assert pc.packages[idx].name == 'PackC'
    assert pc.packages[idx+2].name == 'PackC'


def test_PackageCollection_export_packages():
  baseline_conanfile_text = '''
from conans import ConanFile, CMake
import os, glob

class ConanPackage(ConanFile):
    name = "Name Here"
    version = "master"
    checkout = "master"
    generators = "virtualenv"
    requires = "boost/1.69.0@conan/stable"
    build_requires = "cmake_installer/3.13.0@conan/stable"
    git_url_basename = "Missing"
    repo_name = None

    def source(self):
      pass

    def build(self):
      pass

    def package(self):
      pass

    def package_info(self):
      pass
'''

  res = subprocess.run("conan remove PackA -f", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove PackB -f", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove PackC -f", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  with util.in_temporary_directory() as d:
    path_a = Path('PackA')
    path_b = Path('PackB')
    path_c = Path('PackC')

    conan_a = path_a / 'conanfile.py'
    conan_b = path_b / 'conanfile.py'
    conan_c = path_c / 'conanfile.py'

    path_a.mkdir()
    conan_a.touch()
    path_b.mkdir()
    conan_b.touch()
    path_c.mkdir()
    conan_c.touch()

    with open(conan_a,'w') as f:
      f.write(baseline_conanfile_text)
    with open(conan_b,'w') as f:
      f.write(baseline_conanfile_text)
    with open(conan_c,'w') as f:
      f.write(baseline_conanfile_text)

    config = yaml.load('''
  package_defaults:
    owner : initech
    channel : devel
    version : master 
    checkout : master
  package_overrides:
    PackA:
      channel : channel-A
    PackB:
      channel : channel-B
    PackC:
      channel : channel-C
  ''',Loader=yaml.SafeLoader)

    pc = util.PackageCollection()
    pc.load(config)
    pc.add_from_conan_recipe_collection('.')
    pc.export_packages()

  res = subprocess.run("conan search PackA", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  assert re.match( ".*PackA/master@initech/channel-A", str(res.stdout) )
  res = subprocess.run("conan search PackB", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  assert re.match( ".*PackB/master@initech/channel-B", str(res.stdout) )
  res = subprocess.run("conan search PackC", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  assert re.match( ".*PackC/master@initech/channel-C", str(res.stdout) )


def test_a_deps_on_b():
  baseline_conanfile_text = '''
from conans import ConanFile, CMake
import os, glob

class ConanPackage(ConanFile):
    name = "MyPackage"
    version = "master"
    checkout = "master"
    generators = "virtualenv"
    requires = "boost/1.69.0@conan/stable"
    build_requires = "cmake_installer/3.13.0@conan/stable"
    git_url_basename = "Missing"
    repo_name = None

    def source(self):
      pass

    def build(self):
      pass

    def package(self):
      pass

    def package_info(self):
      pass
'''

  with util.in_temporary_directory() as d:
    path = Path('MyPackage')
    conan = path / 'conanfile.py'

    path.mkdir()
    conan.touch()

    with open(conan,'w') as f:
      f.write(baseline_conanfile_text)

    p = util.Package()
    p.load( {
            'name' : 'MyPackage',
            'version' : '2.0',
            'owner' : 'me',
            'channel' : 'devel',
            'conanfile' : str(conan),
            } )
    p.export()

  assert util.a_deps_on_b( "MyPackage/2.0@me/devel", "boost/1.69.0@conan/stable" )
  assert not util.a_deps_on_b( "MyPackage/2.0@me/devel", "MyOtherPackage/2.0@initech/devel" )



def test_filter_packages():

  config = yaml.load('''
package_defaults:
  owner : initech
  channel : devel
  version : devel
  checkout : master
  ''',Loader=yaml.SafeLoader)

  pc = util.PackageCollection()
  pc.load(config)



  res = subprocess.run("conan remove -f MyPackage", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove -f PackA", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove -f PackB", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove -f PackC", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  
  baseline_conanfile_text = '''
from conans import ConanFile, CMake
import os, glob

class ConanPackage(ConanFile):
    name = "Name"
    version = "master"
    checkout = "master"
    generators = "virtualenv"
    requires = "boost/1.69.0@conan/stable"
    build_requires = "cmake_installer/3.13.0@conan/stable"
    git_url_basename = "Missing"
    repo_name = None

    def source(self):
      pass

    def build(self):
      pass

    def package(self):
      pass

    def package_info(self):
      pass
'''

  with util.in_temporary_directory() as d:
    path = Path('PackA')
    conan = path / 'conanfile.py'
    path.mkdir()
    conan.touch()
    with open(conan,'w') as f:
      f.write(baseline_conanfile_text)

    path = Path('PackB')
    conan = path / 'conanfile.py'
    path.mkdir()
    conan.touch()
    baseline_conanfile_text = baseline_conanfile_text.replace("boost/1.69.0@conan/stable", "PackA/devel@initech/devel")
    with open(conan,'w') as f:
      f.write(baseline_conanfile_text)

    path = Path('PackC')
    conan = path / 'conanfile.py'
    path.mkdir()
    conan.touch()
    baseline_conanfile_text = baseline_conanfile_text.replace("PackA/devel@initech/devel","PackB/devel@initech/devel")
    with open(conan,'w') as f:
      f.write(baseline_conanfile_text)

    pc.add_from_conan_recipe_collection('.')
    pc.export_packages()




  assert len( util.filter_packages('all',pc.packages)) == 3
  assert len( util.filter_packages('none',pc.packages)) == 0
  assert len( util.filter_packages(['PackA', 'PackB'],pc.packages)) == 2
  assert len( util.filter_packages(['PackA', 'PackB', 'PackD'],pc.packages)) == 2
  assert len( util.filter_packages({'include':'Pack'},pc.packages)) == 3
  assert len( util.filter_packages({'include': 'Pack.*'},pc.packages)) == 3
  assert len( util.filter_packages({'include':'.*A'},pc.packages)) == 1
  assert len( util.filter_packages({'exclude':'None'},pc.packages)) == 0
  assert len( util.filter_packages({'include':'.*', 'exclude':'None'},pc.packages)) == 3
  assert len( util.filter_packages({'include':'.*', 'exclude':'.*A$'},pc.packages)) == 2


  assert util.a_deps_on_b( "PackA/devel@initech/devel", "boost/1.69.0@conan/stable" )
  assert not util.a_deps_on_b( "PackA/devel@initech/devel", "PackB/devel@initech/devel" )
  assert not util.a_deps_on_b( "PackA/devel@initech/devel", "PackC/devel@initech/devel" )
  assert util.a_deps_on_b( "PackB/devel@initech/devel", "PackA/devel@initech/devel" )
  assert util.a_deps_on_b( "PackB/devel@initech/devel", "boost/1.69.0@conan/stable" ) # PackA depends on boost, so PackB will too
  assert util.a_deps_on_b( "PackC/devel@initech/devel", "PackB/devel@initech/devel" )
  assert util.a_deps_on_b( "PackC/devel@initech/devel", "PackA/devel@initech/devel" )
  assert util.a_deps_on_b( "PackC/devel@initech/devel", "boost/1.69.0@conan/stable" )


def test_PackageCollection__build_dependency_set():
  config = yaml.load('''
package_defaults:
  owner : initech
  channel : devel
  version : devel
  checkout : master
package_overrides:
  PackA:
    version : master
package_instances:
  - name : PackA
  - name : PackB
    dependencies:
      - 'PackA/2.6@initech/stable'
  - name : PackC
    version : '1.1'
    checkout : 'v1.1'
  - name : PackA
    version : '2.6'
    checkout : 'v2.6'
    channel : 'stable'
    dependencies: []
  ''',Loader=yaml.SafeLoader)

  pc = util.PackageCollection()

  pc.load(config)

