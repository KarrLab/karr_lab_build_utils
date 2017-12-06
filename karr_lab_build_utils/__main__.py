from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController, expose
from karr_lab_build_utils.core import BuildHelper
import karr_lab_build_utils
import os
import sys


class BaseController(CementBaseController):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = "Karr Lab build utilities"

    @expose(help='Archive test report')
    def archive_test_report(self):
        """ Upload test report to history server """
        buildHelper = BuildHelper()
        buildHelper.archive_test_report()

    @expose(help='Install requirements')
    def install_requirements(self):
        """ Install requirements """
        buildHelper = BuildHelper()
        buildHelper.install_requirements()

    @expose(help='Get version')
    def get_version(self):
        """ Get version """
        buildHelper = BuildHelper()
        print(buildHelper.get_version())


class CreateRepositoryController(CementBaseController):
    """ Create a Git repository with the default directory structure """

    class Meta:
        label = 'create-repository'
        description = 'Create a Git repository with the default directory structure'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                default='.', type=str, help='Desired name for the Git repository')),
            (['--url'], dict(
                default=None, type=str, help='URL for the Git repository')),
            (['--build-image-version'], dict(
                default=None, type=str, help='Build image version')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_repository(dirname=args.dirname, url=args.url, build_image_version=args.build_image_version)


class SetupRepositoryController(CementBaseController):
    """ Setup a Git repository with the default directory structure """

    class Meta:
        label = 'setup-repository'
        description = 'Setup a Git repository with the default directory structure'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                default='.', type=str, help='Desired name for the Git repository')),
            (['--build-image-version'], dict(
                default=None, type=str, help='Build image version')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.setup_repository(dirname=args.dirname, build_image_version=args.build_image_version)


class CreateDocumentationTemplateController(CementBaseController):
    """ Create a Sphinx documentation template for a package """

    class Meta:
        label = 'create-documentation-template'
        description = 'Create a Sphinx documentation template for a package'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                default='.', type=str, help='Path to the package')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_documentation_template(dirname=args.dirname)


