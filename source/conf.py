# -*- coding: utf-8 -*-
#
# invoca documentation build configuration file, created by
# sphinx-quickstart on Fri May  9 18:53:36 2014.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import os
import re
import pickle
import types
from datetime import datetime
# append the current folder to the Python class path
sys.path.append(os.getcwd())

# Invoca py files
from doc_versions import *
from org_types import *

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# -- General configuration ------------------------------------------------

# Determine if this file being executed on read the docs or locally
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

# these templates will only be used we building locally, they will be ignored by RTD
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = ['.rst']

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Invoca'
copyright = u'{}, Invoca'.format(datetime.now().year)

# The full version, including alpha/beta/rc tags.
version = COMMON_VERSION
release = COMMON_VERSION

if on_rtd:
  custom_template_path = './custom_templates/'
  source_path = './'
else:
  custom_template_path = './source/custom_templates/'
  source_path = './source/'

"""
def build_template():
Replaces directives with the contents of a custom template. Substitutes
values passed to the directive into the template.

Example directive (NOTE: there are 2 new lines at the end!):
.. api_endpoint::
  :verb: GET
  :path: /advertiser_campaigns
  :description: Get all campaigns for an Advertiser
  :page: get_advertiser_campaigns


Example template:
<div class=":verb:">:description</div>
"""
def build_template(match, template_file_name):
  lines = match.group().splitlines()

  # remove the directive line (e.g. ".. api_endpoint::" as shown above)
  lines.pop(0)

  # extract the replacement keys and values (e.g. ":verb: GET")
  template_vars = {}
  for line in lines:
    if not line.strip(): continue
    args = line.strip().split(' ')
    key = args.pop(0)
    template_vars[key] = ' '.join(args)

  # open the template and find/replace the keys with the values
  template = open('{}{}'.format(custom_template_path, template_file_name), 'r').read()
  for search, replacement in template_vars.iteritems():
    if re.search(search, template):
      template = template.replace(search, replacement)
    else:
      raise Exception("Template: [" + template + "] does not have replacement key " + search)

  # raise error if we have extra or not enough keys
  remaining_keys = re.search(r":[a-zA-Z_]+:", template)
  if not remaining_keys:
    return template
  else:
    raise Exception("Template: [" + template + "] has and  unreplaced key " + remaining_keys.group())

# Use regex to find all directives (matching structure of "Example directive" above)
# in the current file's source
def find_and_replace_templates(source, directive_name, template_file_name):
  return re.sub(
          re.compile("^ *\.\. {}::$\n(^\s+:\w+:\s+.*$\n)+^$\n".format(directive_name), re.MULTILINE),
          lambda match: build_template(match, template_file_name),
          source)

def build_api_endpoint_template(source):
  return find_and_replace_templates(source, "api_endpoint", "_api_endpoint.txt")

def build_tx_api_templates(source):
  for org_docname in ORG_TYPES_FOR_FILES:
    source = find_and_replace_templates(source, org_docname + "_tx_api_page", "_tx_api_page.txt")
  return source

# ==================
# Callback function:
# ==================
# Runs upon completion of "source-read" event. Substitutes :my_var" variables in custom templates
def source_handler(app, docname, source):
  # Build templates in custom_templates/
  source[0] = build_api_endpoint_template(source[0])
  source[0] = build_tx_api_templates(source[0])

  # Replace @@API_VERSION in templates with strings from doc_versions.py
  for symbol_string, version_string in VERSIONS.iteritems():
    source[0] = re.sub(symbol_string, version_string, source[0])


# In the case of partials which have enumerable replacements like { Network, Advertiser, Affiliate }
# three copies of the .tmp file must be made, using each respective enumerable as its replacement text
# The resulting files will look like _networks_something_page.tmp, ... _affiliates_something_page.tmp 

# Typically there will be corresponding files _something_page.rst in the API directory you're working in
# as well as a file in custom_templates/ named _something_page.txt. (See api_endpoint and tx_api_page for reference)
def build_partials_for_orgs(tmp_files):
  for tmp_file in tmp_files:
    partial = open(tmp_file, 'r').read()
    for (symbol_string, org_type_list), (symbol_string2, org_type_list2) in zip(ORG_TYPES_PLURAL.iteritems(), ORG_TYPES_SINGULAR.iteritems()):
      for org_type, org_type2, org_type_for_file, in zip(org_type_list, org_type_list2, ORG_TYPES_FOR_FILES):
        new_partial = re.sub(symbol_string, org_type, partial)
        new_partial = re.sub(symbol_string2, org_type2, new_partial)
        if partial != new_partial:
          new_file_name = os.path.join(os.path.dirname(tmp_file), "_" + org_type_for_file + os.path.basename(tmp_file))
          print "BUILDING PARTIALS FOR ORG:" + new_file_name
          open(new_file_name,'w').write(new_partial)

