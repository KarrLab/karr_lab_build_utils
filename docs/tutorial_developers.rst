Tutorial for WC modeling software developers
============================================

Configuring files not to statically analyze
-------------------------------------------
The ``static_analyses.ignore_files`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of glob patterns not to statically analyze. E.g.::
    
    static_analyses:
      ignore_files:
          - karr_lab_build_utils/templates/*


Configuring tests of downstream dependencies
--------------------------------------------

The ``downstream_dependencies`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of the names of the downstream dependencies of your package. For example, if your package is used by ``wc_lang`` and ``wc_sim``, ``.karr_lab_build_utils.yml`` should contain::

    downstream_dependencies:
      - wc_lang
      - wc_sim


Configuring build email notifications
-------------------------------------

The ``email_notifications`` key of ``/path/to/repo/.karr_lab_build_utils.yml`` should represent a list of email addresses to receive notifications of the build status of your package. E.g.::
    
    email_notifications:
      - jonrkarr@gmail.com


Configuring build passwords
---------------------------

The ``passwords.yml`` file in the ``karr_lab_passwords`` repository should contain all of the global and repository-specific passwords needed to run your tests. The file should follow this format::

    global:
      key_1: val_1
      key_2: val_2
      ...
    local:
      package_1:
        key_1: val_1
        key_2: val_
        ...
      ...