class RunTestsController(CementBaseController):
    """ Controller for run_tests.

    Run unit tests located at `test-path`.
    Optionally, generate a coverage report.
    Optionally, save the results to an XML file.
    """

    class Meta:
        label = 'run-tests'
        description = 'Run unit tests located at `test_path`'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['test_path'], dict(
                type=str, default='tests', help='path to tests to run')),
            (['--dirname'], dict(
                type=str, default='.', help='path to package to test')),
            (['--with-xunit'], dict(
                default=False, action='store_true', help='True/False to save test results to XML file')),
            (['--with-coverage'], dict(
                default=False, action='store_true', help='True/False to assess code coverage')),
            (['--coverage-dirname'], dict(
                type=str, default='.', help='Directory to store coverage data')),
            (['--coverage-type'], dict(
                type=str, default='statement',
                help='Type of coverage analysis to run {statemment, branch, or multiple-decision}')),
            (['--environment'], dict(
                type=str, default='local',
                help='Environment to run tests (local, docker, or circleci)')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        coverage_type = karr_lab_build_utils.core.CoverageType[args.coverage_type.lower().replace('-', '_')]
        buildHelper.run_tests(dirname=args.dirname, test_path=args.test_path, with_xunit=args.with_xunit,
                              with_coverage=args.with_coverage, coverage_dirname=args.coverage_dirname,
                              coverage_type=coverage_type, environment=karr_lab_build_utils.core.Environment[args.environment])


class CreateCircleciBuildController(CementBaseController):
    """ Create a CircleCI build for a repository """
    class Meta:
        label = 'create-circleci-build'
        description = 'Create a CircleCI build for a repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
            (['--circleci-api-token'], dict(
                type=str, default=None, help='CircleCI API token')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_circleci_build(
            repo_type=args.repo_type, repo_owner=args.repo_owner,
            repo_name=args.repo_name, circleci_api_token=args.circleci_api_token)


class GetCircleciEnvironmentVariablesController(CementBaseController):
    """ Get the CircleCI environment variables for a repository and their partial values"""
    class Meta:
        label = 'get-circleci-environment-variables'
        description = 'Get the CircleCI environment variables for a repository and their partial values'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
            (['--circleci-api-token'], dict(
                type=str, default=None, help='CircleCI API token')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        vars = buildHelper.get_circleci_environment_variables(
            repo_type=args.repo_type, repo_owner=args.repo_owner,
            repo_name=args.repo_name, circleci_api_token=args.circleci_api_token)
        for key, val in vars.items():
            print('{}={}'.format(key, val))


class SetCircleciEnvironmentVariableController(CementBaseController):
    """ Set a CircleCI environment variable for a repository """
    class Meta:
        label = 'set-circleci-environment-variable'
        description = 'Set a CircleCI environment variable for a repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['name'], dict(
                type=str, help='Name of the environment variable.')),
            (['value'], dict(
                type=str, help='Value of the environment variable.')),
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
            (['--circleci-api-token'], dict(
                type=str, default=None, help='CircleCI API token')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.set_circleci_environment_variables(
            {args.name: args.value},
            repo_type=args.repo_type, repo_owner=args.repo_owner,
            repo_name=args.repo_name, circleci_api_token=args.circleci_api_token)


class DeleteCircleciEnvironmentVariableController(CementBaseController):
    """ Delete a CircleCI environment variable for a repository """
    class Meta:
        label = 'delete-circleci-environment-variable'
        description = 'Delete a CircleCI environment variable for a repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['name'], dict(
                type=str, help='Name of the environment variable.')),
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
            (['--circleci-api-token'], dict(
                type=str, default=None, help='CircleCI API token')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.delete_circleci_environment_variable(args.name,
                                                         repo_type=args.repo_type, repo_owner=args.repo_owner,
                                                         repo_name=args.repo_name, circleci_api_token=args.circleci_api_token)


class CreateCodeclimateGithubWebhookController(CementBaseController):
    """ Create CodeClimate GitHub webook for the current repository """
    class Meta:
        label = 'create-codeclimate-github-webhook'
        description = 'Create CodeClimate GitHub webook for the current repository'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--repo-type'], dict(
                type=str, default=None, help='Repository type (e.g., github)')),
            (['--repo-owner'], dict(
                type=str, default=None, help='Repository owner')),
            (['--repo-name'], dict(
                type=str, default=None, help='Name of the repository to build. This defaults to the name of the current repository.')),
            (['--github-username'], dict(
                type=str, default=None, help='GitHub username')),
            (['--github-password'], dict(
                type=str, default=None, help='GitHub password')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.create_codeclimate_github_webhook(
            repo_type=args.repo_type, repo_owner=args.repo_owner, repo_name=args.repo_name,
            github_username=args.github_username, github_password=args.github_password)


class MakeAndArchiveReportsController(CementBaseController):
    """ Make and archive reports:

    * Generate HTML test history reports
    * Generate HTML API documentation
    * Archive coverage report to Coveralls and Code Climate
    """

    class Meta:
        label = 'make-and-archive-reports'
        description = 'Make and archive reports'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                default='.', type=str, help='Directory to save coverage reports')),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If true, do not send results to Coveralls and Code Climate')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.make_and_archive_reports(coverage_dirname=args.coverage_dirname, dry_run=args.dry_run)


class CombineCoverageReportsController(CementBaseController):
    """ Combine coverage reports """

    class Meta:
        label = 'combine-coverage-reports'
        description = 'Combine coverage reports (.coverage.*) into a single file (.coverage)'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                default='.', type=str, help='Directory to save coverage reports')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.combine_coverage_reports(coverage_dirname=args.coverage_dirname)


class ArchiveCoverageReportController(CementBaseController):
    """ Archive a coverage report:

    * Upload report to Coveralls and Code Climate
    """

    class Meta:
        label = 'archive-coverage-report'
        description = 'Archive coverage report'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                default='.', type=str, help='Directory to save coverage reports')),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If true, do not send results to Coveralls and Code Climate')),
        ]

    @expose(hide=True)
    def default(self):
        """ Archive a coverage report:

        * Upload report to Coveralls and Code Climate
        """
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.archive_coverage_report(coverage_dirname=args.coverage_dirname, dry_run=args.dry_run)


