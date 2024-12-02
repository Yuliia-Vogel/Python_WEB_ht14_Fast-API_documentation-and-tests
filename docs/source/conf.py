# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os


sys.path.insert(0, os.path.abspath('../..'))
print(os.path.abspath('../..'))
# sys.path.insert(0, r"D:\Yuliia\ht14_Fast API_documentation and tests\Python_WEB_ht14_Fast-API_documentation-and-tests\docs\src")

# Логування sys.path у файл
with open("sphinx_path_log.txt", "w") as log_file:
    log_file.write("sys.path:\n")
    log_file.write("\n".join(sys.path))
    log_file.write("\n")

project = 'Contacts Fast API (_)'
copyright = '2024, Yuliia Melnychenko'
author = 'Yuliia Melnychenko'
release = '1.4'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'nature'
html_static_path = ['_static']
