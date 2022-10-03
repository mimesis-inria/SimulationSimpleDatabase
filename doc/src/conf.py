# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

from os.path import abspath, join, pardir
import sys

# Modules imports
for parent in ['Core', 'SOFA']:
    for child in ['Storage', 'Rendering']:
        path = abspath(join(abspath(__file__), pardir, pardir, pardir, 'src', parent, child))
        sys.path.append(path)

# -- Project information -----------------------------------------------------

project = 'SimulationSimpleDatabase'
copyright = '2022, Mimesis, Inria'
author = 'Robin ENJALBERT, Alban ODOT'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.duration',
              'sphinx.ext.autodoc',
              'sphinx.ext.intersphinx',
              'sphinx.ext.autosummary',
              'sphinx.ext.viewcode',
              'sphinx.ext.extlinks',
              ]

intersphinx_mapping = {'python': ('https://docs.python.org/3/', None),
                       'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
                       }

# Add any paths that contain templates here, relative to this directory.
# templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_options = {'collapse_navigation': False}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_css_files = ['theme.css']
master_doc = "index"

extlinks = {'Peewee': ('https://docs.peewee-orm.com/en/latest/', None),
            'DeepPhysX': ('https://deepphysx.readthedocs.io/en/latest/', None),
            'SOFA': ('https://www.sofa-framework.org/%s', None),
            'SP3': ('https://sofapython3.readthedocs.io/en/latest/', None),
            'SP3I': ('https://sofapython3.readthedocs.io/en/latest/menu/Compilation.html', None),
            'Numpy': ('https://numpy.org/', None),
            'PyPi': ('https://pypi.org/project/SimulationSimpleDatabase', None),
            'Vedo': ('https://vedo.embl.es/', None),
            'VedoObject': ('https://vedo.embl.es/autodocs/content/vedo/%s', '%s')
            }
