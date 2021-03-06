AsciiDoc Builder and Writer for Sphinx (asciidoc)
=================================================

Introduction
------------

Sphinx is used to build documentation from reST source files using
Docutils. While there are many Sphinx output writers, such as html,
ePub, and LaTex, there has been no conversion tool available to convert
Sphinx based reST documentation to asciidoc files. Some of the open source 
projects, such as Pandoc, do not understand most of the Sphinx directives 
and are only able to proceed the simple reST format. 

The following is my attempt to write an AsciiDoc extension
for Sphinx and Docutils that would be able to serve as a builder and
writer for Sphinx, as well as a simple reST to AsciiDoc convertor.

It primarily uses Python 3, but should be fine with 2.7.

Standalone usage
----------------

You can also use the ``./asciidoc/writer.py`` as a simple convertor of
single reST files based on **docutils** reST format. 

To convert a reST file to asciidoc:

    python writer.py file.rst

When the script finishes, it creates a new asciidoc file with the same
name and the ``.adoc`` extension.

Current status
--------------

The extension is now a beta 0.9.1 version. It understands the majority
of Docutils markup and produces a usable asciidoc format, that can be
processed with Asciidoctor. However, there are improvements needed.

Note, that the convertor includes files with ``include::`` directives,
that is it puts their content directly into the referencing file. The
convertor does not preserve individual files for included content.

The conversion may fail because of ``NotImplemented Error`` that is
caused when the convertor does not understand how to interpret a
Sphinx directive. Some of the nodes are only partially implemented. 
They do not throw out an error, but they do not know how to convert the
content either. Instead, they pass the content as plain text and wrap it
with the name of the directive, so that users know where the conversion 
fails. 

If you experience such troubles, please report this in the *issues* of this 
Github project (http://github.com/lruzicka/sphinx-asciidoc) and describe which
directive is not rendered and how do you think it should be rendered in asciidoc or
how should the html rendering from **Asciidoctor** look like.

Future improvements
--------------------

In the future, I will try to focus on:

1. implementation of formatting features of the nodes that only produce plain
   text,
2. implement the not yet implemented Sphinx and Docutils nodes, so that
   the AsciiDoc files use all possible features of the original reST and
   Sphinx format,
3. improve the visitors (conversion functions) so that the AsciiDoc
   output is always flawless and possibly error free.

Installing the **sphinx_asciidoc** package
------------------------------------------

The package is in **PyPI**. To install it:

    pip3 install sphinx_asciidoc

Now, you should be able to use it.

Using the **asciidoc** builder
------------------------------

When building the documentation from the source files, choose the
**asciidoc** builder with the ``-b`` option:

    sphinx-build -b asciidoc ./source ./build

The built documentation is placed in the ``./build/asciidoc`` directory.

Disclaimer
----------

You can already use the software, but you shall take it as not fully
developed, so there still may be problems and some features may not work
properly or at all.
