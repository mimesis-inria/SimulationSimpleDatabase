from setuptools import setup, find_packages
from os.path import join

PROJECT = 'SSD'
PACKAGES = ['Core', 'SOFA']

packages = [f'{PROJECT}']
packages_dir = {f'{PROJECT}': 'src'}

# Configure packages list and directories
for package in find_packages(where='src'):
    packages.append(f'{PROJECT}.{package}')
for package in PACKAGES:
    packages_dir[f'{PROJECT}.{package}'] = join('src', package)

# Add examples as subpackages
examples_dir = {'Core': ['storage', 'rendering'],
                'SOFA': ['storage', 'rendering', 'rendering-offscreen']}
for package in PACKAGES:
    packages_dir[f'{PROJECT}.examples.{package}'] = join('examples', package)
    for example_dir in examples_dir[package]:
        packages.append(f'{PROJECT}.examples.{package}.{example_dir}')

# Extract README.md content
with open('README.md') as f:
    long_description = f.read()

# Installation
setup(name='SimulationSimpleDatabase',
      version='24.1',
      description='A simplified API to use SQL Databases with numerical simulation.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='R. Enjalbert, A. Odot',
      author_email='robin.enjalbert@inria.fr',
      url='https://github.com/RobinEnjalbert/SimulationSimpleDatabase',
      packages=packages,
      package_dir=packages_dir,
      package_data={f'{PROJECT}.examples.Core.rendering': ['armadillo.obj']},
      install_requires=['numpy >= 1.26.4',
                        'peewee >= 3.17.0',
                        'vedo >= 2024.5.1',
                        'matplotlib >= 3.8.3',
                        'open3d >= 0.16.0'],
      entry_points={'console_scripts': ['SSD=SSD.cli:execute_cli']})
