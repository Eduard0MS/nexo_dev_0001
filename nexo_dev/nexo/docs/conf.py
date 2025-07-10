# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import os
import sys
import django

# Add the Django project path to the Python path
sys.path.insert(0, os.path.abspath('..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nexus.settings')

# Setup Django
try:
    django.setup()
except Exception as e:
    print(f"Warning: Django setup failed: {e}")

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Nexo - Sistema de Gestão Organizacional'
copyright = '2025, Eduardo Moura da Silva - CGEST/SAGE/MPO'
author = 'Eduardo Moura da Silva'
release = '1.0.0'
version = '1.0.0'

# Informações da equipe
html_context = {
    'github_user': 'Eduard0MS',
    'github_repo': 'nexo_dev_0001',
    'github_version': 'main',
    'doc_path': 'nexo_dev_0001/nexo_dev/nexo/docs/',
    'equipe': 'CGEST - SAGE/MPO',
    'desenvolvedor': 'Eduardo Moura da Silva',
}

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.githubpages',
    'sphinx_copybutton',
    'myst_parser',
    'sphinx_tabs.tabs',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

language = 'pt'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']

# Theme options
html_theme_options = {
    'repository_url': 'https://github.com/Eduard0MS/nexo_dev_0001',
    'use_repository_button': True,
    'use_edit_page_button': True,
    'use_source_button': True,
    'use_issues_button': True,
    'use_download_button': True,
    'path_to_docs': 'nexo_dev_0001/nexo_dev/nexo/docs/',
    'repository_branch': 'main',
    'show_navbar_depth': 2,
    'announcement': 'Sistema de Gestão Organizacional - CGEST/SAGE/MPO',
}

html_title = 'Nexo - Documentação'
html_css_files = [
    'custom.css',
]

# -- Extension configuration -------------------------------------------------

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'special-members': '__init__',
    'private-members': False,
    'inherited-members': True,
    'exclude-members': '__weakref__',
}

autodoc_mock_imports = []
autodoc_typehints = 'description'
autodoc_preserve_defaults = True

# Napoleon configuration
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'django': ('https://docs.djangoproject.com/en/stable/', 'https://docs.djangoproject.com/en/stable/_objects/'),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}

# Todo configuration
todo_include_todos = True

# MyST configuration
myst_enable_extensions = [
    'amsmath',
    'colon_fence',
    'deflist',
    'dollarmath',
    'html_admonition',
    'html_image',
    'replacements',
    'smartquotes',
    'substitution',
    'tasklist',
]

# Copy button configuration
copybutton_prompt_text = r'>>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: '
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True
copybutton_remove_prompts = True

# Autosummary configuration
autosummary_generate = True
autosummary_mock_imports = [] 