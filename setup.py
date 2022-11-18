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

examples = {'Core': ['storage', 'rendering'],
            'SOFA': ['storage', 'rendering', 'rendering-offscreen']}
for root in roots:
    for repo in examples[root]:
        packages.append(f'{project}.examples.{root}.{repo}')
        packages_dir[f'{project}.examples.{root}.{repo}'] = join('examples', root, repo)

packages.append(f'{project}')
packages_dir[f'{project}'] = 'src'

setup(name='SimulationSimpleDatabase',
      version='22.06',
      description='A simplified API to use SQL Databases with numerical simulation.',
      author='R. Enjalbert, A. Odot',
      url='https://github.com/RobinEnjalbert/SimulationSimpleDatabase',
      packages=packages,
      package_dir=packages_dir,
      package_data={f'{project}.examples.Core.rendering': ['armadillo.obj']},
      install_requires=['numpy', 'peewee', 'vedo'],
      entry_points={'console_scripts': ['SSD=SSD.cli:execute_cli']})