class UploadCoverageReportToCoverallsController(CementBaseController):
    """ Upload coverage report to Code Climate """

    class Meta:
        label = 'upload-coverage-report-to-coveralls'
        description = 'Upload coverage report to Coveralls'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                default='.', type=str, help='Directory to save coverage reports')),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If true, do not send results to Coveralls')),
        ]

    @expose(hide=True)
    def default(self):
        """ Upload coverage report to Coveralls """
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_coveralls(coverage_dirname=args.coverage_dirname, dry_run=args.dry_run)


class UploadCoverageReportToCodeClimateController(CementBaseController):
    """ Upload coverage report to Code Climate """

    class Meta:
        label = 'upload-coverage-report-to-code-climate'
        description = 'Upload coverage report to Code Climate'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--coverage-dirname'], dict(
                default='.', type=str, help='Directory to save coverage reports')),
            (['--dry-run'], dict(
                default=False, dest='dry_run', action='store_true', help='If true, do not send results to Code Climate')),
        ]

    @expose(hide=True)
    def default(self):
        """ Upload coverage report to Code Climate """
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.upload_coverage_report_to_code_climate(coverage_dirname=args.coverage_dirname, dry_run=args.dry_run)


class MakeDocumentationController(CementBaseController):
    """ Controller for make_documentation.

    Make HTML documentation. Optionally, spell check documentation.
    """

    class Meta:
        label = 'make-documentation'
        description = 'Make HTML documentation. Optionally, spell check documentation.'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--spell-check'], dict(
                default=False, dest='spell_check', action='store_true', help='If set, spell check documentation')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.make_documentation(spell_check=args.spell_check)


class CompileDownstreamDependenciesController(CementBaseController):
    """ Compile the downstream dependencies of a package by analyzing the requirements files of other packages """

    class Meta:
        label = 'compile-downstream-dependencies'
        description = 'Compile the downstream dependencies of a package by analyzing the requirements files of other packages'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                type=str, default='.', help='Path to package')),
            (['--packages-parent-dir'], dict(
                type=str, default='..', help='Path to the parent directory of the other packages')),
            (['--downstream-dependencies-filename'], dict(
                type=str, default=None, help='Path to save the downstream dependencies in YAML format')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        packages = buildHelper.compile_downstream_dependencies(
            dirname=args.dirname,
            packages_parent_dir=args.packages_parent_dir,
            downstream_dependencies_filename=args.downstream_dependencies_filename)

        if packages:
            print('The following downstream dependencies were found:')
            for package in packages:
                print('  {}'.format(package))
        else:
            print('No downstream packages were found.')


class ArePackageDependenciesAcyclicController(CementBaseController):
    """ Check if the package dependencies are acyclic so they are suported by CircleCI """

    class Meta:
        label = 'are-package-dependencies-acyclic'
        description = 'Check if the package dependencies are acyclic so they are suported by CircleCI'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--packages-parent-dir'], dict(
                type=str, default='..', help='Path to the parent directory of the other packages')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        if buildHelper.are_package_dependencies_acyclic(packages_parent_dir=args.packages_parent_dir):
            print('The dependencies are acyclic.')
        else:
            print('The dependencies are cyclic. This must be corrected for CircleCI.')


class VisualizePackageDependenciesController(CementBaseController):
    """ Visualize downstream package dependencies as a graph """

    class Meta:
        label = 'visualize-package-dependencies'
        description = 'Visualize downstream package dependencies as a graph'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--packages-parent-dir'], dict(
                type=str, default='..', help='Path to the parent directory of the other packages')),
            (['--out-filename'], dict(
                type=str, default='../package_dependencies.pdf', help='Path to save the visualization')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.visualize_package_dependencies(packages_parent_dir=args.packages_parent_dir, out_filename=args.out_filename)


class TriggerTestsOfDownstreamDependenciesController(CementBaseController):
    """ Trigger CircleCI to test downstream dependencies """

    class Meta:
        label = 'trigger-tests-of-downstream-dependencies'
        description = 'Trigger CircleCI to test downstream dependencies'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--downstream-dependencies-filename'], dict(
                type=str, default='.circleci/downstream_dependencies.yml', help='Path to YAML-formatted list of downstream dependencies')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        packages = buildHelper.trigger_tests_of_downstream_dependencies(
            downstream_dependencies_filename=args.downstream_dependencies_filename)
        if packages:
            print('{} dependent builds were triggered'.format(len(packages)))
            for package in packages:
                print('  {}'.format(package))
        else:
            print('No dependent builds were triggered.')


