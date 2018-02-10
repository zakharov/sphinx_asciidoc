#!/bin/python
# -*- coding: utf-8 -*-

"""
   sphinx.writers.asciidoc
   ~~~~~~~~~~~~~~~~~~~~~~~

   Custom docutils writer for AsciiDoc format.

   This writer is based on the RTF writer by Benoit Allard (benoit@aeteurope.nl) and has been adapted to use with AsciiDoc.

   Author:    Lukas Ruzicka
   Contact:   lukas.ruzicka@gmail.com
   Copyright: This module has been placed in the public domain.
"""
from docutils import writers, nodes
import sys

from sphinx import addnodes
# from sphinx.deprecation import RemovedInSphinx16Warning
from sphinx.locale import admonitionlabels, _


class AsciiDocWriter(writers.Writer):
    supported = ('asciidoc',)
    output = None

    def __init__(self):
        writers.Writer.__init__(self)
        self._translator_class = AsciiDocTranslator

    def translate(self):
        visitor = self._translator_class(self.document)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


def toansi(text):
    """ Encode special characters """
    trans = {'{': r'\{',
             '}': r'\}',
             '\\': r'\\',
             '|': r'\|',
             }
    out = ''
    for char in text:
        if char in trans:
            out += trans[char]
        elif ord(char) < 127:
            out += char
        else:
            out += r"\'%x" % ord(char)
    return out


sectionEquals = {  # Stores values for different section levels
    -1: '',
    0: '= ',  # title
    1: '== ',  # section
    2: '=== ',  # subsection
    3: '==== ',  # subsubsection
}

bulletIndent = {  # Adds indentation to bullet lists
    1: '* ',  # First level
    2: '** ',  # Second level
    3: '*** ',  # Third level
    4: '**** ',  # Fourth level
    5: '***** ',  # Fifth level
}

enumIndent = {  # Adds indentation to ordered lists
    1: '. ',  # First level
    2: '.. ',  # Second level
    3: '... ',  # Third level
    4: '.... ',  # Fourth level
    5: '..... ',  # Fifth level
}

numberIndent = {}  # Holds the level of indentation


def indent(fn):
    def wrapper(self, *args, **kwargs):
        self.par_level += 1
        return fn(self, *args, **kwargs)

    return wrapper


def dedent(fn):
    def wrapper(self, *args, **kwargs):
        self.par_level -= 1
        return fn(self, *args, **kwargs)

    return wrapper


