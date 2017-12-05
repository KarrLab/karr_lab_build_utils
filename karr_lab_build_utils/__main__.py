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

    @expose(help='Create CircleCI build for the current repository')
    def create_circleci_build(self):
        """ Create CircleCI build for the current repository """
        buildHelper = BuildHelper()
        buildHelper.create_circleci_build()

    @expose(help='Create CodeClimate GitHub webook for the current repository')
    def create_codeclimate_github_webhook(self):
        """ Create CodeClimate GitHub webook for the current repository """
        buildHelper = BuildHelper()
        buildHelper.create_codeclimate_github_webhook()

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
                default='tests', type=str, help='path to tests that should be run')),
            (['--with-xunit'], dict(
                default=False, dest='with_xunit', action='store_true', help='True/False to save test results to XML file')),
            (['--with-coverage'], dict(
                default=False, dest='with_coverage', action='store_true', help='True/False to assess code coverage')),
            (['--coverage-dirname'], dict(
                default='.', dest='coverage_dirname', help='Directory to store coverage data')),
            (['--environment'], dict(
                type=str, default='local', help='Environment to run tests (local, docker, or circleci-local-executor)')),
        ]

    @expose(hide=True)
    def default(self):
        args = self.app.pargs
        buildHelper = BuildHelper()
        buildHelper.run_tests(test_path=args.test_path, with_xunit=args.with_xunit,
                              with_coverage=args.with_coverage, coverage_dirname=args.coverage_dirname,
                              environment=args.environment)


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


class AnalyzePackage(CementBaseController):
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
        if missing:
            print('The following dependencies should likely be added to requirements.txt\n')
            for name, uses in missing:
                for use in uses:
                    for filename, lineno in use.locations:
                        print('  {:s}:{:d} dist={:s} module={:s}\n'.format(
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
            print('The following requirements from requirements.txt may not be necessary:\n')
            for name in unuseds:
                print('  {}\n'.format(name))
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
            MakeAndArchiveReportsController,
            CombineCoverageReportsController,
            ArchiveCoverageReportController,
            UploadCoverageReportToCoverallsController,
            UploadCoverageReportToCodeClimateController,
            MakeDocumentationController,
            AnalyzePackage,
            FindMissingRequirementsController,
            FindUnusedRequirementsController,
            UploadPackageToPypiController,
        ]


def main():
    with App() as app:
        app.run()
