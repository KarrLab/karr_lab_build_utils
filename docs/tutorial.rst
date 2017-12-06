Tutorial
========

The following is a brief tutorial of the command line interface for ``karr_lab_build_utils``. Note, the command line interface provides some functionality in addition to that described below. However, in general, these additional commands should only be run from CircleCI.

Except as indicated below, the command line interface should be run from the desired parent directory of the package, e.g. ``~/Documents/my_package``.

To use the command line interface, your package should follow the organization scheme described in "An Introduction Whole-Cell Modeling":

* `Structing Python projects <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/structuring_python_projects.html>`_
* `Testing Python projects <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/continuous_integration.html>`_
* `Documenting Python code <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/documenting_python.html>`_
* `Packaging Python projects <http://intro-to-wc-modeling.readthedocs.io/en/latest/concepts_skills/software_engineering/distributing_python.html>`_

In addition, you should save a list of your the downstream dependencies of the package in YAML format to ``.circleci/downstream_dependencies.yml``, e.g.::

    - wc_lang
    - wc_sim


Getting help
------------

Run the following commands to get help documentation about the command line utility and each individual command::

    karr_lab_build_utils --help
    karr_lab_build_utils create-repository --help


Create a repository for a package
---------------------------------

Run this command to create a new repository with the proper directory sturcture and files for our build system. This should be run from the desired parent directory of the package, e.g. ``~/Documents``.::

    cd ~/Documents
    karr_lab_build_utils create-repository --dirname new_package --url https://github.com/KarrLab/new_package


Install the requirements for a package
--------------------------------------

Run the following command to install all of the requirements for the current package in the following files:

* ``requirements.txt``,
* ``requirements.optional.txt``,
* ``tests/requirements.txt``, and
* ``docs/requirements.txt``

.. code-block:: bash

    karr_lab_build_utils install-requirements


Run the tests for a package
---------------------------

Run this command to test a package::

    karr_lab_build_utils run-tests tests

Add the ``--coverage-type`` option to specify ``statement``, ``branch``, or ``multiple-condition`` coverage, e.g.::

    karr_lab_build_utils run-tests --coverage-type branch tests


Build the documentation for a package
-------------------------------------

Run this command to compile the documentation in HTML format for a package.::

    karr_lab_build_utils make-documentation

Add the ``--spell-check`` option to spell check the documenation, e.g.::

    karr_lab_build_utils -spell-check make-documentation

The output will be saved to ``docs/_build/spelling/output.txt``.

White-listed words can be saved (1 word per line) to ``docs/spelling_wordlist.txt``.


Statically analyze a package
----------------------------

Run this command to statistically analyze a package using Pylint::

    karr_lab_build_utils analyze-package

This will identify potential errors such as

* duplicate arguments
* duplicate dictionary keys
* re-imported modules, classes, functions, and variables
* unused imports, arguments, and variables
* wild card imports


Find missing requirements for a package
---------------------------------------

Run this command to find potentially missing requirements for a package::

    karr_lab_build_utils find-missing-requirements


Find unused requirements for a package
--------------------------------------

Run this command to identify potentially unused requirements for a package::

    karr_lab_build_utils find-unused-requirements


Create a CircleCI build for a package
-------------------------------------

Run this command to create a CircleCI build for a package instead of usign the CirlceCI web interface::

    karr_lab_build_utils create-circleci-build


Compile the downstream dependencies of a package
------------------------------------------------

Run this command to compile the downstream dependencies of your package::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/Documents

Optionaly, add the ``--downstream-dependencies-filename`` option to save the dependencies to a YAML file::

    karr_lab_build_utils compile-downstream-dependencies --packages-parent-dir ~/Documents --downstream-dependencies-filename .circleci/downstream_dependencies.yml


Visualize the package dependencies
----------------------------------

Run this command to visualize the dependencies of your packages::

    karr_lab_build_utils visualize-package-dependencies --packages-parent-dir ~/Documents --out-filename ~/Documents/package-dependencies.pdf


Check if the package dependencies are acyclic
---------------------------------------------

Run this command to determine if there are any cyclcic dependencies among your packages. This must be eliminated from the ``.circleci/downstream_dependencies.yml`` files because CircleCI does not support cyclic dependencies::

    karr_lab_build_utils are-package-dependencies-acyclic --packages-parent-dir ~/Documents


Trigger CircleCI to test downstream dependencies of a package
-------------------------------------------------------------

#. Save a list of your the downstream dependencies of the package in YAML format to ``.circleci/downstream_dependencies.yml``, e.g.::

    - wc_lang
    - wc_sim

#. Run this command to trigger CircleCI to test the downstream dependencies of your package::

    karr_lab_build_utils trigger-tests-of-downstream-dependencies


Create Code Climate build for a package
-----------------------------------------------------------

Run this command to create a Code Climate build for a package instead of usign the Code Climate web interface::

    karr_lab_build_utils create-codeclimate-github-webhook


Distribute a package by uploading it to PyPI
--------------------------------------------

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