class AnalyzePackageController(CementBaseController):
    """ Perform static analyses of a package using Pylint """

    class Meta:
        label = 'analyze-package'
        description = 'Perform static analyses of a package using Pylint'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['package_name'], dict(
                type=str, help='Name of the package to analyze')),
            (['--messages'], dict(
                type=str, default='', help='comma-separted list of ids of Pylint checks to run')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        if args.messages:
            messages = [msg.strip() for msg in args.messages.split(',')]
        else:
            messages = None
        buildHelper.analyze_package(args.package_name, messages=messages)


class FindMissingRequirementsController(CementBaseController):
    """ Controller for finding missing requirements """

    class Meta:
        label = 'find-missing-requirements'
        description = 'Finding missing requirements for a package.'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['package_name'], dict(
                type=str, help='Package name')),
            (['--dirname'], dict(
                type=str, default='.', help='Path to package')),
            (['--ignore-files'], dict(
                action="append", default=[], help='Paths to ignore')),

        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        missing = buildHelper.find_missing_requirements(
            args.package_name, dirname=args.dirname, ignore_files=args.ignore_files)
        missing = sorted(missing, key=lambda m: m[0])
        if missing:
            print('The following dependencies should likely be added to requirements.txt')
            for name, uses in missing:
                for use in uses:
                    for filename, lineno in use.locations:
                        print('  {:s}:{:d} dist={:s} module={:s}'.format(
                            os.path.relpath(filename), lineno, name, use.modname))
        else:
            print('requirements.txt appears to contain all of the dependencies')


class FindUnusedRequirementsController(CementBaseController):
    """ Controller for finding unused requirements """

    class Meta:
        label = 'find-unused-requirements'
        description = 'Finding unused requirements for a package.'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['package_name'], dict(
                type=str, help='Package name')),
            (['--dirname'], dict(
                type=str, default='.', help='Path to package')),
            (['--ignore-file'], dict(
                dest='ignore_files', action="append", default=[], help='Paths to ignore')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        unuseds = buildHelper.find_unused_requirements(
            args.package_name, dirname=args.dirname,
            ignore_files=args.ignore_files)
        if unuseds:
            print('The following requirements from requirements.txt may not be necessary:')
            for name in sorted(unuseds):
                print('  {}'.format(name))
        else:
            print('All of the dependencies appear to be necessary')


class UploadPackageToPypiController(CementBaseController):
    """ Upload package to PyPI
    """

    class Meta:
        label = 'upload-package-to-pypi'
        description = 'Upload package to PyPI'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['--dirname'], dict(
                type=str, default='.', help='Path to package (e.g. parent directory of setup.py)')),
            (['--repository'], dict(
                type=str, default='pypi', help='Repository upload package (e.g. pypi or testpypi)')),
            (['--pypi-config-filename'], dict(
                type=str, default='~/.pypirc', help='Path to .pypirc file')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.upload_package_to_pypi(
            dirname=args.dirname,
            repository=args.repository,
            pypi_config_filename=args.pypi_config_filename)


class App(CementApp):
    """ Command line application """
    class Meta:
        label = 'karr_lab_build_utils'
        base_controller = 'base'
        handlers = [
            BaseController,
            CreateRepositoryController,
            SetupRepositoryController,
            CreateDocumentationTemplateController,
            RunTestsController,
            CreateCircleciBuildController,
            GetCircleciEnvironmentVariablesController,
            SetCircleciEnvironmentVariableController,
            DeleteCircleciEnvironmentVariableController,
            CreateCodeclimateGithubWebhookController,
            MakeAndArchiveReportsController,
            CombineCoverageReportsController,
            ArchiveCoverageReportController,
            UploadCoverageReportToCoverallsController,
            UploadCoverageReportToCodeClimateController,
            MakeDocumentationController,
            CompileDownstreamDependenciesController,
            ArePackageDependenciesAcyclicController,
            VisualizePackageDependenciesController,
            TriggerTestsOfDownstreamDependenciesController,
            AnalyzePackageController,
            FindMissingRequirementsController,
            FindUnusedRequirementsController,
            UploadPackageToPypiController,
        ]


def main():
    with App() as app:
        app.run()
