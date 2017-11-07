Overview
========


Package organization
-----------------------------------
To use the utilities, your package should follow this organization scheme

.. code-block:: text

    /path/to/repo/
      LICENSE
      setup.py
      setup.cfg
      MANIFEST.in  
      requirements.txt
      README.md
      <repo_name>
        __init__.py
          __version__ = '<version_number>'
        __main__.py (optional, for command line programs)
      tests/
        requirements.txt
        fixtures/
          secret/ (git-ignored fixtures that contain usernames, passwords, and tokens)
      docs/
        conf.py
        requirements.txt
        index.rst
        _static (optional for any files needed for the documentation)

Setup settings
-----------------------------------
The following options should be set in `setup.cfg`

.. code-block:: text

    [coverage:run]
    source = 
        <repo_name>

    [sphinx-apidocs]
    packages = 
        <repo_name>

Sphinx settings
-----------------------------------
Add/uncomment these lines in `docs/conf.py`

.. code-block:: text

    import os
    import sys
    sys.path.insert(0, os.path.abspath('..'))

Enable the napolean and google analytics extensions in `docs/conf.py`

.. code-block:: text

    extensions = [
        ...
        'sphinx.ext.napoleon',
        'sphinxcontrib.googleanalytics',
    ]

Set the version and release in `docs/conf.py`

.. code-block:: text

    version = <repo_name>.__version__
    release = version

Set the napolean options in `docs/conf.py`

.. code-block:: text

    napoleon_google_docstring = True
    napoleon_numpy_docstring = False
    napoleon_include_private_with_doc = False
    napoleon_include_special_with_doc = True
    napoleon_use_admonition_for_examples = False
    napoleon_use_admonition_for_notes = False
    napoleon_use_admonition_for_references = False
    napoleon_use_ivar = False
    napoleon_use_param = True
    napoleon_use_rtype = True

Configure `docs/conf.py` to use the Read the Docs theme

.. code-block:: text

    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

Set the google analytics id in `docs/conf.py`


.. code-block:: text

    googleanalytics_id = 'UA-86340737-1'

Add the following to trigger API documentation when the documenation is compiled

.. code-block:: text

    from configparser import ConfigParser
    from sphinx import apidoc

    def run_apidoc(app):
        this_dir = os.path.dirname(__file__)
        parser = ConfigParser()
        parser.read(os.path.join(this_dir, '..', 'setup.cfg'))
        packages = parser.get('sphinx-apidocs', 'packages').strip().split('\n')
        for package in packages:
            apidoc.main(argv=['sphinx-apidoc', '-f', '-o', os.path.join(this_dir, 'source'), os.path.join(this_dir, '..', package)])

    def setup(app):
        app.connect('builder-inited', run_apidoc)

Sphinx examples
-----------------------------------

Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    class MyClass(object):
        ''' Short description

        Long description

        Attributes:
          arg1 (:obj:`type`): description
          arg2 (:obj:`type`): description
          …
        '''

        ...

Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def my_method(self, arg1, arg2):
        ''' Short description

        Long description

        Args:
          arg1 (:obj:`type`): description
          arg2 (:obj:`type`, optional): description
          …

        Returns:
          :obj:`type`: description

        Raises:
          :obj:`ErrorType`: description
          …
        '''

        ...

Command line
-----------------------------------

.. code-block:: text

    export CIRCLE_PROJECT_REPONAME=karr_lab_build_utils
    export CIRCLE_BUILD_NUM=1
    export CODE_SERVER_PASSWORD=*******
    karr_lab_build_utils install-requirements
    karr_lab_build_utils run-tests --test_path /path/to/tests --with_xml_report --with_coverage
    karr_lab_build_utils make-and-archive-reports

CircleCI build configuration
-----------------------------------

.. code-block:: text
    
    machine:
      python:
        version: 2.7.11
    dependencies:
      pre:
        - pip install git+git://github.com/KarrLab/karr_lab_build_utils#egg=karr_lab_build_utils
        - karr_lab_build_utils install-requirements
    test:
      override:
        - karr_lab_build_utils run-tests --test_path tests --with_xml_report --with_coverage
      post:
        - karr_lab_build_utils make-and-archive-reports
