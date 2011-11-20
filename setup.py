from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.command.install import INSTALL_SCHEMES
import os
import sys


def return_version():
	return __import__('dirtt').get_version()


class osx_install_data(install_data):
  # On MacOS, the platform-specific lib dir is /System/Library/Framework/Python/.../
  # which is wrong. Python 2.5 supplied with MacOS 10.5 has an Apple-specific fix
  # for this in distutils.command.install_data#306. It fixes install_lib but not
  # install_data, which is why we roll our own install_data class.

  def finalize_options(self):
    # By the time finalize_options is called, install.install_lib is set to the
    # fixed directory, so we set the installdir to install_lib. The
    # install_data class uses ('install_data', 'install_dir') instead.
    self.set_undefined_options('install', ('install_lib', 'install_dir'))
    install_data.finalize_options(self)

if sys.platform == "darwin": 
  cmdclasses = {'install_data': osx_install_data} 
else: 
  cmdclasses = {'install_data': install_data} 


def fullsplit(path, result=None):
  """
  Split a pathname into components (the opposite of os.path.join) in a
  platform-neutral way.
  """
  if result is None:
    result = []
  head, tail = os.path.split(path)
  if head == '':
    return [tail] + result
  if head == path:
    return result
  return fullsplit(head, [tail] + result)


# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
  scheme['data'] = scheme['purelib']


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
  os.chdir(root_dir)
dirtt_dir = 'dirtt'

for dirpath, dirnames, filenames in os.walk(dirtt_dir):
  # Ignore dirnames that start with '.'
  for i, dirname in enumerate(dirnames):
    if dirname.startswith('.'): del dirnames[i]
  if '__init__.py' in filenames:
    packages.append('.'.join(fullsplit(dirpath)))
  elif filenames:
    data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# Small hack for working with bdist_wininst.
# See http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
if len(sys.argv) > 1 and sys.argv[1] == 'bdist_wininst':
  for file_info in data_files:
    file_info[0] = '\\PURELIB\\%s' % file_info[0]


setup(
	name='python-dirtt',
	packages=packages,
	cmdclass = cmdclasses,
	scripts=['dirtt/scripts/mkdirt','dirtt/scripts/mkproj'],
	data_files = data_files,
#  data_files=[
#    ('/var/dirtt/dtds/dirtt.dtd', ['dirtt/data/dtds/dirtt.dtd']),
#    ('/var/dirtt/templates/project.xml', ['dirtt/data/templates/project.xml']),
#    ('/var/dirtt/templates/sequence.xml', ['dirtt/data/templates/sequence.xml']),
#    ('/var/dirtt/templates/shot.xml', ['dirtt/data/templates/shot.xml']),
#    ('/var/dirtt/templates/dshng_project.xml', ['dirtt/data/templates/dshng_project.xml']),
#    ('/var/dirtt/templates/dshng_sequence.xml', ['dirtt/data/templates/dshng_sequence.xml']),
#    ('/var/dirtt/templates/dshng_shot.xml', ['dirtt/data/templates/dshng_shot.xml'])
#  ],
	version=return_version(),
	description="Directory Tree Templater",
	long_description="""
		python-dirtt - Directory Tree Templater
		(c) 2011 Dashing Collective Inc. and contributors
		Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
		
		dirtt is a standalone tool and library used to generate 
		directory and file structures from xml templates that describe 
		repeatedly used filesystem layouts such as project structures
		or elements therein.
		
		It provides a subclassed implementation of xml.sax.handler ContentHandler
		with internal methods that read,parse,render,and execute builds of
		user defined XML directory tree templates.
		
		""",
	classifiers=[
		'Development Status :: 2 - Beta',
		'Intended Audience :: Developers',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python',
		'Natural Language :: English',
		'Operating System :: POSIX :: Linux',
		'Operating System :: MacOS :: MacOS X',
		'Topic :: System :: Systems Administration',
		'Topic :: Text Processing :: Markup :: XML'
	],
	keywords='filesystem template utilities',
	author='Robert Moggach',
	author_email='rob@dashing.tv',
	maintainer='Dashing Collective Inc.',
	maintainer_email='rob@dashing.tv',
	license='MIT'
)

