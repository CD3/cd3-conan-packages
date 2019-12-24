import util
import re
import subprocess
import yaml
import pytest
from pathlib import Path

def test_PackageInstance_configuration():

  config = {"key" : "val"}

  p = util.PackageInstance()

  p.load(config)

  assert( p.conanfile is None )
  assert( p.setting_overrides is None )
  assert( p.dependency_overrides is None )

  config["conanfile"] = "MyPackage.py"

  p.update(config)

  assert p.conanfile == "MyPackage.py"
  assert( p.setting_overrides is None )
  assert( p.dependency_overrides is None )

  config = {"setting_overrides" : {"name": "MyPackage"} }

  p.load(config)
  assert p.conanfile is None
  assert isinstance( p.setting_overrides, dict)
  assert len(p.setting_overrides) == 1
  assert "name" in p.setting_overrides
  assert p.setting_overrides["name"] == "MyPackage"


  config = {"conanfile":"MyPackage.py", "setting_overrides" : {"name": "MyPackage"}, "dependency_overrides": ["MyDep/*@cd3/testing"] }

  p.load(config)
  assert p.conanfile == "MyPackage.py"
  assert "name" in p.setting_overrides
  assert len(p.dependency_overrides) > 0


def test_PackageInstance_write_conanfile():

  conanfile_text = '''
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

  def setting_regex(setting,value,modified=True):
    # helper function that builds a regex to check that
    # a setting was written by the Package
    if modified:
      return re.compile(rf'''^\s*{setting}\s*=\s*['"]{value}['"]\s*#.*$''',re.MULTILINE)
    else:
      return re.compile(rf'''^\s*{setting}\s*=\s*['"]{value}['"]\s*$''',re.MULTILINE)

  with util.in_temporary_directory() as d:

    p = util.PackageInstance()
    p.load( { "conanfile" : "./conanfile.py",
              "setting_overrides" : {
                "version" : "2.0",
                "requires" : "boost/1.70@conan/stable"
                },
            }
          )

    with open("conanfile.py",'w') as f:
      f.write(conanfile_text)
   
    assert not p.instance_conanfile_path.is_file()
    p.write_instance_conanfile()
    assert p.instance_conanfile_path.is_file()
    text = p.instance_conanfile_path.read_text()

    assert setting_regex("name","Name Here",False).search(text)
    assert setting_regex("version","2.0",True).search(text)
    assert setting_regex("checkout","master",False).search(text)
    assert re.search("boost/1.70@conan/stable",text)


  with util.in_temporary_directory() as d:

    p = util.PackageInstance()
    p.load( { "conanfile" : "./conanfile.py",
              "setting_overrides" :
               {"name" : "my_project",
                "version" : "2.0",
                "group" : "Initech",
                "channel" : "unstable",
                "checkout" : "v2.0",
                "git_url_basename" : "git://example.com",
                "repo_name" : "MyProject",
               }
             }
          )

    with open("conanfile.py",'w') as f:
      f.write(conanfile_text)
   
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



def test_PackageInstance_export_package():
  conanfile_text = '''
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

    p = util.PackageInstance()
    p.load( {"setting_overrides" : {
              "name" : "MyPackage",
              "version" : "2.0",
              },
              "conanfile" : "./conanfile.py"
              }
          )

    with open("conanfile.py",'w') as f:
      f.write(conanfile_text)

    res = subprocess.run("conan remove -f MyPackage/*", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with open("export.out",'w') as f:
      p.export(stdout=f,owner="initech",channel="unstable")
    res = subprocess.run("conan search ", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert re.match( ".*MyPackage/2.0@initech/unstable", str(res.stdout) )


def test_PackageCollection_configuration():

  config = yaml.load('''
global:
  export:
    owner : initech
    channel : devel
  setting_overrides:
    version : devel
    checkout : master
package_instances:
  - conanfile: PackA/conanfile.py
  - conanfile: PackB/conanfile.py
    dependency_overrides:
      - 'PackA/2.6@initech/stable'
  - conanfile : PackC/conanfile.py
    setting_overrides:
      version : '1.1'
      checkout : 'v1.1'
  - conanfile: PackA/conanfile.py
    channel : 'stable'
    setting_overrides:
      version : '2.6'
      checkout : 'v2.6'
  ''',Loader=yaml.SafeLoader)

  pc = util.PackageCollection()

  pc.load(config)

  assert len(pc.package_instances) == 4
  assert pc.package_instances[0].conanfile == 'PackA/conanfile.py'
  assert pc.package_instances[0].setting_overrides['version'] == 'devel'
  assert pc.package_instances[0].setting_overrides['checkout'] == 'master'

  assert pc.package_instances[1].conanfile == 'PackB/conanfile.py'
  assert pc.package_instances[1].setting_overrides['version'] == 'devel'
  assert pc.package_instances[1].setting_overrides['checkout'] == 'master'

  assert pc.package_instances[2].conanfile == 'PackC/conanfile.py'
  assert pc.package_instances[2].setting_overrides['version'] == '1.1'
  assert pc.package_instances[2].setting_overrides['checkout'] == 'v1.1'

  assert pc.package_instances[3].conanfile == 'PackA/conanfile.py'
  assert pc.package_instances[3].setting_overrides['version'] == '2.6'
  assert pc.package_instances[3].setting_overrides['checkout'] == 'v2.6'





def test_PackageCollection_build():
  config = yaml.load('''
global:
  export:
    owner : initech
    channel : devel
  setting_overrides:
    version : devel
    checkout : master
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

    assert len(pc.package_instances) == 2

    idx = names.index('PackA')
    assert pc.package_instances[idx].conanfile == str(Path('PackA/conanfile.py').resolve())
    assert pc.package_instances[idx].setting_overrides['version'] == 'devel'
    assert pc.package_instances[idx].setting_overrides['checkout'] == 'master'

    idx = names.index('PackC')
    assert pc.package_instances[idx].conanfile == str(Path('PackC/conanfile.py').resolve())
    assert pc.package_instances[idx].setting_overrides['version'] == 'devel'
    assert pc.package_instances[idx].setting_overrides['checkout'] == 'master'

    pc.add_from_conan_recipe_collection('.')

    assert len(pc.package_instances) == 4
    idx = names.index('PackA')
    assert pc.package_instances[idx].conanfile == str(Path('PackA/conanfile.py').resolve())
    assert pc.package_instances[idx-2].conanfile == str(Path('PackA/conanfile.py').resolve())
    idx = names.index('PackC')
    assert pc.package_instances[idx].conanfile == str(Path('PackC/conanfile.py').resolve())
    assert pc.package_instances[idx-2].conanfile == str(Path('PackC/conanfile.py').resolve())


def test_PackageCollection_export_packages():
  conanfile_text = '''
from conans import ConanFile, CMake
import os, glob

class ConanPackage(ConanFile):
    name = "Name Here"
    version = "Unknown"
    checkout = "Unknown"
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
      f.write(conanfile_text.replace("Name Here","PackA"))
    with open(conan_b,'w') as f:
      f.write(conanfile_text.replace("Name Here","PackB"))
    with open(conan_c,'w') as f:
      f.write(conanfile_text.replace("Name Here","PackC"))

    config = yaml.load('''
global:
  export:
    owner : initech
    channel : devel
  setting_overrides:
    version : master 
    checkout : master
  ''',Loader=yaml.SafeLoader)

    pc = util.PackageCollection()
    pc.load(config)
    pc.add_from_conan_recipe_collection('.')
    pc.export_packages()

  res = subprocess.run("conan search PackA", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  assert re.match( ".*PackA/master@initech/devel", str(res.stdout) )
  res = subprocess.run("conan search PackB", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  assert re.match( ".*PackB/master@initech/devel", str(res.stdout) )
  res = subprocess.run("conan search PackC", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  assert re.match( ".*PackC/master@initech/devel", str(res.stdout) )


def test_a_deps_on_b():
  conanfile_text = '''
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
      f.write(conanfile_text)

    p = util.PackageInstance()
    p.load( {'conanfile' : str(conan),
            'setting_overrides' : {
            'name' : 'MyPackage',
            'version' : '2.0',
            }} )
    p.export(owner='me', channel='devel')

  assert util.a_deps_on_b( "MyPackage/2.0@me/devel", "boost/1.69.0@conan/stable" )
  assert not util.a_deps_on_b( "MyPackage/2.0@me/devel", "MyOtherPackage/2.0@initech/devel" )



def test_filter_packages():

  config = yaml.load('''
global:
  export:
    owner : initech
    channel : devel
  setting_overrides:
    version : devel
    checkout : master
  ''',Loader=yaml.SafeLoader)

  pc = util.PackageCollection()
  pc.load(config)



  res = subprocess.run("conan remove -f MyPackage", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove -f PackA", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove -f PackB", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  res = subprocess.run("conan remove -f PackC", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  
  conanfile_text = '''
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
      f.write(conanfile_text.replace("Name","PackA"))

    path = Path('PackB')
    conan = path / 'conanfile.py'
    path.mkdir()
    conan.touch()
    conanfile_text = conanfile_text.replace("boost/1.69.0@conan/stable", "PackA/devel@initech/devel")
    with open(conan,'w') as f:
      f.write(conanfile_text.replace("Name","PackB"))

    path = Path('PackC')
    conan = path / 'conanfile.py'
    path.mkdir()
    conan.touch()
    conanfile_text = conanfile_text.replace("PackA/devel@initech/devel","PackB/devel@initech/devel")
    with open(conan,'w') as f:
      f.write(conanfile_text.replace("Name","PackC"))

    pc.add_from_conan_recipe_collection('.')
    pc.export_packages()




  assert len( util.filter_packages('all',pc.package_instances)) == 3
  assert len( util.filter_packages('none',pc.package_instances)) == 0
  assert len( util.filter_packages(['PackA', 'PackB'],pc.package_instances)) == 2
  assert len( util.filter_packages(['PackA', 'PackB', 'PackD'],pc.package_instances)) == 2
  assert len( util.filter_packages({'include':'Pack'},pc.package_instances)) == 3
  assert len( util.filter_packages({'include': 'Pack.*'},pc.package_instances)) == 3
  assert len( util.filter_packages({'include':'.*A'},pc.package_instances)) == 1
  assert len( util.filter_packages({'exclude':'None'},pc.package_instances)) == 0
  assert len( util.filter_packages({'include':'.*', 'exclude':'None'},pc.package_instances)) == 3
  assert len( util.filter_packages({'include':'.*', 'exclude':'.*A$'},pc.package_instances)) == 2


  assert util.a_deps_on_b( "PackA/devel@initech/devel", "boost/1.69.0@conan/stable" )
  assert not util.a_deps_on_b( "PackA/devel@initech/devel", "PackB/devel@initech/devel" )
  assert not util.a_deps_on_b( "PackA/devel@initech/devel", "PackC/devel@initech/devel" )
  assert util.a_deps_on_b( "PackB/devel@initech/devel", "PackA/devel@initech/devel" )
  assert util.a_deps_on_b( "PackB/devel@initech/devel", "boost/1.69.0@conan/stable" ) # PackA depends on boost, so PackB will too
  assert util.a_deps_on_b( "PackC/devel@initech/devel", "PackB/devel@initech/devel" )
  assert util.a_deps_on_b( "PackC/devel@initech/devel", "PackA/devel@initech/devel" )
  assert util.a_deps_on_b( "PackC/devel@initech/devel", "boost/1.69.0@conan/stable" )


def test_get_latest_version_tag_and_get_latest_release():
  with util.in_temporary_directory() as d:
    print(d)
    repo = Path("MyProject").resolve()

    repo.mkdir()
    with util.working_directory(str(repo)):
      file = Path("file.txt")
      file.touch()
      util.run('git init')
      util.run('git add .')
      util.run('git commit -m "initial import"') 
      
      def edit_commit_tag(version, num=1):
        for i in range(num):
          file.write_text(f"{version} commit {i}")
          util.run(f'git add .')
          util.run(f'git commit -m "pre-{version} edit {i}"') 
        util.run(f'git tag {version}') 

      edit_commit_tag("v1.0",1)
      edit_commit_tag("v1.1",2)
      edit_commit_tag("v1.1.1",2)
      edit_commit_tag("v1.1.2",1)
      edit_commit_tag("v2.0",5)
      edit_commit_tag("v2.1",2)
      edit_commit_tag("v2.1.1",2)
      edit_commit_tag("v2.1.2",1)
      edit_commit_tag("v2.2",1)
      edit_commit_tag("v2.3",2)
      util.run("git checkout -b devel")
      edit_commit_tag("v2.3.1",2)
      edit_commit_tag("v3",2)
      edit_commit_tag("v3.1",3)
      edit_commit_tag("v3.1.1",3)
      edit_commit_tag("v3.1.2",3)
      edit_commit_tag("v3.2.0",3)

      assert util.get_latest_version_tag() == "v3.2.0"
      assert util.get_latest_version_tag("HEAD^") == "v3.1.2"
      assert util.get_latest_version_tag("HEAD^^") == "v3.1.2"
      assert util.get_latest_version_tag("v3.2.0^") == "v3.1.2"
      assert util.get_latest_version_tag("v3.1.2^") == "v3.1.1"
      assert util.get_latest_version_tag("v3.1.1^") == "v3.1"
      assert util.get_latest_version_tag("v3.1^") == "v3"
      assert util.get_latest_version_tag("v3^") == "v2.3.1"

      assert util.get_latest_release( repo ) == "v2.3"
      assert util.get_latest_release( repo, major_series = '1' ) == "v1.1.2"
      assert util.get_latest_release( repo, "devel" ) == "v3.2.0"
      assert util.get_latest_release( repo, "devel", major_series = '2' ) == "v2.3.1"







