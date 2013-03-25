# $Id$ -*- coding: utf-8 -*-
##
##  This file is part of pyFormex 0.9.0  (Mon Mar 25 13:52:29 CET 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##  Distributed under the GNU General Public License version 3 or later.
##
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##
# pyFormex documentation build configuration file, created by
# sphinx-quickstart on Fri Aug 21 15:05:14 2009.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0,os.path.abspath('../pyformex/examples'))
#sys.path.insert(0,os.path.abspath('../pyformex/lib'))
sys.path.insert(0,os.path.abspath('../pyformex/gui'))
sys.path.insert(0,os.path.abspath('../pyformex/plugins'))
sys.path.insert(0,os.path.abspath('../pyformex'))
sys.path.insert(0,os.path.abspath('..'))
#sys.path.insert(0,os.path.abspath('.'))  # for our patched numpydoc
print sys.path

from sphinx.directives.other import *
#TocTree.option_spec['numberedfrom'] = int
#print TocTree.option_spec


class MyTocTree(Directive):
    """
    Directive to notify Sphinx about the hierarchical structure of the docs,
    and to include a table-of-contents like tree in the current document.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'maxdepth': int,
        'glob': directives.flag,
        'hidden': directives.flag,
        'numbered': int_or_nothing,
        'numberedfrom': int,
        'titlesonly': directives.flag,
    }

    def run(self):
        env = self.state.document.settings.env
        suffix = env.config.source_suffix
        glob = 'glob' in self.options

        ret = []
        # (title, ref) pairs, where ref may be a document, or an external link,
        # and title may be None if the document's title is to be used
        entries = []
        includefiles = []
        all_docnames = env.found_docs.copy()
        # don't add the currently visited file in catch-all patterns
        all_docnames.remove(env.docname)
        for entry in self.content:
            if not entry:
                continue
            if not glob:
                # look for explicit titles ("Some Title <document>")
                m = explicit_title_re.match(entry)
                if m:
                    ref = m.group(2)
                    title = m.group(1)
                    docname = ref
                else:
                    ref = docname = entry
                    title = None
                # remove suffixes (backwards compatibility)
                if docname.endswith(suffix):
                    docname = docname[:-len(suffix)]
                # absolutize filenames
                docname = docname_join(env.docname, docname)
                if url_re.match(ref) or ref == 'self':
                    entries.append((title, ref))
                elif docname not in env.found_docs:
                    ret.append(self.state.document.reporter.warning(
                        'toctree contains reference to nonexisting '
                        'document %r' % docname, line=self.lineno))
                    env.note_reread()
                else:
                    entries.append((title, docname))
                    includefiles.append(docname)
            else:
                patname = docname_join(env.docname, entry)
                docnames = sorted(patfilter(all_docnames, patname))
                for docname in docnames:
                    all_docnames.remove(docname) # don't include it again
                    entries.append((None, docname))
                    includefiles.append(docname)
                if not docnames:
                    ret.append(self.state.document.reporter.warning(
                        'toctree glob pattern %r didn\'t match any documents'
                        % entry, line=self.lineno))
        subnode = addnodes.toctree()
        subnode['parent'] = env.docname
        # entries contains all entries (self references, external links etc.)
        subnode['entries'] = entries
        # includefiles only entries that are documents
        subnode['includefiles'] = includefiles
        subnode['maxdepth'] = self.options.get('maxdepth', -1)
        subnode['glob'] = glob
        subnode['hidden'] = 'hidden' in self.options
        subnode['numbered'] = self.options.get('numbered', 0)
        subnode['numberedfrom'] = self.options.get('numberedfrom', 0)
        print("DOCNAME %s" % docname)
        print("NUMBEREDFROM = %s" % subnode['numberedfrom'])
        subnode['titlesonly'] = 'titlesonly' in self.options
        set_source_info(self, subnode)
        wrappernode = nodes.compound(classes=['toctree-wrapper'])
        wrappernode.append(subnode)
        ret.append(wrappernode)
        return ret

directives.register_directive('mytoctree', MyTocTree)


def assign_section_numbers(self):
    """Assign a section number to each heading under a numbered toctree."""
    # a list of all docnames whose section numbers changed
    rewrite_needed = []

    old_secnumbers = self.toc_secnumbers
    self.toc_secnumbers = {}

    def _walk_toc(node, secnums, depth, titlenode=None):
        # titlenode is the title of the document, it will get assigned a
        # secnumber too, so that it shows up in next/prev/parent rellinks
        for subnode in node.children:
            if isinstance(subnode, nodes.bullet_list):
                numstack.append(0)
                _walk_toc(subnode, secnums, depth-1, titlenode)
                numstack.pop()
                titlenode = None
            elif isinstance(subnode, nodes.list_item):
                _walk_toc(subnode, secnums, depth, titlenode)
                titlenode = None
            elif isinstance(subnode, addnodes.only):
                # at this stage we don't know yet which sections are going
                # to be included; just include all of them, even if it leads
                # to gaps in the numbering
                _walk_toc(subnode, secnums, depth, titlenode)
                titlenode = None
            elif isinstance(subnode, addnodes.compact_paragraph):
                numstack[-1] += 1
                if depth > 0:
                    number = tuple(numstack)
                else:
                    number = None
                secnums[subnode[0]['anchorname']] = \
                    subnode[0]['secnumber'] = number
                if titlenode:
                    titlenode['secnumber'] = number
                    titlenode = None
            elif isinstance(subnode, addnodes.toctree):
                _walk_toctree(subnode, depth)

    def _walk_toctree(toctreenode, depth):
        if depth == 0:
            return
        for (title, ref) in toctreenode['entries']:
            if url_re.match(ref) or ref == 'self':
                # don't mess with those
                continue
            if ref in self.tocs:
                secnums = self.toc_secnumbers[ref] = {}
                _walk_toc(self.tocs[ref], secnums, depth,
                          self.titles.get(ref))
                if secnums != old_secnumbers.get(ref):
                    rewrite_needed.append(ref)

    for docname in self.numbered_toctrees:
        doctree = self.get_doctree(docname)

        # Autonumber
        if docname == "refman":
            numberedfrom = 0
            for node in doctree.traverse():
                #print node.tagname
                #if node.tagname == 'title':
                #    print node
                if node.tagname == 'toctree':
                    att = node.attributes
                    #print att.keys()
                    if att.get('numberedfrom',0) < 0:
                        att['numberedfrom'] = numberedfrom
                    nentries = len(att['entries'])
                    #print numberedfrom,nentries
                    numberedfrom += nentries
                    #print att

        for toctreenode in doctree.traverse(addnodes.toctree):
            depth = toctreenode.get('numbered', 0)
            fromn = toctreenode.get('numberedfrom', 0)
            #print("DEPTH %s, FROM %s" % (depth,fromn))
            if depth:
                # every numbered toctree gets new numbering
                numstack = [fromn]
                _walk_toctree(toctreenode, depth)

    return rewrite_needed

from sphinx.environment import BuildEnvironment
BuildEnvironment.assign_section_numbers = assign_section_numbers

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.1'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc','sphinx.ext.pngmath', 'sphinx.ext.autosummary',] #  'sphinx.ext.viewcode'] #'sphinx.ext.jsmath',

#render_class_autosummary = False

# Add both class and __init__ docstrings
autoclass_content = 'class'  # 'class', 'init' or 'both'

autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'pyFormex'
copyright = u'2004-2012, Benedict Verhegghe'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.9.0'
# The full version, including alpha/beta/rc tags.
release = '0.9.0r1'

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
exclude_patterns = ['_build', 'HOWTO.rst']

# The reST default role (used for this markup: `text`) to use for all documents.
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


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'pyformex'
html_theme_options = {
    "rightsidebar": "true",
#    "relbarbgcolor": "black",
#    "sidebarbgcolor": "silver",
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ['.']

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = 'Documentation'

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = 'images/pyformex_logo_filled.png' # 'images/scallop_dome_small.png'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = 'favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

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
html_copy_source = False
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'pyFormexdoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
latex_paper_size = 'a4'

# The font size ('10pt', '11pt' or '12pt').
latex_font_size = '11pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'pyformex.tex', u'pyFormex Documentation',
   u'Benedict Verhegghe', 'manual', True),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
latex_logo = 'images/pyformex_logo_with_dome.png'

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = True

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


def list_toctree(app, doctree, docname):
    """Change the numbering of the  multiple toctrees in a document"""
    if docname == "refman":
        print app.env.toc_num_entries
        print app.env.toc_secnumbers
        numberedfrom = 0
        for node in doctree.traverse():
            #print node.tagname
            if node.tagname == 'title':
                print node
            if node.tagname == 'toctree':
                att = node.attributes
                print att.keys()
                if att.get('numberedfrom',0) < 0:
                    att['numberedfrom'] = numberedfrom
                nentries = len(att['entries'])
                print numberedfrom,nentries
                numberedfrom += nentries
                print att


def setup(app):
    from sphinx.ext.autodoc import cut_lines
    app.connect("doctree-resolved", list_toctree)
    app.connect('autodoc-process-docstring', cut_lines(2, what=['module']))
##     app.connect('autodoc-skip-member', autodoc_skip_member1)


## def autodoc_skip_member1(app,what,name,obj,skip,options):
##     #from sphinx.ext.autodoc import autodoc_skip_member
##     print obj
##     print skip
##     if obj.__doc__ is not None:
##         skip |= obj.__doc__[0] == '_'
##     return skip


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'sometext', u'sometext Documentation',
     [u'we'], 1)
]


# End
