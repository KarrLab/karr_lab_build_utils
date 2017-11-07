""" Tests karr_lab_build_utils.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from glob import glob
from jinja2 import Template
from karr_lab_build_utils.__main__ import App as KarrLabBuildUtilsCli
from karr_lab_build_utils.core import BuildHelper
from pkg_resources import resource_filename
import shutil
import os
import sys
import tempfile
import unittest

if sys.version_info >= (3, 0, 0):
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard


class TestKarrLabBuildUtils(unittest.TestCase):
    COVERALLS_REPO_TOKEN = ''
    CODECLIMATE_REPO_TOKEN = ''
    DUMMY_TEST = 'tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test'

    @staticmethod
    def construct_environment():
        env = EnvironmentVarGuard()
        env.set('CIRCLE_TEST_REPORTS', tempfile.mkdtemp())
        env.set('COVERALLS_REPO_TOKEN', TestKarrLabBuildUtils.COVERALLS_REPO_TOKEN)
        env.set('CODECLIMATE_REPO_TOKEN', TestKarrLabBuildUtils.CODECLIMATE_REPO_TOKEN)
        env.set('CIRCLE_BUILD_NUM', '0')
        env.set('CIRCLE_BRANCH', 'master')
        env.set('CIRCLE_SHA1', '--test--')

        if not os.getenv('CIRCLE_PROJECT_REPONAME'):
            with open('tests/fixtures/CIRCLE_PROJECT_REPONAME', 'r') as file:
                env.set('CIRCLE_PROJECT_REPONAME', file.read().rstrip())

        if not os.getenv('CIRCLE_PROJECT_USERNAME'):
            with open('tests/fixtures/CIRCLE_PROJECT_USERNAME', 'r') as file:
                env.set('CIRCLE_PROJECT_USERNAME', file.read().rstrip())

        if not os.getenv('GITHUB_USERNAME'):
            with open('tests/fixtures/secret/GITHUB_USERNAME', 'r') as file:
                env.set('GITHUB_USERNAME', file.read().rstrip())

        if not os.getenv('GITHUB_PASSWORD'):
            with open('tests/fixtures/secret/GITHUB_PASSWORD', 'r') as file:
                env.set('GITHUB_PASSWORD', file.read().rstrip())

        if not os.getenv('CIRCLE_API_TOKEN'):
            with open('tests/fixtures/secret/CIRCLE_API_TOKEN', 'r') as file:
                env.set('CIRCLE_API_TOKEN', file.read().rstrip())

        if not os.getenv('TEST_SERVER_TOKEN'):
            with open('tests/fixtures/secret/TEST_SERVER_TOKEN', 'r') as file:
                env.set('TEST_SERVER_TOKEN', file.read().rstrip())

        return env

    @staticmethod
    def construct_build_helper():
        with TestKarrLabBuildUtils.construct_environment():
            buildHelper = BuildHelper()

        return buildHelper

    def test_create_repository(self):
        buildHelper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        """ test API """
        # test valid repo names
        buildHelper.create_repository(dirname=os.path.join(tempdirname, 'a'))
        buildHelper.create_repository(dirname=os.path.join(tempdirname, 'a2'))
        buildHelper.create_repository(dirname=os.path.join(tempdirname, 'a_2'))
        self.assertRaises(Exception, buildHelper.create_repository, dirname=os.path.join(tempdirname, '2'))
        self.assertRaises(Exception, buildHelper.create_repository, dirname=os.path.join(tempdirname, 'a-'))

        # check files create correctly
        self.assertTrue(os.path.isdir(os.path.join(tempdirname, 'a', '.git')))

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['create-repository', '--dirname', os.path.join(tempdirname, 'b')]) as app:
                app.run()

        self.assertTrue(os.path.isdir(os.path.join(tempdirname, 'b', '.git')))

        """ cleanup """
        shutil.rmtree(tempdirname)

    def test_setup_repository(self):
        buildHelper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        """ test API """
        # test valid repo names
        buildHelper.setup_repository(dirname=os.path.join(tempdirname, 'a'))
        buildHelper.setup_repository(dirname=os.path.join(tempdirname, 'a2'))
        buildHelper.setup_repository(dirname=os.path.join(tempdirname, 'a_2'))
        self.assertRaises(Exception, buildHelper.setup_repository, dirname=os.path.join(tempdirname, '2'))
        self.assertRaises(Exception, buildHelper.setup_repository, dirname=os.path.join(tempdirname, 'a-'))

        # check files create correctly
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.gitignore')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'LICENSE')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'MANIFEST.in')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'README.md')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'setup.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'setup.cfg')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'a', '__init__.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'tests', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'conf.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.circleci', 'config.yml')))

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['setup-repository', '--dirname', os.path.join(tempdirname, 'b')]) as app:
                app.run()

        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.gitignore')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'LICENSE')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'MANIFEST.in')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'README.md')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'setup.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'setup.cfg')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'b', '__init__.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'tests', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'conf.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.circleci', 'config.yml')))

        """ cleanup """
        shutil.rmtree(tempdirname)

    def test_create_circleci_build(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        buildHelper.create_circleci_build()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['create-circleci-build']) as app:
                app.run()

    def test_create_codeclimate_github_webhook(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        try:
            buildHelper.create_codeclimate_github_webhook()
        except ValueError as err:
            pass

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['create-codeclimate-github-webhook']) as app:
                try:
                    app.run()
                except ValueError as err:
                    pass

    def test_install_requirements(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        buildHelper.install_requirements()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['install-requirements']) as app:
                app.run()

    def test_run_tests(self):
        self.help_run('pytest')
        self.help_run('nose')

    def help_run(self, test_runner):
        buildHelper = self.construct_build_helper()
        buildHelper.test_runner = test_runner
        py_v = buildHelper.get_python_version()

        """ test API """
        latest_results_filename = os.path.join(buildHelper.proj_tests_xml_dir, '{0:s}.{1:s}.xml'.format(
            buildHelper.proj_tests_xml_latest_filename, py_v))
        lastest_cov_filename = '.coverage.{}'.format(py_v)
        if os.path.isfile(latest_results_filename):
            os.remove(latest_results_filename)
        if os.path.isfile(lastest_cov_filename):
            os.remove(lastest_cov_filename)

        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)

        self.assertTrue(os.path.isfile(latest_results_filename))
        self.assertTrue(os.path.isfile(lastest_cov_filename))

        """ test CLI """
        argv = ['run-tests', TestKarrLabBuildUtils.DUMMY_TEST, '--with-xunit', '--with-coverage']
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=argv) as app:
                app.run()
                self.assertEqual(TestKarrLabBuildUtils.DUMMY_TEST, app.pargs.test_path)
                self.assertTrue(app.pargs.with_xunit)
                self.assertTrue(app.pargs.with_coverage)

    def test_make_and_archive_reports(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)

        py_v = buildHelper.get_python_version()
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_xml_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_xml_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_xml_dir, '{0:d}.{1:s}.xml'.format(10000000000000001, py_v))
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_xml_dir, '{0:s}.{1:s}.xml'.format(
                buildHelper.proj_tests_xml_latest_filename, py_v)),
            os.path.join(buildHelper.proj_tests_xml_dir, '{0:d}.{1:s}.xml'.format(10000000000000002, py_v))
        )

        """ test API """
        buildHelper.make_and_archive_reports()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['make-and-archive-reports']) as app:
                app.run()

    def test_archive_test_report(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)

        """ test API """
        buildHelper.archive_test_report()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['archive-test-report']) as app:
                app.run()

    def test_combine_coverage_reports(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)
        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage.1')
        shutil.copyfile('.coverage.1', '.coverage.2')

        """ test API """
        if os.path.isfile('.coverage'):
            os.remove('.coverage')
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        buildHelper.combine_coverage_reports()

        self.assertTrue(os.path.isfile('.coverage'))
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        """ test CLI """
        if os.path.isfile('.coverage'):
            os.remove('.coverage')
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['combine-coverage-reports']) as app:
                app.run()

        self.assertTrue(os.path.isfile('.coverage'))
        self.assertTrue(os.path.isfile('.coverage.1'))
        self.assertTrue(os.path.isfile('.coverage.2'))

        # cleanup
        os.remove('.coverage.1')
        os.remove('.coverage.2')

    def test_archive_coverage_report(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)

        buildHelper.combine_coverage_reports()

        """ test API """
        buildHelper.archive_coverage_report()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['archive-coverage-report']) as app:
                app.run()

    def test_upload_coverage_report_to_coveralls(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)

        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage')

        """ test API """
        buildHelper.upload_coverage_report_to_coveralls()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['upload-coverage-report-to-coveralls']) as app:
                app.run()

    def test_upload_coverage_report_to_code_climate(self):
        buildHelper = self.construct_build_helper()
        buildHelper.run_tests(test_path=self.DUMMY_TEST,
                              with_xunit=True, with_coverage=True, exit_on_failure=False)

        shutil.move('.coverage.{}'.format(buildHelper.get_python_version()), '.coverage')

        """ test API """
        buildHelper.upload_coverage_report_to_code_climate()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['upload-coverage-report-to-code-climate']) as app:
                app.run()

    def test_create_documentation_template(self):
        buildHelper = self.construct_build_helper()

        filenames = ['conf.py', 'index.rst', 'overview.rst', 'installation.rst', 'about.rst']

        """ test API """
        tempdirname = tempfile.mkdtemp()
        name = os.path.basename(os.path.abspath(tempdirname))

        with open(resource_filename('karr_lab_build_utils', 'templates/setup.cfg'), 'r') as file:
            template = Template(file.read())
        template.stream(name=name).dump(os.path.join(tempdirname, 'setup.cfg'))

        buildHelper.create_documentation_template(tempdirname)

        for filename in filenames:
            self.assertTrue(os.path.isfile(os.path.join(tempdirname, buildHelper.proj_docs_dir, filename)))

        shutil.rmtree(tempdirname)

        """ test CLI """
        tempdirname = tempfile.mkdtemp()
        name = os.path.basename(os.path.abspath(tempdirname))

        with open(resource_filename('karr_lab_build_utils', 'templates/setup.cfg'), 'r') as file:
            template = Template(file.read())
        template.stream(name=name).dump(os.path.join(tempdirname, 'setup.cfg'))

        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['create-documentation-template', '--dirname', tempdirname]) as app:
                app.run()

        for filename in filenames:
            self.assertTrue(os.path.isfile(os.path.join(tempdirname, buildHelper.proj_docs_dir, filename)))

        shutil.rmtree(tempdirname)

    def test_make_documentation(self):
        buildHelper = self.construct_build_helper()

        """ test API """
        if os.path.isdir(buildHelper.proj_docs_build_html_dir):
            shutil.rmtree(buildHelper.proj_docs_build_html_dir)

        buildHelper.make_documentation()

        self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_docs_build_html_dir, 'index.html')))

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['make-documentation']) as app:
                app.run()

    def test_get_version(self):
        """ setup """
        buildHelper = self.construct_build_helper()

        """ test API """
        buildHelper.get_version()

        """ test CLI """
        with self.construct_environment():
            with KarrLabBuildUtilsCli(argv=['get-version']) as app:
                app.run()

    def test_dummy_test(self):
        buildHelper = self.construct_build_helper()
