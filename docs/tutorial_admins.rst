Tutorial for build administrators
=================================

The following is a brief tutorial of the command line interface for ``karr_lab_build_utils``. Note, the command line interface provides some functionality in addition to that described below. However, in general, these additional commands should only be run from CircleCI.

Except as indicated below, ``karr_lab_build_utils`` should be run from the package's root directory, e.g. with a current working directory of ``~/Documents/my_package``.

To use the command line interface, your package should follow the organization scheme described in "An Introduction Whole-Cell Modeling":

* `Structuring Python projects <http://docs.karrlab.org/intro_to_wc_modeling/latest/concepts_skills/software_engineering/structuring_python_projects.html>`_
* `Testing Python projects <http://docs.karrlab.org/intro_to_wc_modeling/latest/concepts_skills/software_engineering/continuous_integration.html>`_
* `Documenting Python code <http://docs.karrlab.org/intro_to_wc_modeling/latest/concepts_skills/software_engineering/documenting_python.html>`_
* `Packaging Python projects <http://docs.karrlab.org/intro_to_wc_modeling/latest/concepts_skills/software_engineering/distributing_python.html>`_


Getting help
------------

Run the following commands to get help documentation about the command line utility and each individual command::

    karr_lab_build_utils --help
    karr_lab_build_utils create-repository --help

Creating a new package
----------------------

Run this command to create a new package (create local and remote repositories with the proper directory structure and files for our build system, add repository to CircleCI, add package to downstream dependencies of dependencies, etc.). The command will prompt you for all of the information needed to create a repository and instruct you how to create a new package, including linking it to CircleCI, Coveralls, Code Climate, and Read the Docs. The command should be run from the package's desired parent directory, e.g. with a current working directory of ``~/Documents``.::

    cd ~/Documents
    karr_lab_build_utils create-package

``karr_lab_build_utils`` also provides two lower-level commands for creating, cloning, and initializing Git repositories. These commands are an alternative to the ``create-package`` command which creates, clones, and initializes Git repositories and much more.

* ``create-repository``: create a new GitHub repository and clone it locally
* ``setup-repository``: set up the file structure of a local Git repository

.. code::

    cd ~/Documents
    karr_lab_build_utils create-repository
    karr_lab_build_utils setup-repository


Versioning with Git and GitHub
------------------------------

Creating a repository for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to create a new repository (including both local and GitHub versions). This should be run from the package's desired parent directory, e.g. with a current working directory of ``~/Documents``.::

    cd ~/Documents
    karr_lab_build_utils create-repository repository_name \
        --description description \
        --public


Testing with pytest, coverage, instrumental, Docker, and CircleCI
-----------------------------------------------------------------

Runing the tests for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to test the local package::

    karr_lab_build_utils run-tests

Evaluating the coverage of the tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the ``--coverage-type`` option to specify ``statement``, ``branch``, or ``multiple-condition`` coverage, e.g.::

    karr_lab_build_utils run-tests --with-coverage --coverage-type branch

Running tests with Docker or the CircleCI local executor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add the ``--environment`` option to specify ``local``, ``docker``, or ``circleci``, e.g.::

    karr_lab_build_utils run-tests --environment docker tests

Statically analyzing code with Pylint
-------------------------------------

Statically analyzing a package with Pylint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to statically analyze a package using `Pylint https://www.pylint.org/`_::

    karr_lab_build_utils analyze-package package_name

This will identify potential errors such as

* duplicate arguments
* duplicate dictionary keys
* re-imported modules, classes, functions, and variables
* unused imports, arguments, and variables
* wild card imports


Documenting code with Sphinx
----------------------------

Building the documentation for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to compile the documentation in HTML format for a package.::

    karr_lab_build_utils make-documentation

Spell checking documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the ``--spell-check`` option to spell check the documentation, e.g.::

    karr_lab_build_utils -spell-check make-documentation

The output will be saved to ``docs/_build/spelling/output.txt``.

White-listed words can be saved (1 word per line) to ``docs/spelling_wordlist.txt``.


Managing dependencies
---------------------

Installing the dependencies for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the following command to install all of the requirements for the current package in the following files:

* ``requirements.txt``,
* ``requirements.optional.txt``,
* ``tests/requirements.txt``, and
* ``docs/requirements.txt``

.. code-block:: bash

    karr_lab_build_utils install-requirements

Finding missing requirements for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to find potentially missing requirements for a package::

    karr_lab_build_utils find-missing-requirements


Finding unused requirements for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to identify potentially unused requirements for a package::

    karr_lab_build_utils find-unused-requirements

Compiling the downstream dependencies of a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Clone all of our packages
#. Run this command to compile the downstream dependencies of your package::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/Documents

#. Optionally, add the ``--downstream-dependencies-filename`` option to save the dependencies to a YAML file::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/Documents --downstream-dependencies-filename .circleci/downstream_dependencies.yml


Visualizing all of the package dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Clone all of our packages
#. Run this command to visualize the dependencies of your packages::

    karr_lab_build_utils visualize-package-dependencies --packages-parent-dir ~/Documents --out-filename ~/Documents/package-dependencies.pdf

Continuous integration with CircleCI
------------------------------------

The commands described in this section require a CircleCI API token. Visit `https://circleci.com/account/api <https://circleci.com/account/api>`_ to create a token.

Following a build for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to follow a CircleCI build for a package instead of using the CirlceCI web interface::

    karr_lab_build_utils follow-circleci-build \
        --repo-owner <repo_owner> \
        --repo-name <repo_name>


Getting the environment variables for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to get the CircleCI environment variables for a package::

    karr_lab_build_utils get-circleci-environment-variables \
        --repo-owner <repo_owner> \
        --repo-name <repo_name>


Setting a environment variable for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to set a CircleCI environment variable for a package::

    karr_lab_build_utils set-circleci-environment-variable <name> <value> \
        --repo-owner <repo_owner> \
        --repo-name <repo_name>


Deleting a environment variable for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to delete a CircleCI environment variable for a package::

    karr_lab_build_utils delete-circleci-environment-variable <name> \
        --repo-owner <repo_owner> \
        --repo-name <repo_name>


Triggering testing downstream dependencies of a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Save a list of your the downstream dependencies of the package in YAML format to ``.circleci/downstream_dependencies.yml``, e.g.::

    - wc_lang
    - wc_sim

#. Run this command to trigger CircleCI to test the downstream dependencies of your package::

    karr_lab_build_utils trigger-tests-of-downstream-dependencies


Statically analyzing code and performing coverage analysis with Code Climate
----------------------------------------------------------------------------

Creating a Code Climate build for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to create a Code Climate build for a package instead of using the Code Climate web interface::

    karr_lab_build_utils create-codeclimate-github-webhook \
        --repo-owner <repo_owner> \
        --repo-name <repo_name>

Distributing packages with PyPI
-------------------------------

Distributing a package by uploading it to PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. `Create a PyPI account <https://pypi.python.org/pypi?%3Aaction=register_form>`_
#. Save your credentials to ~/.pypirc::

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>

#. Run this command to upload your package to PyPI::

    karr_lab_build_utils upload-package-to-pypi
