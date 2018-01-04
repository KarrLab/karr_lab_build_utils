Tutorial
========

The following is a brief tutorial of the command line interface for ``karr_lab_build_utils``. Note, the command line interface provides some functionality in addition to that described below. However, in general, these additional commands should only be run from CircleCI.

Except as indicated below, ``karr_lab_build_utils`` should be run from the package's root directory, e.g. with a current working directory of ``~/Documents/my_package``.

To use the command line interface, your package should follow the organization scheme described in "An Introduction Whole-Cell Modeling":

* `Structuring Python projects <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/structuring_python_projects.html>`_
* `Testing Python projects <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/continuous_integration.html>`_
* `Documenting Python code <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/documenting_python.html>`_
* `Packaging Python projects <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/distributing_python.html>`_

In addition, save a list of your package's downstream dependencies in YAML format in ``.circleci/downstream_dependencies.yml``. For example, if your package is used by ``wc_lang`` and ``wc_sim``, it should contain::

    - wc_lang
    - wc_sim


Getting help
------------

Run the following commands to get help documentation about the command line utility and each individual command::

    karr_lab_build_utils --help
    karr_lab_build_utils create-repository --help


Versioning with Git and GitHub
------------------------------

Create a repository for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to create a new repository with the proper directory structure and files for our build system. This should be run from the package's desired parent directory, e.g. with a current working directory of ``~/Documents``.::

    cd ~/Documents
    karr_lab_build_utils create-repository --dirname new_package --url https://github.com/KarrLab/new_package


Testing with pytest, coverage, instrumental, Docker, and CircleCI
-----------------------------------------------------------------

Run the tests for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to test a package::

    karr_lab_build_utils run-tests tests

Evaluating the coverage of the tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the ``--coverage-type`` option to specify ``statement``, ``branch``, or ``multiple-condition`` coverage, e.g.::

    karr_lab_build_utils run-tests --with-coverage --coverage-type branch tests

Running tests with Docker or the CircleCI local executor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Add the ``--environment`` option to specify ``local``, ``docker``, or ``circleci``, e.g.::

    karr_lab_build_utils run-tests --environment docker tests

Static code analysis with Pylint
--------------------------------

Statically analyze a package with Pylint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to statistically analyze a package using Pylint::

    karr_lab_build_utils analyze-package

This will identify potential errors such as

* duplicate arguments
* duplicate dictionary keys
* re-imported modules, classes, functions, and variables
* unused imports, arguments, and variables
* wild card imports


Documentation with Sphinx
-------------------------

Build the documentation for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to compile the documentation in HTML format for a package.::

    karr_lab_build_utils make-documentation

Spell checking documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the ``--spell-check`` option to spell check the documentation, e.g.::

    karr_lab_build_utils -spell-check make-documentation

The output will be saved to ``docs/_build/spelling/output.txt``.

White-listed words can be saved (1 word per line) to ``docs/spelling_wordlist.txt``.


Dependency management
---------------------

Install the dependencies for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the following command to install all of the requirements for the current package in the following files:

* ``requirements.txt``,
* ``requirements.optional.txt``,
* ``tests/requirements.txt``, and
* ``docs/requirements.txt``

.. code-block:: bash

    karr_lab_build_utils install-requirements

Find missing requirements for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to find potentially missing requirements for a package::

    karr_lab_build_utils find-missing-requirements


Find unused requirements for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to identify potentially unused requirements for a package::

    karr_lab_build_utils find-unused-requirements

Compile the downstream dependencies of a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Clone all of our packages
#. Run this command to compile the downstream dependencies of your package::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/Documents

#. Optionally, add the ``--downstream-dependencies-filename`` option to save the dependencies to a YAML file::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/Documents --downstream-dependencies-filename .circleci/downstream_dependencies.yml


Visualize all of the package dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Clone all of our packages
#. Run this command to visualize the dependencies of your packages::

    karr_lab_build_utils visualize-package-dependencies --packages-parent-dir ~/Documents --out-filename ~/Documents/package-dependencies.pdf

Continuous integration with CircleCI
------------------------------------

The commands described in this section require a CircleCI API token. Visit `https://circleci.com/account/api <https://circleci.com/account/api>`_ to create a token.

Create a build for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to create a CircleCI build for a package instead of using the CirlceCI web interface::

    karr_lab_build_utils create-circleci-build \
        --repo-owner <repo_owner> \
        --repo-name <repo_name> \
        --circleci-api-token <token>


Get the environment variables for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to get the CircleCI environment variables for a package::

    karr_lab_build_utils get-circleci-environment-variables \
        --repo-owner <repo_owner> \
        --repo-name <repo_name> \
        --circleci-api-token <token>


Set a environment variable for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to set a CircleCI environment variable for a package::

    karr_lab_build_utils set-circleci-environment-variable <name> <value> \
        --repo-owner <repo_owner> \
        --repo-name <repo_name> \
        --circleci-api-token <token>


Delete a environment variable for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to delete a CircleCI environment variable for a package::

    karr_lab_build_utils delete-circleci-environment-variable <name> \
        --repo-owner <repo_owner> \
        --repo-name <repo_name> \
        --circleci-api-token <token>


Trigger testing downstream dependencies of a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Save a list of your the downstream dependencies of the package in YAML format to ``.circleci/downstream_dependencies.yml``, e.g.::

    - wc_lang
    - wc_sim

#. Run this command to trigger CircleCI to test the downstream dependencies of your package::

    karr_lab_build_utils trigger-tests-of-downstream-dependencies


Static analysis and coverage analysis with Code Climate
-------------------------------------------------------

Create Code Climate build for a package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run this command to create a Code Climate build for a package instead of using the Code Climate web interface::

    karr_lab_build_utils create-codeclimate-github-webhook \
        --repo-owner <repo_owner> \
        --repo-name <repo_name> \
        --github-username <username> \
        --github-password <password>

Distribution with PyPI
----------------------

Distribute a package by uploading it to PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