# Replace all occurences of @@ variables in partials (.rst files beginning w/ an underscore)
def build_partials(app, env, docnames):
  tmp_files = []
  for docname in env.found_docs:
    if re.search(r"/_[^/]+$", docname) and not re.search('custom_template', docname):
      # Replace @@API_VERSION with strings in doc_versions.py
      partial = open('{}{}{}'.format(source_path, docname, '.rst'), 'r').read()
      for symbol_string, version_string in VERSIONS.iteritems():
        partial = re.sub(symbol_string, version_string, partial)
        new_docname = docname + '.tmp'
        print "BUILDING PARTIAL: " + new_docname
        tmp_files.append('{}{}'.format(source_path, new_docname))
        open('{}{}'.format(source_path, new_docname), 'w').write(partial)

  build_partials_for_orgs(tmp_files)

INVOCA_CSS = '''<link rel="stylesheet" href="{0}css/sphinx_rtd_theme.css" type="text/css" />
                <link rel="stylesheet" href="//invoca-developer-docs.readthedocs.org/en/{1}/_static/css/custom.css" type="text/css" />
                <link rel="stylesheet" href="{0}css/readthedocs-doc-embed.css" type="text/css" />'''

def update_body(app, pagename, templatename, context, doctree):
  if app.builder.name in ['readthedocssinglehtmllocalmedia', 'readthedocs', 'readthedocsdirhtml']:
    # check if we have patched it already, if so, don't bother
    if hasattr(app.builder.templates, 'render') and \
       hasattr(app.builder.templates.render, '_patched') and \
       not hasattr(app.builder.templates.render, '_invoca_patched'):

      print('Installing monkey patch to get our CSS in the proper location')

      # Janky monkey patch of template rendering to add our content
      old_render = app.builder.templates.render

      def invoca_rtd_render(self, template, render_context):
        """
        Add our CSS after the RTD CSS
        """
        # call original render function
        content = old_render(template, render_context)

        # find our insertion point in the HTML
        end_body = content.lower().find('</head>')

        # Insert our content at the end of the head.
        if end_body != -1:
          content = \
            content[:end_body] + \
            INVOCA_CSS.format(render_context['MEDIA_URL'], render_context['current_version'].lower()) + \
            content[end_body:]
        else:
          app.debug("File doesn't look like HTML. Skipping Invoca content addition")

        return content

      # we have to set two patched flags because RTD ALSO monkey patches this method
      invoca_rtd_render._patched = True
      invoca_rtd_render._invoca_patched = True
      app.builder.templates.render = types.MethodType(invoca_rtd_render,
                                                      app.builder.templates)

# ===========================
# ENTRY POINT to build script
# ===========================
def setup(app):
  app.connect('env-before-read-docs', build_partials)
  app.connect('source-read', source_handler)
  app.connect('html-page-context', update_body)
  app.add_javascript('js/custom.js')
  app.add_javascript('https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js')

  # This CSS is added BEFORE the RTD CSS, so it doesn't allow us to override their CSS
  # We re-add our CSS AFTER the RTD CSS using the update_body method. We have left this
  # in place here so the CSS will load when you build and view locally instead of on RTD
  app.add_stylesheet('css/custom.css')

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all
# documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
#keep_warnings = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

# When building locally, the theme is not automatically imported
# When we're not on read the docs, we have to import it and set the theme manually.
if not on_rtd:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_context = {}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {"nosidebar": True, "display_version": False, "logo_only": True}

# It seems that ReadTheDocs ignores html_theme_options above,
# so here we are expanding the options directly into the context
if on_rtd:
  for key in html_theme_options:
    html_context['theme_' + key] = html_theme_options[key]

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = ''

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '_static/logo.png'

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
#html_extra_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'invocadoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
  ('index', 'invoca.tex', u'invoca Documentation',
   u'invoca', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
latex_logo = '_static/logo.png'

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'invoca', u'invoca Documentation',
     [u'invoca'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'invoca', u'invoca Documentation',
   u'invoca', 'invoca', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False

rst_prolog = """

.. title:: Invoca Developer Portal
.. raw:: html

  <link rel="stylesheet" href="https://media.readthedocs.org/css/sphinx_rtd_theme.css" type="text/css" />
  <link rel="stylesheet" href="http://developers.invoca.net/en/""" + version +  """/_static/css/custom.css" type="text/css" />
  <link rel="stylesheet" href="https://media.readthedocs.org/css/readthedocs-doc-embed.css" type="text/css" />
  <link rel="stylesheet" href="http://developers.invoca.net/en/""" + version+  """/_static/css/custom.css" type="text/css" />
  <link rel="stylesheet" href="https://media.readthedocs.org/css/readthedocs-doc-embed.css" type="text/css" />
  <style>
  .rst-pro {
    visibility: hidden
  }
  </style>
  <div style="text-align: right;" >
    <a href="http://www.invoca.net/home">Return to the Invoca Platform</a>
  </div>


"""