class AsciiDocTranslator(nodes.NodeVisitor):
    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.body = []
        self.section_level = 0
        self.par_level = -1

        self.lists = []  # stack of the currents bullets
        self.listLevel = len(self.lists)
        self.bullet = '*'  # next one to add to the next paragraph
        self.figures = 0  # Counts figures for reference targets
        self.inTable = False
        self.turnsInList = 0
        self.inDesc = False
        self.inList = False
        self.extLinkActive = False
        self.inAdmonition = False
        self.tabColSpecs = []

    def astext(self):
        return ''.join(self.body)

    def visit_document(self, node):
        # self.body.append('Start document')
        pass

    def depart_document(self, node):
        pass

    def visit_title(self, node):
        if isinstance(node.parent, nodes.document):
            """ doc title """
            self.body.append('\n\n%s ' % sectionEquals[0])
        elif isinstance(node.parent, nodes.section):
            level = self.section_level
            try:
                tstr = sectionEquals[level]
            except KeyError:
                tstr = '= '
            self.body.append('\n\n%s ' % tstr)
        elif isinstance(node.parent, nodes.table):
            self.body.append('\n.')  # Table title

    def depart_title(self, node):
        if isinstance(node.parent, nodes.table):
            self.body.append('\n')  # Table title
        else:
            self.body.append('\n\n')

    def visit_Text(self, node):
        ##        if self.bullet is not None:
        ##            self.body.append(self.bullet+'')
        ##            self.bullet = None
        ##        self.body.append(toansi(node.astext()))
        self.body.append(node.astext())

    def depart_Text(self, node):
        pass

    def visit_strong(self, node):  # Does the bold face
        nline = '*'
        self.body.append(nline)

    def depart_strong(self, node):
        nline = '*'
        self.body.append(nline)

    def visit_index(self, node):
        # self.body.append('((')
        pass

    def depart_index(self, node):
        # self.body.append('))')
        pass

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    @indent
    def visit_paragraph(self, node):
        if self.inDesc == True:
            nline = ''
        elif self.inTable == True or self.inList == True:
            nline = ''
        else:
            nline = '\n'
        self.body.append(nline)

    @dedent
    def depart_paragraph(self, node):
        if self.listLevel == -1:
            nline = '\n\n'
        elif self.inTable == True:
            nline = '\n\n'
        else:
            nline = '\n'
        self.body.append(nline)

    def visit_compact_paragraph(self, node):
        nline = ''
        self.body.append(nline)

    @dedent
    def depart_compact_paragraph(self, node):
        if self.listLevel == -1:
            nline = '\n\n'
        else:
            nline = '\n'
        self.body.append(nline)

    def visit_bullet_list(self, node):  # Unordered list
        self.inList = True
        self.lists.append('bulleted')
        if self.turnsInList == 0:
            self.body.append('\n')
        self.turnsInList = self.turnsInList + 1

    def depart_bullet_list(self, node):
        if self.listLevel == -1:
            self.body.append('\n\n')
        else:
            self.body.append('\n')
        self.lists.pop(-1)
        self.turnsInList = 0
        self.inList = False

    def visit_enumerated_list(self, node):  # Ordered list
        self.inList = True
        self.lists.append('numbered')
        enumeration = node['enumtype']
        self.body.append('\n[' + enumeration + ']\n')
        self.turnsInList = self.turnsInList + 1

    def depart_enumerated_list(self, node):
        self.lists.pop(-1)
        self.turnsInList = 0
        self.inList = False

    def visit_list_item(self, node):
        level = len(self.lists)
        if 'bulleted' in self.lists:
            sign = bulletIndent[level]
        elif 'numbered' in self.lists:
            sign = enumIndent[level]
        else:
            sign = '\nList indentation error!\n'
        nline = sign
        self.body.append(nline)
        self.turnsInList = self.turnsInList + 1

    def depart_list_item(self, node):
        if self.inTable == True:
            self.body.append('')
        else:
            self.body.append('\n')

    def visit_block_quote(self, node):
        pass

    def depart_block_quote(self, node):
        pass

    def visit_reference(self, node):

        # print('IDS: '+str(node.get('ids')))
        # print('REFURI: '+str(node.get('refuri')))
        # print('REFID: '+str(node.get('refid')))
        self.extLinkActive = True
        uri = node.get('refuri')
        refid = node.get('refid')
        names = node.get('names')
        self.linkType = None
        if uri:
            self.linkType = 'link'
            nline = 'link:++%s++[' % uri
            self.body.append(nline)
        elif refid:
            self.linkType = 'refx'
            nline = 'xref:%s[' % refid
            self.body.append(nline)
        else:
            pass

    def depart_reference(self, node):
        if self.linkType == 'link':
            self.body.append(']')
        elif self.linkType == 'refx':
            self.body.append(']')
        else:
            pass

    def visit_docinfo(self, node):
        nline = 'Document information: '
        self.body.append(nline)

    def depart_docinfo(self, node):
        self.body.append('\n\n')

    def visit_author(self, node):
        nline = 'Author: '
        self.body.append(nline)

    def depart_author(self, node):
        self.body.append('\n\n')

    def visit_version(self, node):
        nline = 'Document version: '
        self.body.append(nline)

    def depart_version(self, node):
        self.body.append('\n\n')

    def visit_copyright(self, node):
        nline = 'Copyright: '
        self.body.append(nline)

    def depart_copyright(self, node):
        self.body.append('\n\n')

    def visit_rubric(self, node):  # This holds a place for some listings, such as footnotes.
        self.body.append('\n')
        self.body.append('.')

    def depart_rubric(self, node):
        self.body.append('\n')

    def visit_topic(self, node):
        self.body.append('[verse]\n.')

    def depart_topic(self, node):
        self.body.append('')

    def visit_sidebar(self, node):
        self.body.append('****\n')

    def depart_sidebar(self, node):
        self.body.append('****')

    def visit_target(self, node):  # Create internal inline links.
        if self.extLinkActive == False:
            try:
                refid = node.get('ids')
                refid = refid[-1]
            except IndexError:
                refid = False
            refuri = node.get('refuri')
            refnames = node.get('names')

            if refid != False:
                if refuri:
                    if refnames == None:
                        refnames = ''
                    else:
                        refnames = refnames[0]
                    self.body.append('link:++%s++[%s]' % (refuri, refnames))
                else:
                    self.body.append('[[%s]]' % refid)
            else:
                pass
        else:
            pass
            # try:
            #    refid = node.get('refid')
            #    print refid
            #    self.body.append('[[%s]]' % refid)
            # except KeyError:
            #    pass

    def depart_target(self, node):
        # self.body.append(']')
        self.extLinkActive = False

    def visit_compound(self, node):
        self.body.append('====')

    def depart_compound(self, node):
        self.body.append('====\n')

    def visit_glossary(self, node):
        self.body.append('GLOSSARY:')

    def depart_glossary(self, node):
        self.body.append('GLOSSARY:')

    def visit_note(self, node):
        self.inAdmonition = True
        if self.inList == True:
            nline = '+\n[NOTE]\n'
        else:
            nline = '[NOTE]\n'
        mline = '====\n'
        self.body.append(nline + mline)

    def depart_note(self, node):
        if self.inList == True:
            nline = '====\n\n'
        else:
            nline = '====\n'
        self.body.append(nline)
        self.inAdmonition = False

    def visit_literal(self, node):
        nline = '`'
        self.body.append(nline)

    def depart_literal(self, node):
        self.body.append('`')

    def visit_literal_strong(self, node):
        nline = '`*'
        self.body.append(nline)

    def depart_literal_strong(self, node):
        self.body.append('*`')

    def visit_literal_block(self, node):
        level = len(self.lists)
        if self.inAdmonition == True:
            nline = '\n----\n'
        elif level > 0:
            nline = '+\n----\n'
        else:
            nline = '\n----\n'
        self.body.append(nline)

    def depart_literal_block(self, node):
        self.body.append('\n----\n')

    def visit_emphasis(self, node):
        nline = ' _'
        self.body.append(nline)

    def depart_emphasis(self, node):
        self.body.append('_')

    def visit_literal_emphasis(self, node):
        nline = ' `*'
        self.body.append(nline)

    def depart_literal_emphasis(self, node):
        self.body.append('*`')

    def visit_tip(self, node):
        self.inAdmonition = True
        if self.inList == True:
            nline = '+\n[TIP]\n'
        else:
            nline = '[TIP]\n'
        mline = '====\n'
        self.body.append(nline + mline)

    def depart_tip(self, node):
        if self.inList == True:
            nline = '====\n\n'
        else:
            nline = '====\n'
        self.body.append(nline)
        self.inAdmonition = False

    def visit_warning(self, node):
        self.inAdmonition = True
        if self.inList == True:
            nline = '+\n[WARNING]\n'
        else:
            nline = '[WARNING]\n'
        mline = '====\n'
        self.body.append(nline + mline)

    def depart_warning(self, node):
        if self.inList == True:
            nline = '====\n\n'
        else:
            nline = '====\n'
        self.body.append(nline)
        self.inAdmonition = False

    def visit_subtitle(self, node):
        self.body.append('')

    def depart_subtitle(self, node):
        self.body.append('')

    def visit_attribution(self, node):
        self.body.append('-- ')

    def depart_attribution(self, node):
        self.body.append('\n')

    def visit_important(self, node):
        self.inAdmonition = True
        if self.inList == True:
            nline = '+\n[IMPORTANT]\n'
        else:
            nline = '[IMPORTANT]\n'
        mline = '====\n'
        self.body.append(nline + mline)

    def depart_important(self, node):
        if self.inList == True:
            nline = '====\n\n'
        else:
            nline = '====\n'
        self.body.append(nline)
        self.inAdmonition = False

    def visit_caution(self, node):
        self.inAdmonition = True
        if self.inList == True:
            nline = '+\n[CAUTION]\n'
        else:
            nline = '[CAUTION]\n'
        mline = '====\n'
        self.body.append(nline + mline)

    def depart_caution(self, node):  # FIXME: change to level = len(self.lists)
        if self.inList == True:
            nline = '====\n\n'
        else:
            nline = '====\n'
        self.body.append(nline)
        self.inAdminition = False

    def visit_definition_list(self, node):
        self.body.append('\n\n')

    def depart_definition_list(self, node):
        self.body.append('\n\n')

    def visit_definition_list_item(self, node):
        self.body.append('')

    def depart_definition_list_item(self, node):
        self.body.append('\n')

    def visit_term(self, node):
        # nline = ''
        # self.body.append(nline)
        pass

    def depart_term(self, node):
        self.body.append(':: ')

    def visit_definition(self, node):
        nline = '\n'
        self.body.append(nline)

    def depart_definition(self, node):
        self.body.append('\n\n')

    def visit_image(self, node):
        try:
            alt = node['alt']
        except KeyError:
            alt = 'Image'

        uri = node['uri']
        # tag = str(node)
        # parsed = tag.split(' ')
        # for feature in parsed:
        #    if 'uri' in feature:
        #        ptag = feature.split('"')
        #        path = ptag[1]
        # for feature in parsed:
        #    if 'alt' in feature:
        #        palt = feature.split('"')
        #        alt = palt[1]
        #        break
        #    else:
        #        alt = 'Image'
        nline = 'image::' + uri + '[' + alt + ']'
        self.body.append(nline)

    def depart_image(self, node):
        self.body.append('\n\n')

    def visit_footnote_reference(self, node):
        try:
            ref = str(node.get('refid')[0])
            nline = "footnoteref:[" + ref + ","
        except KeyError:
            pass
        self.body.append(nline)

    def depart_footnote_reference(self, node):
        nline = "] "
        self.body.append(nline)

    def visit_footnote(self, node):
        # nline = "footnote:["
        # self.body.append(nline)
        pass

    def depart_footnote(self, node):
        nline = "\n"
        self.body.append(nline)

    def visit_label(self, node):
        self.body.append('[[*')

    def depart_label(self, node):
        self.body.append('*]]')

    def visit_contents(self, node):
        nline = '== '
        self.body.append(nline)

    def depart_contents(self, node):
        pass

    def visit_system_message(self, node):
        self.body.append('System message: ')

    def depart_system_message(self, node):
        # self.body.append('')
        pass

    def visit_figure(self, node):
        ids = str(node['ids'])
        count = str(self.figures)
        nline = '\n[[ids]]\n'
        mline = '.' + ids + '\n'
        self.body.append(nline + mline)

    def depart_figure(self, node):
        self.body.append('\n\n')

    def visit_caption(self, node):
        self.body.append('//.')

    def depart_caption(self, node):
        self.body.append('\n')

    def visit_table(self, node):  ## Whole table element
        self.inTable = True

    def depart_table(self, node):
        self.inTable = False

    def visit_tgroup(self, node):  ## Whole inside of the table
        cols = node['cols']
        specs = self.tabColSpecs
        col = int(round((100 / cols)))
        clist = [col, ] * cols
        if specs == []:
            specs = ['<', ] * cols
        # for i in range(cols):
        #   clist.append(str(col))
        cline = ''
        for spec in specs:
            i = specs.index(spec)
            if str(spec).lower() == 'r':
                specs[i] = '>'
            elif str(spec).lower() == 'c':
                specs[i] = '^'
            elif type(spec) != int:
                specs[i] = '<'
        for c in range(len(clist)):
            # i = clist.index(c)
            if (c + 1) < len(clist):
                cline = cline + str(specs[c]) + str(clist[c]) + ','
            else:
                cline = cline + str(specs[c]) + str(clist[c])

        specline = '[cols="' + cline + '",options="header"]\n'
        introline = "|===\nh| "
        self.body.append(specline + introline)

    def depart_tgroup(self, node):
        nline = '|===\n'
        self.body.append(nline)

    def visit_colspec(self, node):  ## Column specifics
        pass

    def depart_colspec(self, node):
        pass

    def visit_tabular_col_spec(self, node):  ## Column specifics
        specs = node.get("spec").split("|")
        del specs[-1]
        del specs[0]
        self.tabColSpecs = specs

    def depart_tabular_col_spec(self, node):
        pass

    def visit_thead(self, node):  ## Table head
        pass

    def depart_thead(self, node):
        pass

    def visit_row(self, node):  # Table row
        ##        nline = ''
        ##        self.body.append(nline)
        pass

    def depart_row(self, node):
        self.body.append('\n')

    def visit_entry(self, node):  # Table cell
        nline = ''
        self.body.append('')

    def depart_entry(self, node):
        self.body.append('a| ')

    def visit_tbody(self, node):
        pass

    def depart_tbody(self, node):
        pass

    def visit_subscript(self, node):
        self.body.append('~')

    def depart_subscript(self, node):
        self.body.append('~')

    def visit_superscript(self, node):
        self.body.append('^')

    def depart_superscript(self, node):
        self.body.append('^')

    def visit_title_reference(self, node):  # This, in rst, was rendered as typeface font only.
        self.body.append('`*')

    def depart_title_reference(self, node):
        self.body.append('*`')

    def visit_line_block(self, node):
        self.body.append('[%hardbreaks]\n')

    def depart_line_block(self, node):
        self.body.append('')

    def visit_line(self, node):
        nlink = ""
        self.body.append(nlink)

    def depart_line(self, node):
        self.body.append('\n')

    def visit_comment(self, node):
        self.body.append('\n////\n')

    def depart_comment(self, node):
        self.body.append('\n////\n\n')

    def visit_problematic(self, node):  # Occurs when the rst source files have an error in them.
        self.body.append('*Problematic*, check error messages! : ')

    def depart_problematic(self, node):
        self.body.append('')

    def visit_meta(self, node):
        name = str(node.get('name'))
        content = str(node.get('content'))
        self.body.append(':' + name + ':' + ' ' + content)

    def depart_meta(self, node):
        self.body.append('\n')

    def visit_transition(self, node):
        self.body.append("\n'''")

    def depart_transition(self, node):
        self.body.append('\n')

    def visit_manpage(self, node):
        self.body.append('_')

    def depart_manpage(self, node):
        self.body.append('_')
        pass

    def visit_raw(self, node):
        self.body.append('RAW: ')

    def depart_raw(self, node):
        self.body.append('')

    def visit_subtitle(self, node):
        self.body.append('SUBTITLE: ')

    def depart_subtitle(self, node):
        self.body.append('')

    def visit_inline(self, node):  # Leave passed
        pass

    def depart_inline(self, node):
        pass

    def visit_desc(self, node):
        self.inDesc = True
        self.body.append('\n')

    def depart_desc(self, node):
        self.inDesc = False
        self.body.append('\n')

    def visit_desc_signature(self, node):
        self.body.append('\n')

    def depart_desc_signature(self, node):
        self.body.append('\n')
        # self.body.append(':DESCSIGNATURE')

    def visit_desc_signature_line(self, node):
        self.body.append('DESCSIGLINE:')

    def depart_desc_signature_line(self, node):
        self.body.append('DESCSIGLINE')

    def visit_desc_name(self, node):
        self.body.append('**')

    def depart_desc_name(self, node):
        self.body.append('**')

    def visit_desc_addname(self, node):
        self.body.append('**')

    def depart_desc_addname(self, node):
        self.body.append('**')

    def visit_desc_type(self, node):
        self.body.append('DESCTYPE:')

    def depart_desc_type(self, node):
        self.body.append(':DESCTYPE')

    def visit_desc_returns(self, node):
        self.body.append('DESCRETURNS:')

    def depart_desc_returns(self, node):
        self.body.append(':DESCRETURNS')

    def visit_desc_parameterlist(self, node):
        self.body.append('_')

    def depart_desc_parameterlist(self, node):
        self.body.append('_')

    def visit_desc_parameter(self, node):
        self.body.append('(')

    def depart_desc_parameter(self, node):
        self.body.append(')')

    def visit_desc_optional(self, node):
        self.body.append(':DESCOPTIONAL')

    def depart_desc_optional(self, node):
        self.body.append('DESCOPTIONAL:')

    def visit_desc_annotation(self, node):
        self.body.append('_')

    def depart_desc_annotation(self, node):
        self.body.append('_ ')

    def visit_desc_content(self, node):
        self.body.append('\n')

    def depart_desc_content(self, node):
        self.body.append('\n')

    def visit_productionlist(self, node):
        #   self.new_state()
        #   names = []
        #  for production in node:
        #      names.append(production['tokenname'])
        #  maxlen = max(len(name) for name in names)
        #  lastname = None
        #  for production in node:
        #      if production['tokenname']:
        #          self.add_text(production['tokenname'].ljust(maxlen) + ' ::=')
        #          lastname = production['tokenname']
        #      elif lastname is not None:
        #          self.add_text('%s    ' % (' ' * len(lastname)))
        #      self.add_text(production.astext() + self.nl)
        #  self.end_state(wrap=False)
        #  raise nodes.SkipNode
        self.body.append('PRODUCTIONLIST:')

    def depart_production_list(self, node):
        self.body.append(':PRODUCTIONLIST')

    def visit_option_list(self, node):
        pass

    def depart_option_list(self, node):
        self.body.append('\n')

    def visit_option_list_item(self, node):
        pass

    def depart_option_list_item(self, node):
        pass

    def visit_option_group(self, node):
        self.body.append('')

    def depart_option_group(self, node):
        self.body.append('')

    def visit_option(self, node):
        pass

    def depart_option(self, node):
        pass

    def visit_option_string(self, node):
        self.body.append('')

    def depart_option_string(self, node):
        self.body.append(' ')

    def visit_option_argument(self, node):
        self.body.append('')

    def depart_option_argument(self, node):
        self.body.append(' ')

    def visit_legend(self, node):
        self.body.append('LEGEND:')

    def depart_legend(self, node):
        self.body.append(':LEGEND')

    def visit_description(self, node):
        self.body.append(':: ')

    def depart_description(self, node):
        self.body.append('\n')

    def visit_field_list(self, node):
        self.body.append('\n|===\n')

    def depart_field_list(self, node):
        self.body.append('|===\n')

    def visit_field(self, node):
        self.body.append('')

    def depart_field(self, node):
        self.body.append('\n')

    def visit_field_name(self, node):
        self.body.append('| ')

    def depart_field_name(self, node):
        self.body.append('')

    def visit_field_body(self, node):
        self.body.append('| ')

    def depart_field_body(self, node):
        self.body.append('\n')

    def visit_centered(self, node):
        self.body.append('CENTER:')

    def depart_centered(self, node):
        self.body.append(':CENTER')

    def visit_hlist(self, node):
        self.body.append('')

    def depart_hlist(self, node):
        self.body.append('')

    def visit_hlistcol(self, node):
        self.body.append('')

    def depart_hlistcol(self, node):
        self.body.append('')

    def visit_versionmodified(self, node):
        self.body.append('')

    def depart_versionmodified(self, node):
        self.body.append('')

    def visit_date(self, node):
        self.body.append('Date:')

    def depart_date(self, node):
        self.body.append(':Date')

    def visit_revision(self, node):
        self.body.append('Revision:')

    def depart_revision(self, node):
        self.body.append(':Revision')

    def visit_doctest_block(self, node):
        self.body.append('[source, python]\n')

    def depart_doctest_block(self, node):
        self.body.append('\n')

    def visit_classifier(self, node):
        self.body.append('Classifier:')

    def depart_classifier(self, node):
        self.body.append(':Classifier')

    def visit_citation(self, node):
        self.body.append('')

    def depart_citation(self, node):
        self.body.append('')

    def visit_citation_reference(self, node):
        self.body.append('CitationRFR:')

    def depart_citation_reference(self, node):
        self.body.append(':CitationRFR')

    def visit_substitution_definition(self, node):
        name = node.get('names')[0]
        self.body.append('\n:' + name + ': ')

    def depart_substitution_definition(self, node):
        self.body.append('\n')

    def visit_abbreviation(self, node):
        pass  # FIXME: We lose explanation this way

    def depart_abbreviation(self, node):
        pass  # FIXME: We lose explanation this way

    def visit_seealso(self, node):
        self.body.append('See also: ')

    def depart_seealso(self, node):
        pass

    def visit_todo_node(self, node):
        self.body.append('To do: ')

    def depart_todo_node(self, node):
        pass

    def visit_download_reference(self, node):
        self.body.append('Download reference: ')

    def depart_download_reference(self, node):
        pass

    def visit_graphviz(self, node):
        self.body.append('Graphviz: ')

    def depart_graphviz(self, node):
        pass

    def visit_container(self, node):
        self.body.append('[stem]\n')
        self.body.append('++++')

    def depart_container(self, node):
        self.body.append('++++')


if __name__ == "__main__":
    """ To test the writer """
    from docutils.core import publish_string

    filename = sys.argv[-1]
    print('Converting: ' + filename)
    f_in = open(filename, 'rb')
    rtf = publish_string(f_in.read(), writer=AsciiDocWriter())
    f_in.close()

    filename = filename + '.adoc'

    f_out = open(filename, 'wb')
    f_out.write(rtf)
    print('Converted file: ' + filename)
    f_out.close()