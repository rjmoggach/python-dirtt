import sys, os
try:
    from setuptools import setup
    kw = {'entry_points':
          """[console_scripts]\ndirtt = dirtt:main\n""",
          'zip_safe': False}
except ImportError:
    from distutils.core import setup
    if sys.platform == 'win32':
        print('Note: dirtt is not mean for UNC type paths with disk letters, etc.')
        kw = {}
    else:
        kw = {'scripts': ['scripts/dirtt']}

here = os.path.dirname(os.path.abspath(__file__))

## Get long_description from index.txt:
f = open(os.path.join(here, 'docs', 'index.txt'))
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()
f = open(os.path.join(here, 'docs', 'news.txt'))
long_description += "\n\n" + f.read()
f.close()

version = __import__('dirtt').get_version()


setup(name='dirtt',
      version=version,
      description="Directory Tree Templater",
      long_description=long_description,
      classifiers=[
        'Development Status :: 5 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        ],
      keywords='setuptools deployment installation distutils',
      author='Robert Moggach',
      author_email='rob@dashing.tv',
      maintainer='Dashing Collective Inc.',
      maintainer_email='opensource@dashing.tv',
      url='http://opensource.dashing.tv/dirtt',
      license='MIT',
      py_modules=['dirtt'],
      **kw
      )
