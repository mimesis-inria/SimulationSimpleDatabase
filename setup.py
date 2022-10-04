from setuptools import setup, find_packages
from os.path import join

packages = []
packages_dir = {}

include_SOFA = True
try:
    import Sofa
except ImportError:
    include_SOFA = False

project = 'SSD'
roots = ['Core', 'SOFA'] if include_SOFA else ['Core']
root_packages = ['storage', 'rendering']

for root in roots:
    packages.append(f'{project}.{root}')
    packages_dir[f'{project}.{root}'] = join('src', root)
    for package in find_packages(where=join('src', root)):
        packages.append(f'{project}.{root}.{package}')
        packages_dir[f'{project}.{root}.{package}'] = join('src', root, package)

setup(name='SimulationSimpleDatabase',
      version='22.06',
      description='A simplified API to use SQL Databases with numerical simulation.',
      author='R. Enjalbert, A. Odot',
      url='https://github.com/RobinEnjalbert/SimulationSimpleDatabase',
      packages=packages,
      package_dir=packages_dir,
      install_requires=['numpy', 'peewee', 'vedo'])
