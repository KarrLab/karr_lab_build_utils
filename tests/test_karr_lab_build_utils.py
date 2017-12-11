""" Tests karr_lab_build_utils.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from codeclimate_test_reporter.components.runner import Runner as CodeClimateRunner
from glob import glob
from jinja2 import Template
from karr_lab_build_utils import __main__
from karr_lab_build_utils import core
from pkg_resources import resource_filename
from six.moves import configparser
import abduct
import attrdict
import capturer
import imp
import karr_lab_build_utils
import karr_lab_build_utils.__init__
import mock
import nose
import os
import pip
import pytest
import requests
import shutil
import six
import smtplib
import sys
import tempfile
import unittest
import whichcraft
import yaml

# reload modules to get coverage correct
imp.reload(core)
imp.reload(karr_lab_build_utils)
imp.reload(karr_lab_build_utils.__init__)
imp.reload(__main__)

if sys.version_info >= (3, 0, 0):
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard


class TestKarrLabBuildUtils(unittest.TestCase):
    COVERALLS_REPO_TOKEN = 'xxx'
    CODECLIMATE_REPO_TOKEN = 'xxx'
    DUMMY_TEST = 'tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test'

    def setUp(self):
        self.coverage_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.coverage_dirname)

    @staticmethod
    def construct_environment(build_num=0):
        env = EnvironmentVarGuard()
        env.set('CIRCLE_TEST_REPORTS', tempfile.mkdtemp())
        env.set('COVERALLS_REPO_TOKEN', TestKarrLabBuildUtils.COVERALLS_REPO_TOKEN)
        env.set('CODECLIMATE_REPO_TOKEN', TestKarrLabBuildUtils.CODECLIMATE_REPO_TOKEN)
        env.set('CIRCLE_BUILD_NUM', str(build_num))
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

        if not os.getenv('CIRCLECI_API_TOKEN'):
            with open('tests/fixtures/secret/CIRCLECI_API_TOKEN', 'r') as file:
                env.set('CIRCLECI_API_TOKEN', file.read().rstrip())

        if not os.getenv('TEST_SERVER_TOKEN'):
            with open('tests/fixtures/secret/TEST_SERVER_TOKEN', 'r') as file:
                env.set('TEST_SERVER_TOKEN', file.read().rstrip())

        if not os.getenv('KARR_LAB_DAEMON_GMAIL_PASSWORD'):
            with open('tests/fixtures/secret/KARR_LAB_DAEMON_GMAIL_PASSWORD', 'r') as file:
                env.set('KARR_LAB_DAEMON_GMAIL_PASSWORD', file.read().rstrip())

        return env

    @staticmethod
    def construct_build_helper(build_num=0):
        with TestKarrLabBuildUtils.construct_environment(build_num=build_num):
            build_helper = core.BuildHelper()

        return build_helper

    def test_create_repository(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        """ test API """
        # test valid repo names
        build_helper.create_repository(dirname=os.path.join(tempdirname, 'a'))
        build_helper.create_repository(dirname=os.path.join(tempdirname, 'a2'))
        build_helper.create_repository(dirname=os.path.join(tempdirname, 'a_2'))
        self.assertRaises(Exception, build_helper.create_repository, dirname=os.path.join(tempdirname, '2'))
        self.assertRaises(Exception, build_helper.create_repository, dirname=os.path.join(tempdirname, 'a-'))

        # check files create correctly
        self.assertTrue(os.path.isdir(os.path.join(tempdirname, 'a', '.git')))

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['create-repository', '--dirname', os.path.join(tempdirname, 'b')]) as app:
                app.run()

        self.assertTrue(os.path.isdir(os.path.join(tempdirname, 'b', '.git')))

        """ cleanup """
        shutil.rmtree(tempdirname)

    def test_setup_repository(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        """ test API """
        # test valid repo names
        build_helper.setup_repository(dirname=os.path.join(tempdirname, 'a'))
        build_helper.setup_repository(dirname=os.path.join(tempdirname, 'a2'))
        build_helper.setup_repository(dirname=os.path.join(tempdirname, 'a_2'))
        self.assertRaises(Exception, build_helper.setup_repository, dirname=os.path.join(tempdirname, '2'))
        self.assertRaises(Exception, build_helper.setup_repository, dirname=os.path.join(tempdirname, 'a-'))

        # check files create correctly
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.gitignore')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'LICENSE')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'MANIFEST.in')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'README.md')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'requirements.optional.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'setup.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'setup.cfg')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'a', '__init__.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'a', 'VERSION')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'tests', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'conf.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'conda.environment.yml')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'spelling_wordlist.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.circleci', 'config.yml')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.readthedocs.yml')))

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['setup-repository', '--dirname', os.path.join(tempdirname, 'b')]) as app:
                app.run()

        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.gitignore')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'LICENSE')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'MANIFEST.in')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'README.md')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'requirements.optional.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'setup.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'setup.cfg')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'b', '__init__.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'b', 'VERSION')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'tests', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'conf.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'conda.environment.yml')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'spelling_wordlist.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.circleci', 'config.yml')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.readthedocs.yml')))

        """ cleanup """
        shutil.rmtree(tempdirname)

    def test_create_circleci_build(self):
        """ test API """
        with self.construct_environment():
            build_helper = self.construct_build_helper()
        build_helper.create_circleci_build()

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['create-circleci-build']) as app:
                app.run()

    def test_create_circleci_build_error(self):
        with self.construct_environment():
            build_helper = self.construct_build_helper()

        class Result(object):

            def raise_for_status(self):
                return
            def json(self):
                return {'following': False}

        with mock.patch.object(requests, 'post', return_value=Result()):
            with self.assertRaisesRegexp(ValueError, '^Unable to create CircleCI build for repository'):
                build_helper.create_circleci_build()

    def test_get_circleci_environment_variables(self):
        """ test API """
        with self.construct_environment():
            build_helper = self.construct_build_helper()

        vars = build_helper.get_circleci_environment_variables()
        self.assertTrue('TEST_SERVER_TOKEN' in vars)
        self.assertTrue('COVERALLS_REPO_TOKEN' in vars)
        self.assertTrue('CODECLIMATE_REPO_TOKEN' in vars)

        """ test CLI """
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['get-circleci-environment-variables']) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), 'COVERALLS_REPO_TOKEN=')
                    self.assertEqual(captured.stderr.get_text(), '')

    def test_set_circleci_environment_variables(self):
        """ test API """
        with self.construct_environment():
            build_helper = self.construct_build_helper()

        build_helper.set_circleci_environment_variables({
            '__TEST1__': 'test value 1a',
            '__TEST2__': 'test value 2a',
        })
        vars = build_helper.get_circleci_environment_variables()
        self.assertEqual(vars['__TEST1__'], 'xxxxe 1a')
        self.assertEqual(vars['__TEST2__'], 'xxxxe 2a')

        build_helper.set_circleci_environment_variables({
            '__TEST1__': 'test value 1b',
        })
        vars = build_helper.get_circleci_environment_variables()
        self.assertEqual(vars['__TEST1__'], 'xxxxe 1b')

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['set-circleci-environment-variable', '__TEST1__', 'test value 1c']) as app:
                with capturer.CaptureOutput(merged=False, relay=False) as captured:
                    app.run()
                    self.assertEqual(captured.stdout.get_text(), '')
                    self.assertEqual(captured.stderr.get_text(), '')

            with __main__.App(argv=['get-circleci-environment-variables']) as app:
                with capturer.CaptureOutput(merged=False, relay=False) as captured:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '__TEST1__=xxxxe 1c')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        build_helper.delete_circleci_environment_variable('__TEST1__')
        build_helper.delete_circleci_environment_variable('__TEST2__')

    def test_delete_circleci_environment_variables(self):
        """ test API """
        with self.construct_environment():
            build_helper = self.construct_build_helper()

        build_helper.set_circleci_environment_variables({
            '__TEST1__': 'test value 1a',
        })
        vars = build_helper.get_circleci_environment_variables()
        self.assertTrue('__TEST1__' in vars)

        build_helper.delete_circleci_environment_variable('__TEST1__')

        vars = build_helper.get_circleci_environment_variables()
        self.assertTrue('__TEST1__' not in vars)

        """ test CLI """
        build_helper.set_circleci_environment_variables({
            '__TEST1__': 'test value 1a',
        })
        vars = build_helper.get_circleci_environment_variables()
        self.assertTrue('__TEST1__' in vars)

        with self.construct_environment():
            with __main__.App(argv=['delete-circleci-environment-variable', '__TEST1__']) as app:
                with capturer.CaptureOutput(merged=False, relay=False) as captured:
                    app.run()
                    self.assertEqual(captured.stdout.get_text(), '')
                    self.assertEqual(captured.stderr.get_text(), '')

        vars = build_helper.get_circleci_environment_variables()
        self.assertTrue('__TEST1__' not in vars)

    def test_create_codeclimate_github_webhook(self):
        build_helper = self.construct_build_helper()

        """ test API """
        try:
            build_helper.create_codeclimate_github_webhook()
        except ValueError as err:
            pass

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['create-codeclimate-github-webhook']) as app:
                try:
                    app.run()
                except ValueError as err:
                    pass

    def test_create_codeclimate_github_webhook_error(self):
        build_helper = self.construct_build_helper()

        class Result(object):

            def __init__(self):
                self.status_code = 0

            def json(self):
                return {'message': 'Error!'}

        with mock.patch.object(requests, 'post', return_value=Result()):
            with self.assertRaisesRegexp(ValueError, '^Unable to create webhook for'):
                build_helper.create_codeclimate_github_webhook()

    def test_install_requirements(self):
        build_helper = self.construct_build_helper()

        """ test API """
        build_helper.install_requirements()

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['install-requirements']) as app:
                app.run()

    def test_install_requirements_no_file(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()
        build_helper.proj_tests_dir = tempdirname
        build_helper.proj_docs_dir = tempdirname

        build_helper.install_requirements()

        shutil.rmtree(tempdirname)

    def test_run_tests(self):
        self.help_run('pytest', coverage_type=core.CoverageType.statement)
        self.help_run('nose', coverage_type=core.CoverageType.branch)
        with self.assertRaisesRegexp(core.BuildHelperError, '^Unsupported coverage type: '):
            self.help_run('pytest', coverage_type=core.CoverageType.multiple_condition)

    def help_run(self, test_runner, coverage_type=core.CoverageType.statement):
        build_helper = self.construct_build_helper()
        build_helper.test_runner = test_runner
        py_v = build_helper.get_python_version()

        tempdirname = tempfile.mkdtemp()
        shutil.rmtree(tempdirname)
        build_helper.proj_tests_xml_dir = tempdirname

        """ test API """
        latest_results_filename = os.path.join(build_helper.proj_tests_xml_dir, '{0:s}.{1:s}.xml'.format(
            build_helper.proj_tests_xml_latest_filename, py_v))
        lastest_cov_filename = os.path.join(self.coverage_dirname, '.coverage.{}'.format(py_v))
        if os.path.isdir(build_helper.proj_tests_xml_dir):
            shutil.rmtree(build_helper.proj_tests_xml_dir)
        if os.path.isfile(latest_results_filename):
            os.remove(latest_results_filename)
        if os.path.isfile(lastest_cov_filename):
            os.remove(lastest_cov_filename)

        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname,
                               coverage_type=coverage_type)

        self.assertTrue(os.path.isfile(latest_results_filename))
        self.assertTrue(os.path.isfile(lastest_cov_filename))

        """ test CLI """
        argv = ['run-tests', '--test-path', TestKarrLabBuildUtils.DUMMY_TEST, '--with-xunit', '--with-coverage']
        with self.construct_environment():
            with __main__.App(argv=argv) as app:
                app.run()
                self.assertEqual(TestKarrLabBuildUtils.DUMMY_TEST, app.pargs.test_path)
                self.assertTrue(app.pargs.with_xunit)
                self.assertTrue(app.pargs.with_coverage)

        shutil.rmtree(tempdirname)

    def test_run_tests_error(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()
        shutil.rmtree(tempdirname)
        build_helper.proj_tests_xml_dir = tempdirname

        build_helper.test_runner = 'unsupported_runner'
        with self.assertRaisesRegexp(Exception, '^Unsupported test runner'):
            build_helper.run_tests(test_path=self.DUMMY_TEST, with_xunit=True)

        build_helper.test_runner = 'pytest'
        with mock.patch.object(pytest, 'main', return_value=1):
            with self.assertRaises(SystemExit):
                build_helper.run_tests(test_path=self.DUMMY_TEST, with_xunit=True)

        build_helper.test_runner = 'nose'
        with mock.patch.object(nose, 'run', return_value=False):
            with self.assertRaises(SystemExit):
                build_helper.run_tests(test_path=self.DUMMY_TEST, with_xunit=True)

        shutil.rmtree(tempdirname)

    @unittest.skipIf(whichcraft.which('docker') is None, (
        'Test requires Docker and Docker isn''t installed. '
        'See installation instructions at `https://intro-to-wc-modeling.readthedocs.io/en/latest/installation.html`'
    ))
    def test_run_tests_docker(self):
        build_helper = self.construct_build_helper()

        # test success
        build_helper.run_tests(test_path=self.DUMMY_TEST, environment=core.Environment.docker)

        # :todo: test failure

    @unittest.skipIf(whichcraft.which('docker') is None or whichcraft.which('circleci') is None, (
        'Test requires the CircleCI command line utility (local executor) and this isn''t installed. See '
        'installation instructions at `http://intro-to-wc-modeling.readthedocs.io/en/latest/installation.html`.'
    ))
    def test_run_tests_circleci(self):
        build_helper = self.construct_build_helper()

        # test success
        with self.assertRaisesRegexp(core.BuildHelperError, '404 Client Error'):
            build_helper.run_tests(test_path=self.DUMMY_TEST, environment=core.Environment.circleci)

        # :todo: test failure

    def test_run_tests_unsupported_env(self):
        build_helper = self.construct_build_helper()
        with self.assertRaisesRegexp(core.BuildHelperError, '^Unsupported environment:'):
            build_helper.run_tests(test_path=self.DUMMY_TEST, environment=None)

    def test_do_post_test_tasks(self):
        down_pkgs_return = []
        notify_return = {
            'is_fixed': False,
            'is_old_error': False,
            'is_new_error': False,
            'is_new_downstream_error': False,
        }
        with mock.patch.object(core.BuildHelper, 'make_and_archive_reports', return_value=None):
            with mock.patch.object(core.BuildHelper, 'trigger_tests_of_downstream_dependencies', return_value=down_pkgs_return):
                with mock.patch.object(core.BuildHelper, 'send_email_notifications', return_value=notify_return):
                    # test api
                    build_helper = self.construct_build_helper()
                    build_helper.do_post_test_tasks()

                    # test cli
                    with self.construct_environment():
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            with __main__.App(argv=['do-post-test-tasks']) as app:
                                app.run()
                                self.assertRegexpMatches(captured.stdout.get_text(), 'No downstream builds were triggered.')
                                self.assertRegexpMatches(captured.stdout.get_text(), 'No notifications were sent.')
                                self.assertEqual(captured.stderr.get_text(), '')

        down_pkgs_return = ['pkg_1', 'pkg_2']
        notify_return = {
            'is_fixed': True,
            'is_old_error': True,
            'is_new_error': True,
            'is_new_downstream_error': True,
        }
        with mock.patch.object(core.BuildHelper, 'make_and_archive_reports', return_value=None):
            with mock.patch.object(core.BuildHelper, 'trigger_tests_of_downstream_dependencies', return_value=down_pkgs_return):
                with mock.patch.object(core.BuildHelper, 'send_email_notifications', return_value=notify_return):
                    # test api
                    build_helper = self.construct_build_helper()
                    build_helper.do_post_test_tasks()

                    # test cli
                    with self.construct_environment():
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            with __main__.App(argv=['do-post-test-tasks']) as app:
                                app.run()
                                self.assertRegexpMatches(captured.stdout.get_text(), '2 downstream builds were triggered')
                                self.assertRegexpMatches(captured.stdout.get_text(), '  pkg_1')
                                self.assertRegexpMatches(captured.stdout.get_text(), '  pkg_2')
                                self.assertRegexpMatches(captured.stdout.get_text(), '4 notifications were sent')
                                self.assertRegexpMatches(captured.stdout.get_text(), '  Build fixed notification')
                                self.assertRegexpMatches(captured.stdout.get_text(), '  Recurring error notification')
                                self.assertRegexpMatches(captured.stdout.get_text(), '  New error notification')
                                self.assertRegexpMatches(captured.stdout.get_text(), '  Downstream error notification')
                                self.assertEqual(captured.stderr.get_text(), '')

    def test_get_test_results(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{0}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="0" failures="0" skips="0" tests="4">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_1" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_2" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_skipped_5" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <skipped type="skip" message="msg">details</skipped>')
            file.write('  </testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 4)
        self.assertEqual(test_results.get_num_passed(), 3)
        self.assertEqual(test_results.get_num_skipped(), 1)
        self.assertEqual(test_results.get_num_errors(), 0)
        self.assertEqual(test_results.get_num_failures(), 0)

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_no_failure(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{0}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="0" failures="0" skips="0" tests="4">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_1" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_2" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_skipped_4" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <skipped type="skip" message="msg">details</skipped>')
            file.write('  </testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 4)
        self.assertEqual(test_results.get_num_passed(), 3)
        self.assertEqual(test_results.get_num_skipped(), 1)
        self.assertEqual(test_results.get_num_errors(), 0)
        self.assertEqual(test_results.get_num_failures(), 0)

        # requests side effects
        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'commit': 'yyyyyyyyyyyyyyyyyyyy',
                    'committer_name': 'Test user 2',
                    'committer_email': 'test2@test.com',
                    'subject': 'Test commit 2',
                    'commit_url': 'https://github.com/KarrLab/test_repo_2/commit/yyyyyyyyyyyyyyyyyyyy',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo_2/51',
            },
        })

        # mock SMTP
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })

        # test API
        with self.construct_environment(build_num=1):
            build_helper = self.construct_build_helper(build_num=1)
            with mock.patch('requests.get', side_effect=[requests_get_1]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications()
                    self.assertEqual(result, {
                        'is_fixed': True,
                        'is_new_error': False,
                        'is_old_error': False,
                        'is_new_downstream_error': False,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_fixed(self):
        build_helper = self.construct_build_helper(build_num=10)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{0}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="0" failures="0" skips="0" tests="4">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_1" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_2" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" time="0.01"></testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_skipped_4" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <skipped type="skip" message="msg">details</skipped>')
            file.write('  </testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 4)
        self.assertEqual(test_results.get_num_passed(), 3)
        self.assertEqual(test_results.get_num_skipped(), 1)
        self.assertEqual(test_results.get_num_errors(), 0)
        self.assertEqual(test_results.get_num_failures(), 0)

        # requests side effects
        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'commit': 'yyyyyyyyyyyyyyyyyyy1',
                    'committer_name': 'Test user 1',
                    'committer_email': 'test1@test.com',
                    'subject': 'Test commit 1',
                    'commit_url': 'https://github.com/KarrLab/test_repo/commit/yyyyyyyyyyyyyyyyyyy1',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo/51',
                'status': 'failure',
            },
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'commit': 'yyyyyyyyyyyyyyyyyyy2',
                    'committer_name': 'Test user 2',
                    'committer_email': 'test2@test.com',
                    'subject': 'Test commit 2',
                    'commit_url': 'https://github.com/KarrLab/test_repo/commit/yyyyyyyyyyyyyyyyyyy2',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo/52',
            },
        })

        # mock SMTP
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })

        # test API
        with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
            with mock.patch('smtplib.SMTP', return_value=smtp):
                result = build_helper.send_email_notifications()
                self.assertEqual(result, {
                    'is_fixed': True,
                    'is_new_error': False,
                    'is_old_error': False,
                    'is_new_downstream_error': False,
                })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_no_upstream(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="1" failures="1" skips="0" tests="3">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_error_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <error type="err" message="msg">details</error>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_failure_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <failure type="err" message="msg">details</failure>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" file="/script.py" line="1" time="0.01"></testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 3)
        self.assertEqual(test_results.get_num_passed(), 1)
        self.assertEqual(test_results.get_num_skipped(), 0)
        self.assertEqual(test_results.get_num_errors(), 1)
        self.assertEqual(test_results.get_num_failures(), 1)

        # requests side effects
        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'commit': 'yyyyyyyyyyyyyyyyyyyy',
                    'committer_name': 'Test user 2',
                    'committer_email': 'test2@test.com',
                    'subject': 'Test commit 2',
                    'commit_url': 'https://github.com/KarrLab/test_repo_2/commit/yyyyyyyyyyyyyyyyyyyy',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo_2/51',
            },
        })

        # mock SMTP
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })

        # test API
        with mock.patch('requests.get', side_effect=[requests_get_1]):
            with mock.patch('smtplib.SMTP', return_value=smtp):
                result = build_helper.send_email_notifications()
                self.assertEqual(result, {
                    'is_fixed': False,
                    'is_new_error': True,
                    'is_old_error': False,
                    'is_new_downstream_error': False,
                })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_no_previous_builds(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="1" failures="1" skips="0" tests="3">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_error_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <error type="err" message="msg">details</error>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_failure_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <failure type="err" message="msg">details</failure>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" file="/script.py" line="1" time="0.01"></testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 3)
        self.assertEqual(test_results.get_num_passed(), 1)
        self.assertEqual(test_results.get_num_skipped(), 0)
        self.assertEqual(test_results.get_num_errors(), 1)
        self.assertEqual(test_results.get_num_failures(), 1)

        # requests side effects
        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'commit': 'yyyyyyyyyyyyyyyyyyyy',
                    'committer_name': 'Test user 2',
                    'committer_email': 'test2@test.com',
                    'subject': 'Test commit 2',
                    'commit_url': 'https://github.com/KarrLab/test_repo_2/commit/yyyyyyyyyyyyyyyyyyyy',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo_2/51',
            },
        })

        # mock SMTP
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })

        # mock environment
        env = self.construct_environment(build_num=1)
        env.set('CIRCLE_PROJECT_REPONAME', 'test_repo_2')
        env.set('CIRCLE_SHA1', 'yyyyyyyyyyyyyyyyyyyy')
        env.set('CIRCLE_BUILD_NUM', '1')
        env.set('UPSTREAM_REPONAME', 'test_repo')
        env.set('UPSTREAM_BUILD_NUM', '101')

        # test API
        with mock.patch('requests.get', side_effect=[requests_get_1]):
            with mock.patch('smtplib.SMTP', return_value=smtp):
                with env:
                    build_helper = self.construct_build_helper(build_num=1)
                    result = build_helper.send_email_notifications()
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': True,
                        'is_old_error': False,
                        'is_new_downstream_error': False,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_existing_error(self):
        build_helper = self.construct_build_helper()

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="1" failures="1" skips="0" tests="3">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_error_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <error type="err" message="msg">details</error>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_failure_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <failure type="err" message="msg">details</failure>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" file="/script.py" line="1" time="0.01"></testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 3)
        self.assertEqual(test_results.get_num_passed(), 1)
        self.assertEqual(test_results.get_num_skipped(), 0)
        self.assertEqual(test_results.get_num_errors(), 1)
        self.assertEqual(test_results.get_num_failures(), 1)

        # requests side effects
        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'status': 'failure'},
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'commit': 'yyyyyyyyyyyyyyyyyyyy',
                    'committer_name': 'Test user 2',
                    'committer_email': 'test2@test.com',
                    'subject': 'Test commit 2',
                    'commit_url': 'https://github.com/KarrLab/test_repo_2/commit/yyyyyyyyyyyyyyyyyyyy',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo_2/51',
            },
        })

        # mock SMTP
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })

        # mock environment
        env = self.construct_environment(build_num=51)
        env.set('CIRCLE_PROJECT_REPONAME', 'test_repo_2')
        env.set('CIRCLE_SHA1', 'yyyyyyyyyyyyyyyyyyyy')
        env.set('CIRCLE_BUILD_NUM', '51')
        env.set('UPSTREAM_REPONAME', 'test_repo')
        env.set('UPSTREAM_BUILD_NUM', '101')

        # test API
        with env:
            build_helper = self.construct_build_helper(build_num=51)
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications()
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': False,
                        'is_old_error': True,
                        'is_new_downstream_error': False,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_send_email(self):
        build_helper = self.construct_build_helper()

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
        with open(filename, 'w') as file:
            file.write('<?xml version="1.0" encoding="utf-8"?>')
            file.write('<testsuite errors="1" failures="1" skips="0" tests="3">')
            file.write('  <testcase classname="tests.core.TestCase" name="test_error_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <error type="err" message="msg">details</error>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_failure_1" file="/script.py" line="1" time="0.01">')
            file.write('    <system-out>stdout</system-out>')
            file.write('    <system-err>stderr</system-err>')
            file.write('    <failure type="err" message="msg">details</failure>')
            file.write('  </testcase>')
            file.write('  <testcase classname="tests.core.TestCase" name="test_pass_3" file="/script.py" line="1" time="0.01"></testcase>')
            file.write('</testsuite>')

        test_results = build_helper.get_test_results()
        self.assertEqual(test_results.get_num_tests(), 3)
        self.assertEqual(test_results.get_num_passed(), 1)
        self.assertEqual(test_results.get_num_skipped(), 0)
        self.assertEqual(test_results.get_num_errors(), 1)
        self.assertEqual(test_results.get_num_failures(), 1)

        # mock environment
        env = self.construct_environment(build_num=51)
        env.set('CIRCLE_PROJECT_REPONAME', 'test_repo_2')
        env.set('CIRCLE_SHA1', 'yyyyyyyyyyyyyyyyyyyy')
        env.set('CIRCLE_BUILD_NUM', '51')
        env.set('UPSTREAM_REPONAME', 'test_repo')
        env.set('UPSTREAM_BUILD_NUM', '101')

        # requests side effects
        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'status': 'success'},
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'committer_name': 'Test user 2',
                    'committer_email': 'test2@test.com',
                    'commit': 'yyyyyyyyyyyyyyyyyyyy',
                    'subject': 'Test commit 2',
                    'commit_url': 'https://github.com/KarrLab/test_repo_2/commit/yyyyyyyyyyyyyyyyyyyy',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo_2/51',
            },
        })
        requests_get_3 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {
                'all_commit_details': [{
                    'committer_name': 'Test user',
                    'committer_email': 'test@test.com',
                    'commit': 'xxxxxxxxxxxxxxxxxxxx',
                    'subject': 'Test commit',
                    'commit_url': 'https://github.com/KarrLab/test_repo/commit/xxxxxxxxxxxxxxxxxxxx',
                }],
                'build_url': 'https://circleci.com/gh/KarrLab/test_repo/101',
            },
        })

        # mock SMTP
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })

        with env:
            build_helper = self.construct_build_helper(build_num=51)
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_3]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications()
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': True,
                        'is_old_error': False,
                        'is_new_downstream_error': True,
                    })

        # cleanup
        os.remove(filename)

    def test_make_and_archive_reports(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)

        py_v = build_helper.get_python_version()
        shutil.copyfile(
            os.path.join(build_helper.proj_tests_xml_dir, '{0:s}.{1:s}.xml'.format(
                build_helper.proj_tests_xml_latest_filename, py_v)),
            os.path.join(build_helper.proj_tests_xml_dir, '{0:d}.{1:s}.xml'.format(10000000000000001, py_v))
        )
        shutil.copyfile(
            os.path.join(build_helper.proj_tests_xml_dir, '{0:s}.{1:s}.xml'.format(
                build_helper.proj_tests_xml_latest_filename, py_v)),
            os.path.join(build_helper.proj_tests_xml_dir, '{0:d}.{1:s}.xml'.format(10000000000000002, py_v))
        )

        """ test API """
        build_helper.make_and_archive_reports(coverage_dirname=self.coverage_dirname, dry_run=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['make-and-archive-reports', '--coverage-dirname', self.coverage_dirname, '--dry-run']) as app:
                app.run()

    def test_archive_test_report(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)

        """ test API """
        build_helper.archive_test_report()

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['archive-test-report']) as app:
                app.run()

    def test_archive_test_report_no_repo(self):
        build_helper = self.construct_build_helper()
        build_helper.repo_revision = None
        build_helper.archive_test_report()

    def test_archive_test_report_err(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)

        class Result(object):

            def raise_for_status(self):
                return

            def json(self):
                return {'success': False, 'message': 'Error!'}

        with mock.patch.object(requests, 'post', return_value=Result()):
            with self.assertRaisesRegexp(core.BuildHelperError, '^Error uploading report to test history server:'):
                build_helper.archive_test_report()

    def test_combine_coverage_reports(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)
        shutil.move(
            os.path.join(self.coverage_dirname, '.coverage.{}'.format(build_helper.get_python_version())),
            os.path.join(self.coverage_dirname, '.coverage.1'))
        shutil.copyfile(
            os.path.join(self.coverage_dirname, '.coverage.1'),
            os.path.join(self.coverage_dirname, '.coverage.2'))

        """ test API """
        if os.path.isfile(os.path.join(self.coverage_dirname, '.coverage')):
            os.remove(os.path.join(self.coverage_dirname, '.coverage'))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.2')))

        build_helper.combine_coverage_reports(coverage_dirname=self.coverage_dirname)

        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage')))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.2')))

        """ test CLI """
        if os.path.isfile(os.path.join(self.coverage_dirname, '.coverage')):
            os.remove(os.path.join(self.coverage_dirname, '.coverage'))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.2')))

        with self.construct_environment():
            with __main__.App(argv=['combine-coverage-reports', '--coverage-dirname', self.coverage_dirname]) as app:
                app.run()

        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage')))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.coverage_dirname, '.coverage.2')))

    def test_archive_coverage_report(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)

        build_helper.combine_coverage_reports(coverage_dirname=self.coverage_dirname)

        """ test API """
        build_helper.archive_coverage_report(coverage_dirname=self.coverage_dirname, dry_run=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['archive-coverage-report', '--coverage-dirname', self.coverage_dirname, '--dry-run']) as app:
                app.run()

    def test_upload_coverage_report_to_coveralls(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)

        shutil.move(
            os.path.join(self.coverage_dirname, '.coverage.{}'.format(build_helper.get_python_version())),
            os.path.join(self.coverage_dirname, '.coverage'))

        """ test API """
        build_helper.upload_coverage_report_to_coveralls(coverage_dirname=self.coverage_dirname, dry_run=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(
                    argv=['upload-coverage-report-to-coveralls',
                          '--coverage-dirname', self.coverage_dirname,
                          '--dry-run'
                          ]) as app:
                app.run()

    def test_upload_coverage_report_to_code_climate(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(test_path=self.DUMMY_TEST,
                               with_xunit=True,
                               with_coverage=True, coverage_dirname=self.coverage_dirname)

        shutil.move(
            os.path.join(self.coverage_dirname, '.coverage.{}'.format(build_helper.get_python_version())),
            os.path.join(self.coverage_dirname, '.coverage'))

        """ test API """
        with mock.patch.object(CodeClimateRunner, 'run', return_value=0):
            build_helper.upload_coverage_report_to_code_climate(coverage_dirname=self.coverage_dirname)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(
                    argv=['upload-coverage-report-to-code-climate',
                          '--coverage-dirname', self.coverage_dirname,
                          ]) as app:
                with mock.patch.object(CodeClimateRunner, 'run', return_value=0):
                    app.run()

    def test_create_documentation_template(self):
        build_helper = self.construct_build_helper()

        filenames = ['conf.py', 'index.rst', 'overview.rst', 'installation.rst', 'about.rst', 'references.rst', 'references.bib']

        """ test API """
        tempdirname = tempfile.mkdtemp()
        name = os.path.basename(os.path.abspath(tempdirname))

        with open(resource_filename('karr_lab_build_utils', 'templates/setup.cfg'), 'r') as file:
            template = Template(file.read())
        template.stream(name=name).dump(os.path.join(tempdirname, 'setup.cfg'))

        build_helper.create_documentation_template(tempdirname)

        for filename in filenames:
            self.assertTrue(os.path.isfile(os.path.join(tempdirname, build_helper.proj_docs_dir, filename)))

        shutil.rmtree(tempdirname)

        """ test CLI """
        tempdirname = tempfile.mkdtemp()
        name = os.path.basename(os.path.abspath(tempdirname))

        with open(resource_filename('karr_lab_build_utils', 'templates/setup.cfg'), 'r') as file:
            template = Template(file.read())
        template.stream(name=name).dump(os.path.join(tempdirname, 'setup.cfg'))

        with self.construct_environment():
            with __main__.App(argv=['create-documentation-template', '--dirname', tempdirname]) as app:
                app.run()

        for filename in filenames:
            self.assertTrue(os.path.isfile(os.path.join(tempdirname, build_helper.proj_docs_dir, filename)))

        shutil.rmtree(tempdirname)

    def test_create_documentation_template_error(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()
        name = os.path.basename(os.path.abspath(tempdirname))

        parser = configparser.ConfigParser()
        parser.read(resource_filename('karr_lab_build_utils', 'templates/setup.cfg'))
        parser.set('sphinx-apidocs', 'packages', '\npkg_1\npkg_2\n')
        with open(os.path.join(tempdirname, 'setup.cfg'), 'w') as file:
            parser.write(file)

        with self.assertRaisesRegexp(ValueError, '^Sphinx configuration auto-generation only supports'):
            build_helper.create_documentation_template(tempdirname)

        # shutil.rmtree(tempdirname)

    def test_make_documentation(self):
        build_helper = self.construct_build_helper()

        """ test API """
        if os.path.isdir(build_helper.proj_docs_build_html_dir):
            shutil.rmtree(build_helper.proj_docs_build_html_dir)
        if os.path.isdir(build_helper.proj_docs_static_dir):
            shutil.rmtree(build_helper.proj_docs_static_dir)

        build_helper.make_documentation(spell_check=True)

        self.assertTrue(os.path.isfile(os.path.join(build_helper.proj_docs_build_html_dir, 'index.html')))

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['make-documentation']) as app:
                app.run()

    def test_compile_downstream_dependencies(self):
        # create temp directory with temp packages
        packages_parent_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_1'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_2'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_3'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_1', '.circleci'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_2', '.circleci'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_3', '.circleci'))
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_1', 'requirements.txt'), 'w') as file:
            file.write('dep_1\n')
            file.write('git+https://github.com/KarrLab/karr_lab_build_utils.git#egg=karr_lab_build_utils\n')
            file.write('dep_2\n')
        with open(os.path.join(packages_parent_dir, 'pkg_2', 'requirements.txt'), 'w') as file:
            file.write('dep_3\n')
            file.write('dep_4\n')
            file.write('dep_5\n')
        with open(os.path.join(packages_parent_dir, 'pkg_3', 'requirements.txt'), 'w') as file:
            file.write('dep_6\n')
            file.write('dep_7\n')
            file.write('git+https://github.com/KarrLab/karr_lab_build_utils.git#egg=karr_lab_build_utils\n')

        # create temp filename to save dependencies
        tmp_file, downstream_dependencies_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        os.remove(downstream_dependencies_filename)

        # test api
        build_helper = core.BuildHelper()
        deps = build_helper.compile_downstream_dependencies(
            packages_parent_dir=packages_parent_dir,
            downstream_dependencies_filename=downstream_dependencies_filename)
        self.assertEqual(sorted(deps), ['pkg_1', 'pkg_3'])

        with open(downstream_dependencies_filename, 'r') as file:
            self.assertEqual(sorted(yaml.load(file.read())), ['pkg_1', 'pkg_3'])

        with open(os.path.join(packages_parent_dir, 'pkg_1', 'setup.cfg'), 'w') as file:
            file.write('[coverage:run]\n')
            file.write('source = \n')
            file.write('    pkg_1\n')
            file.write('    mod_2\n')
        with self.assertRaisesRegexp(core.BuildHelperError, 'Package should have only one module'):
            deps = build_helper.compile_downstream_dependencies(
                dirname=os.path.join(packages_parent_dir, 'pkg_1'),
                packages_parent_dir=packages_parent_dir,
                downstream_dependencies_filename=downstream_dependencies_filename)

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['compile-downstream-dependencies', '--packages-parent-dir', packages_parent_dir]) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '^The following downstream dependencies were found')
                    self.assertEqual(captured.stderr.get_text(), '')

        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['compile-downstream-dependencies',
                                        '--packages-parent-dir', os.path.join(packages_parent_dir, 'pkg_1')]) as app:
                    app.run()
                    self.assertEqual(captured.stdout.get_text(), 'No downstream packages were found.')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        shutil.rmtree(packages_parent_dir)
        os.remove(downstream_dependencies_filename)

    def test_are_package_dependencies_acyclic(self):
        packages_parent_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_1'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_2'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_3'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_1', '.circleci'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_2', '.circleci'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_3', '.circleci'))
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('- pkg_2\n')
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('- pkg_3\n')
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('[]\n')

        """ Acyclic """

        # test api
        build_helper = core.BuildHelper()
        result = build_helper.are_package_dependencies_acyclic(packages_parent_dir=packages_parent_dir)
        self.assertTrue(result)

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['are-package-dependencies-acyclic',
                                        '--packages-parent-dir', packages_parent_dir]) as app:
                    app.run()
                    self.assertEqual(captured.stdout.get_text(), 'The dependencies are acyclic.')
                    self.assertEqual(captured.stderr.get_text(), '')

        """ cyclic """

        with open(os.path.join(packages_parent_dir, 'pkg_3', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('- pkg_1\n')

        # test api
        build_helper = core.BuildHelper()
        result = build_helper.are_package_dependencies_acyclic(packages_parent_dir=packages_parent_dir)
        self.assertFalse(result)

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['are-package-dependencies-acyclic',
                                        '--packages-parent-dir', packages_parent_dir]) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '^The dependencies are cyclic.')
                    self.assertEqual(captured.stderr.get_text(), '')

        """ Cleanup """
        shutil.rmtree(packages_parent_dir)

    def test_visualize_package_dependencies(self):
        packages_parent_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_1'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_2'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_3'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_1', '.circleci'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_2', '.circleci'))
        os.mkdir(os.path.join(packages_parent_dir, 'pkg_3', '.circleci'))
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.circleci', 'config.yml'), 'w') as file:
            pass
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('- pkg_2\n')
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('- pkg_3\n')
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.circleci', 'downstream_dependencies.yml'), 'w') as file:
            file.write('- pkg_1\n')

        tmp_file, out_filename = tempfile.mkstemp(suffix='.pdf')
        os.close(tmp_file)
        os.remove(out_filename)

        # test api
        build_helper = core.BuildHelper()
        build_helper.visualize_package_dependencies(packages_parent_dir=packages_parent_dir, out_filename=out_filename)
        self.assertTrue(os.path.isfile(out_filename))

        os.remove(out_filename)

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['visualize-package-dependencies',
                                        '--packages-parent-dir', packages_parent_dir,
                                        '--out-filename', out_filename]) as app:
                    app.run()
                    self.assertTrue(os.path.isfile(out_filename))
                    self.assertEqual(captured.stdout.get_text(), '')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        shutil.rmtree(packages_parent_dir)
        os.remove(out_filename)

    def test_trigger_tests_of_downstream_dependencies_no_upstream(self):
        tmp_file, downstream_dependencies_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(downstream_dependencies_filename, 'w') as file:
            yaml.dump(['dep_1', 'dep_2'], file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'all_commit_details': [{'committer_date': '2017-01-01T01:01:01-05:00'}]},
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: [{'build_parameters': [], 'start_time': '2016-01-01T01:01:01.001Z'}],
        })
        requests_post = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: None,
        })

        env = self.construct_environment()

        with env:
            with mock.patch('requests.post', return_value=requests_post):
                # test api
                with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_2]):
                    build_helper = core.BuildHelper()
                    deps = build_helper.trigger_tests_of_downstream_dependencies(
                        downstream_dependencies_filename=downstream_dependencies_filename)
                    self.assertEqual(deps, ['dep_1', 'dep_2'])

                with mock.patch('requests.get', side_effect=[requests_get_1]):
                    deps = build_helper.trigger_tests_of_downstream_dependencies(downstream_dependencies_filename='__junk__')
                    self.assertEqual(deps, [])

                # test cli
                with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_2]):
                    with __main__.App(argv=['trigger-tests-of-downstream-dependencies',
                                            '--downstream-dependencies-filename', downstream_dependencies_filename]) as app:
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '^2 dependent builds were triggered')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        os.remove(downstream_dependencies_filename)

    def test_trigger_tests_of_downstream_dependencies_with_upstream(self):
        tmp_file, downstream_dependencies_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(downstream_dependencies_filename, 'w') as file:
            yaml.dump(['dep_1', 'dep_2'], file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'all_commit_details': [{'committer_date': '2017-01-01T01:01:01-05:00'}]},
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: [
                {
                    'build_parameters':
                    {
                        'UPSTREAM_REPONAME': 'dep_3',
                        'UPSTREAM_BUILD_NUM': '1',
                    },
                    'start_time': '2016-01-01T01:01:01.001Z',
                }
            ],
        })
        requests_post = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: None,
        })

        env = self.construct_environment()
        env.set('UPSTREAM_REPONAME', 'dep_3')
        env.set('UPSTREAM_BUILD_NUM', '1')

        with env:
            with mock.patch('requests.post', return_value=requests_post):
                # test api
                with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_2]):
                    build_helper = core.BuildHelper()
                    deps = build_helper.trigger_tests_of_downstream_dependencies(
                        downstream_dependencies_filename=downstream_dependencies_filename)
                    self.assertEqual(deps, [])

                # test cli
                with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_2]):
                    with __main__.App(argv=['trigger-tests-of-downstream-dependencies',
                                            '--downstream-dependencies-filename', downstream_dependencies_filename]) as app:
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            app.run()
                    self.assertEqual(captured.stdout.get_text(), 'No dependent builds were triggered.')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        os.remove(downstream_dependencies_filename)

    def test_trigger_tests_of_downstream_dependencies_trigger_original_upstream(self):
        tmp_file, downstream_dependencies_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(downstream_dependencies_filename, 'w') as file:
            yaml.dump(['dep_1'], file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'all_commit_details': [{'committer_date': '2017-01-01T01:01:01-05:00'}]},
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: [
                {
                    'build_num': 0,
                    'build_parameters': {},
                    'start_time': '2016-01-01T01:01:01.001Z',
                },
                {
                    'build_num': 1,
                    'build_parameters': {},
                    'start_time': '2016-01-01T01:01:01.001Z',
                },
            ],
        })
        requests_post = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: None,
        })

        env = self.construct_environment()
        env.set('CIRCLE_PROJECT_REPONAME', 'dep_3')
        env.set('UPSTREAM_REPONAME', 'dep_1')
        env.set('UPSTREAM_BUILD_NUM', '1')

        with env:
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
                with mock.patch('requests.post', return_value=requests_post):
                    # test api
                    build_helper = core.BuildHelper()
                    deps = build_helper.trigger_tests_of_downstream_dependencies(
                        downstream_dependencies_filename=downstream_dependencies_filename)
                    self.assertEqual(deps, [])

        # cleanup
        os.remove(downstream_dependencies_filename)

    def test_trigger_tests_of_downstream_dependencies_already_queued(self):
        tmp_file, downstream_dependencies_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(downstream_dependencies_filename, 'w') as file:
            yaml.dump(['pkg_2'], file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'all_commit_details': [{'committer_date': '2017-01-01T01:01:01-05:00'}]},
        })
        requests_get_2 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: [
                {
                    'build_num': 1,
                    'build_parameters': {},
                    'start_time': '2018-01-01T01:01:01.001Z',
                },
            ],
        })
        requests_post = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: None,
        })

        env = self.construct_environment()
        env.set('CIRCLE_PROJECT_REPONAME', 'pkg_1')

        with env:
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
                with mock.patch('requests.post', return_value=requests_post):
                    # test api
                    build_helper = core.BuildHelper()
                    deps = build_helper.trigger_tests_of_downstream_dependencies(
                        downstream_dependencies_filename=downstream_dependencies_filename)
                    self.assertEqual(deps, [])

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'all_commit_details': [{'committer_date': '2019-01-01T01:01:01-05:00'}]},
        })
        with env:
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
                with mock.patch('requests.post', return_value=requests_post):
                    # test api
                    build_helper = core.BuildHelper()
                    deps = build_helper.trigger_tests_of_downstream_dependencies(
                        downstream_dependencies_filename=downstream_dependencies_filename)
                    self.assertEqual(deps, ['pkg_2'])

        # cleanup
        os.remove(downstream_dependencies_filename)

    def test_analyze_package(self):
        # test api
        build_helper = core.BuildHelper()
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            build_helper.analyze_package('karr_lab_build_utils')
            self.assertRegexpMatches(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
            self.assertEqual(captured.stderr.get_text().strip(), 'No config file found, using default configuration')

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['analyze-package', 'karr_lab_build_utils']) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
                    self.assertEqual(captured.stderr.get_text().strip(), 'No config file found, using default configuration')

        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['analyze-package', 'karr_lab_build_utils', '--messages', 'W0611']) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
                    self.assertEqual(captured.stderr.get_text().strip(), 'No config file found, using default configuration')

    def test_find_missing_requirements(self):
        # test api
        build_helper = core.BuildHelper()
        missing = build_helper.find_missing_requirements('karr_lab_build_utils', ignore_files=['karr_lab_build_utils/templates/*'])
        self.assertEqual(missing, [])

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=[
                        'find-missing-requirements', 'karr_lab_build_utils',
                        '--ignore-files', 'karr_lab_build_utils/templates/*']) as app:
                    app.run()
                    self.assertEqual(captured.stdout.get_text(), 'requirements.txt appears to contain all of the dependencies')
                    self.assertEqual(captured.stderr.get_text(), '')

        shutil.copy('requirements.optional.txt', 'requirements.optional.txt.save')
        with open('requirements.optional.txt', 'w') as file:
            pass
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=[
                        'find-missing-requirements', 'karr_lab_build_utils',
                        '--ignore-files', 'karr_lab_build_utils/templates/*']) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), '^The following dependencies should likely be added to')
                    self.assertEqual(captured.stderr.get_text(), '')
        os.remove('requirements.optional.txt')
        os.rename('requirements.optional.txt.save', 'requirements.optional.txt')

    def test_find_unused_requirements(self):
        # test api
        build_helper = core.BuildHelper()
        unused = build_helper.find_unused_requirements('karr_lab_build_utils', ignore_files=['karr_lab_build_utils/templates/*'])
        unused.sort()
        if six.PY3:
            self.assertEqual(unused, ['enum34', 'sphinx_rtd_theme', 'sphinxcontrib_spelling', 'wheel'])
        else:
            self.assertEqual(unused, ['sphinx_rtd_theme', 'sphinxcontrib_spelling', 'wheel'])

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=[
                        'find-unused-requirements', 'karr_lab_build_utils',
                        '--ignore-file', 'karr_lab_build_utils/templates/*']) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(),
                                             '^The following requirements from requirements.txt may not be necessary:\n')
                    self.assertEqual(captured.stderr.get_text(), '')

        os.rename('requirements.txt', 'requirements.txt.save')
        with open('requirements.txt', 'w') as file:
            pass
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=[
                        'find-unused-requirements', 'karr_lab_build_utils',
                        '--ignore-file', 'karr_lab_build_utils/templates/*',
                ]) as app:
                    app.run()
                    self.assertEqual(captured.stdout.get_text(), 'All of the dependencies appear to be necessary')
                    self.assertEqual(captured.stderr.get_text(), '')
        os.remove('requirements.txt')
        os.rename('requirements.txt.save', 'requirements.txt')

    def test_upload_package_to_pypi(self):
        dirname = 'tests/fixtures/karr_lab_build_utils_test_package'

        # get username and password
        filename = 'tests/fixtures/secret/TEST_PYPI_USERNAME'
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                username = file.read()
        else:
            username = os.getenv('TEST_PYPI_USERNAME')

        filename = 'tests/fixtures/secret/TEST_PYPI_PASSWORD'
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                password = file.read()
        else:
            password = os.getenv('TEST_PYPI_PASSWORD')

        if not os.path.isdir('tests/fixtures/secret'):
            os.makedirs('tests/fixtures/secret')
        pypi_config_filename = 'tests/fixtures/secret/.pypirc'
        with open(pypi_config_filename, 'w') as file:
            file.write('[distutils]\n')
            file.write('index-servers =\n')
            file.write('    testpypi\n')
            file.write('\n')
            file.write('[testpypi]\n')
            file.write('repository: https://test.pypi.org/legacy/\n')
            file.write('username: {}\n'.format(username))
            file.write('password: {}\n'.format(password))

        if not os.path.isdir('tests/fixtures/karr_lab_build_utils_test_package/build'):
            os.mkdir('tests/fixtures/karr_lab_build_utils_test_package/build')

        if not os.path.isdir('tests/fixtures/karr_lab_build_utils_test_package/dist'):
            os.mkdir('tests/fixtures/karr_lab_build_utils_test_package/dist')

        # test api
        build_helper = core.BuildHelper()
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            build_helper.upload_package_to_pypi(dirname=dirname, repository='testpypi', pypi_config_filename=pypi_config_filename)
            self.assertRegexpMatches(captured.stdout.get_text(), 'Uploading distributions to https://test\.pypi\.org/legacy/')
            self.assertEqual(captured.stderr.get_text().strip(), '')

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['upload-package-to-pypi',
                                        '--dirname', dirname,
                                        '--repository', 'testpypi',
                                        '--pypi-config-filename', pypi_config_filename]) as app:
                    app.run()
                    self.assertRegexpMatches(captured.stdout.get_text(), 'Uploading distributions to https://test\.pypi\.org/legacy/')
                    self.assertEqual(captured.stderr.get_text().strip(), '')

    def test_get_version(self):
        self.assertIsInstance(karr_lab_build_utils.__init__.__version__, str)

        """ setup """
        build_helper = self.construct_build_helper()

        """ test API """
        build_helper.get_version()

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['get-version']) as app:
                app.run()

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['karr_lab_build_utils', '--help']):
            with self.assertRaises(SystemExit) as context:
                karr_lab_build_utils.__main__.main()
                self.assertRegexpMatches(context.Exception, 'usage: karr_lab_build_utils')

    def test_unsupported_test_runner(self):
        with self.assertRaisesRegexp(Exception, 'Unsupported test runner'):
            env = EnvironmentVarGuard()
            env.set('TEST_RUNNER', 'unsupported')
            with env:
                core.BuildHelper()

    def test_no_build_num(self):
        env = EnvironmentVarGuard()
        env.set('CIRCLE_BUILD_NUM', '')
        with env:
            build_helper = core.BuildHelper()
            self.assertEqual(build_helper.build_num, 0)

    def test_BuildHelperError(self):
        self.assertIsInstance(core.BuildHelperError(), Exception)

    def test_run_method_and_capture_stderr(self):
        build_helper = core.BuildHelper()

        def ok_func(arg1, arg2, arg3=None, arg4=None):
            sys.stdout.write('Success!')
            return 0

        def err_func(arg1, arg2, arg3=None, arg4=None):
            sys.stderr.write('Error!')
            return 1

        with abduct.captured(abduct.out(), abduct.err()) as (stdout, stderr):
            build_helper.run_method_and_capture_stderr(ok_func, '', '', arg3=None)
            self.assertEqual(stdout.getvalue(), 'Success!')
            self.assertEqual(stderr.getvalue(), '')

        with abduct.captured(abduct.out(), abduct.err()) as (stdout, stderr):
            with self.assertRaises(SystemExit):
                build_helper.run_method_and_capture_stderr(err_func, '', '', arg3=None)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), 'Error!')

    def test_dummy_test(self):
        pass
