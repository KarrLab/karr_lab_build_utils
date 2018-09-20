""" Tests karr_lab_build_utils.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-03
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

"""
:todo: Test Docker (:obj:`karr_lab_build_utils.core.BuildHelper._run_tests_docker`) and CircleCI
    (:obj:`karr_lab_build_utils.core.BuildHelper._run_tests_circleci`) within CircleCI. Implementing
    this would require the following changes:

    * Install Docker and CircleCI within the Docker image (i.e. add installation to
      ``karr_lab_docker_images/build/Dockerfile``)
    * Run the Docker image with privileged mode or with socket mounting, e.g.

        * docker run --privileged karrlab/wc_env_dependencies:latest
        * docker run -v /var/run/docker.sock:/var/run/docker.sock karrlab/wc_env_dependencies:latest

        Both of these approaches would require:

            * Changing the executor to ``machine`` in ``.circleci/config.yml``
            * Replicating the functionality provided by CircleCI in ``.circleci/config.yml``.
              This would require adding similar commands to those in
              :obj:`karr_lab_build_utils.core.BuildHelper._run_tests_docker` to ``.circleci/config.yml``.
"""

from glob import glob
from jinja2 import Template
from karr_lab_build_utils import __main__
from karr_lab_build_utils import core
from pkg_resources import resource_filename
from sphinx.application import Sphinx
from six.moves import configparser
import abduct
import attrdict
import base64
import capturer
import ftputil
import git
import github
import imp
import karr_lab_build_utils
import karr_lab_build_utils.__init__
import karr_lab_build_utils.config.core
import mock
import nose
import os
import pip._internal
import pytest
import re
import requests
import shutil
import six
import smtplib
import sys
import tempfile
import time
import unittest
import whichcraft
import yaml

# reload modules to get coverage correct
imp.reload(core)
imp.reload(karr_lab_build_utils)
imp.reload(karr_lab_build_utils.__init__)
imp.reload(karr_lab_build_utils.config.core)
imp.reload(__main__)

if sys.version_info >= (3, 0, 0):
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard


class TestKarrLabBuildUtils(unittest.TestCase):
    COVERALLS_REPO_TOKEN = 'xxx'
    CODECLIMATE_REPO_TOKEN = 'xxx'
    DUMMY_TEST = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__)) + \
        ':TestKarrLabBuildUtils.test_dummy_test'

    def setUp(self):
        self.tmp_dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dirname)

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

        return env

    @staticmethod
    def construct_build_helper(build_num=0):
        with TestKarrLabBuildUtils.construct_environment(build_num=build_num):
            build_helper = core.BuildHelper()

        return build_helper

    def test_create_package(self):
        bh = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        g = github.Github(bh.github_api_token)
        org = g.get_organization('KarrLab')
        for name in ['test_a', 'test_a2', 'test_a_2', 'test_b', 'test_c']:
            try:
                repo = org.get_repo(name)
                repo.delete()
            except github.UnknownObjectException:
                pass

        """ test API """
        # test_a
        name = 'test_a'
        description = 'description_a'
        keywords = ['word_a', 'word_b']
        dependencies = ['__undefined__']
        private = True
        dirname = os.path.join(tempdirname, 'test_a')

        confirm_side_effects = 21 * [True]
        prompt_side_effects = [
            name, description, ', '.join(keywords), ', '.join(dependencies), dirname, '0.0.1',
            'code_climate_repo_token', 'code_climate_repo_id', 'code_climate_repo_badge_token',
            'coveralls_repo_token', 'coveralls_repo_badge_token', 'circleci_repo_token',
        ]
        with mock.patch('click.confirm', side_effect=confirm_side_effects):
            with mock.patch('click.prompt', side_effect=prompt_side_effects):
                with pytest.warns(UserWarning, match='Unable to append package to downstream dependency'):
                    bh.create_package()

        self.assertTrue(os.path.isdir(os.path.join(tempdirname, name, '.git')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, name, 'README.md')))

        config_filename = os.path.join(tempdirname, name, '.karr_lab_build_utils.yml')
        with open(config_filename, 'r') as file:
            self.assertEqual(yaml.load(file)['downstream_dependencies'], [])

        repo = org.get_repo(name)
        self.assertEqual(repo.description, description)

        with ftputil.FTPHost(bh.code_server_hostname, bh.code_server_username, bh.code_server_password) as ftp:
            remote_filename = ftp.path.join(bh.code_server_directory, '{}.json'.format(name))
            self.assertTrue(ftp.path.isfile(remote_filename))

        # test_b
        name = 'test_b'
        description = 'description_b'
        keywords = ['word_a', 'word_b']
        dependencies = ['test_a', 'karr_lab_website']
        private = False
        dirname = os.path.join(tempdirname, 'test_b')

        confirm_side_effects = [True, False] + 32 * [True]
        prompt_side_effects = [
            name, description, ', '.join(keywords), ', '.join(dependencies), dirname, '0.0.1',
            'code_climate_repo_token', 'code_climate_repo_badge_token',
            'coveralls_repo_token',
        ]

        config_filename = os.path.join(tempdirname, 'test_a', '.karr_lab_build_utils.yml')
        with open(config_filename, 'w') as file:
            file.write('{}')

        with mock.patch('click.confirm', side_effect=confirm_side_effects):
            with mock.patch('click.prompt', side_effect=prompt_side_effects):
                bh.create_package()

        self.assertTrue(os.path.isdir(os.path.join(tempdirname, name, '.git')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, name, 'README.md')))

        config_filename = os.path.join(tempdirname, 'test_a', '.karr_lab_build_utils.yml')
        with open(config_filename, 'r') as file:
            self.assertEqual(yaml.load(file)['downstream_dependencies'], ['test_b'])

        config_filename = os.path.join(tempdirname, 'test_b', '.karr_lab_build_utils.yml')
        with open(config_filename, 'r') as file:
            self.assertEqual(yaml.load(file)['downstream_dependencies'], [])

        repo = org.get_repo(name)
        self.assertEqual(repo.description, description)

        with ftputil.FTPHost(bh.code_server_hostname, bh.code_server_username, bh.code_server_password) as ftp:
            remote_filename = ftp.path.join(bh.code_server_directory, '{}.json'.format(name))
            self.assertTrue(ftp.path.isfile(remote_filename))

        """ test CLI """
        name = 'test_c'
        description = 'description_c'
        keywords = ['keyword_a', 'keyword_b']
        dependencies = ['test_b']
        private = False
        dirname = os.path.join(tempdirname, 'test_c')

        with self.construct_environment():
            with __main__.App(argv=['create-package']) as app:
                confirm_side_effects = [True, False] + 29 * [True]
                prompt_side_effects = [
                    name, description, ', '.join(keywords), ', '.join(dependencies), dirname, '0.0.1',
                    'code_climate_repo_token', 'code_climate_repo_badge_token',
                    'coveralls_repo_token',
                ]
                with mock.patch('click.confirm', side_effect=confirm_side_effects):
                    with mock.patch('click.prompt', side_effect=prompt_side_effects):
                        app.run()

        self.assertTrue(os.path.isdir(os.path.join(tempdirname, name, '.git')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, name, 'README.md')))

        config_filename = os.path.join(tempdirname, name, '.karr_lab_build_utils.yml')
        with open(config_filename, 'r') as file:
            self.assertEqual(yaml.load(file)['downstream_dependencies'], [])

        repo = org.get_repo(name)
        self.assertEqual(repo.description, description)

        with ftputil.FTPHost(bh.code_server_hostname, bh.code_server_username, bh.code_server_password) as ftp:
            remote_filename = ftp.path.join(bh.code_server_directory, '{}.json'.format(name))
            self.assertTrue(ftp.path.isfile(remote_filename))

        """ cleanup """
        g = github.Github(bh.github_api_token)
        org = g.get_organization('KarrLab')
        for name in ['test_a', 'test_b', 'test_c']:
            repo = org.get_repo(name)
            repo.delete()

        with ftputil.FTPHost(bh.code_server_hostname, bh.code_server_username, bh.code_server_password) as ftp:
            remote_filename = ftp.path.join(bh.code_server_directory, '{}.json'.format('test_a'))
            ftp.remove(remote_filename)

            remote_filename = ftp.path.join(bh.code_server_directory, '{}.json'.format('test_b'))
            ftp.remove(remote_filename)

            remote_filename = ftp.path.join(bh.code_server_directory, '{}.json'.format('test_c'))
            ftp.remove(remote_filename)

        shutil.rmtree(tempdirname)

    def test_create_repository(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        g = github.Github(build_helper.github_api_token)
        org = g.get_organization('KarrLab')
        for name in ['test_a', 'test_a2', 'test_a_2', 'test_b']:
            try:
                repo = org.get_repo(name)
                repo.delete()
            except github.UnknownObjectException:
                pass

        """ test API """
        # test valid repo names
        build_helper.create_repository('test_a', dirname=os.path.join(tempdirname, 'test_a'))
        build_helper.create_repository('test_a2', dirname=os.path.join(tempdirname, 'test_a2'))
        build_helper.create_repository('test_a_2', dirname=os.path.join(tempdirname, 'test_a_2'))
        self.assertRaises(core.BuildHelperError, build_helper.create_repository, '2')
        self.assertRaises(core.BuildHelperError, build_helper.create_repository, 'test-a-')

        # check files create correctly
        self.assertTrue(os.path.isdir(os.path.join(tempdirname, 'test_a', '.git')))

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['create-repository', 'test_b', '--dirname', os.path.join(tempdirname, 'test_b')]) as app:
                app.run()

        self.assertTrue(os.path.isdir(os.path.join(tempdirname, 'test_b', '.git')))

        """ cleanup """
        g = github.Github(build_helper.github_api_token)
        org = g.get_organization('KarrLab')
        for name in ['test_a', 'test_a2', 'test_a_2', 'test_b']:
            repo = org.get_repo(name)
            repo.delete()

        shutil.rmtree(tempdirname)

    def test_setup_repository(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()

        """ test API """
        # test valid repo names
        build_helper.setup_repository('a', dirname=os.path.join(tempdirname, 'a'), keywords=['abc', 'def'], dependencies=['b', 'c'])
        build_helper.setup_repository('a2', dirname=os.path.join(tempdirname, 'a2'))
        build_helper.setup_repository('a_2', dirname=os.path.join(tempdirname, 'a_2'))
        self.assertRaises(core.BuildHelperError, build_helper.setup_repository, '2')
        self.assertRaises(core.BuildHelperError, build_helper.setup_repository, 'a-')

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
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'a', 'core.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'a', '__main__.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'tests', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'tests', 'test_core.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'tests', 'test_main.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'conf.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', 'docs', 'spelling_wordlist.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.circleci', 'config.yml')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'a', '.karr_lab_build_utils.yml')))

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['setup-repository', 'b',
                                    '--dirname', os.path.join(tempdirname, 'b'),
                                    '--keyword', 'abc',
                                    '--keyword', 'def',
                                    '--dependency', 'b',
                                    '--dependency', 'c',
                                    ]) as app:
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
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'b', 'core.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'b', '__main__.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'tests', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'tests', 'test_core.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'tests', 'test_main.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'conf.py')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'requirements.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', 'docs', 'spelling_wordlist.txt')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.circleci', 'config.yml')))
        self.assertTrue(os.path.isfile(os.path.join(tempdirname, 'b', '.karr_lab_build_utils.yml')))

        """ cleanup """
        shutil.rmtree(tempdirname)

    def test_follow_circleci_build(self):
        """ test API """
        with self.construct_environment():
            build_helper = self.construct_build_helper()
        build_helper.follow_circleci_build(has_private_dependencies=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['follow-circleci-build']) as app:
                app.run()

    def test_follow_circleci_build_error(self):
        with self.construct_environment():
            build_helper = self.construct_build_helper()

        class Result(object):

            def raise_for_status(self):
                return

            def json(self):
                return {'following': False}

        with mock.patch.object(requests, 'post', return_value=Result()):
            with self.assertRaisesRegex(ValueError, '^Unable to follow CircleCI build for repository'):
                build_helper.follow_circleci_build()

    def test_get_circleci_environment_variables(self):
        """ test API """
        with self.construct_environment():
            build_helper = self.construct_build_helper()

        vars = build_helper.get_circleci_environment_variables()
        self.assertTrue('COVERALLS_REPO_TOKEN' in vars)
        self.assertTrue('CODECLIMATE_REPO_TOKEN' in vars)

        """ test CLI """
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['get-circleci-environment-variables']) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(), 'COVERALLS_REPO_TOKEN=')
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
                    self.assertRegex(captured.stdout.get_text(), '__TEST1__=xxxxe 1c')
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

    def test_create_code_climate_github_webhook(self):
        build_helper = self.construct_build_helper()

        """ test API """
        try:
            build_helper.create_code_climate_github_webhook()
        except ValueError as err:
            pass

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['create-code-climate-github-webhook']) as app:
                try:
                    app.run()
                except ValueError as err:
                    pass

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

    def test_upgrade_karr_lab_packages(self):
        build_helper = self.construct_build_helper()

        """ test API """
        build_helper.upgrade_karr_lab_packages()

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['upgrade-karr-lab-packages']) as app:
                app.run()

    def test_upgrade_requirements_karr_lab_reqs(self):
        freeze = [
            '-e git+https://github.com/KarrLab/pkg1.git@commit#egg=pkg1',
            'pkg2==0.0.2',
            'pkg3==0.0.3',
            'pkg4==0.0.4',
            'pkg5==0.0.5',
        ]

        show = [
            [{'name': 'pkg2', 'home-page': 'pypi'}],
            [{'name': 'pkg3', 'home-page': 'https://github.com/KarrLab/pkg3'}],
            [{'name': 'pkg4', 'home-page': 'pypi'}],
            [{'name': 'pkg5', 'home-page': 'https://github.com/KarrLab/pkg5'}],
        ]

        with mock.patch('subprocess.check_call', return_value=None):
            with mock.patch('pip._internal.commands.show.search_packages_info', side_effect=show):
                with mock.patch('pip._internal.operations.freeze.freeze', return_value=freeze):
                    build_helper = self.construct_build_helper()
                    reqs = build_helper.upgrade_karr_lab_packages()
        self.assertEqual(reqs, ['git+https://github.com/KarrLab/pkg3.git#egg=pkg3[all]',
                                'git+https://github.com/KarrLab/pkg5.git#egg=pkg5[all]'])

    def test_run_tests(self):
        self.help_run('pytest', coverage_type=core.CoverageType.branch)
        self.help_run('nose', coverage_type=core.CoverageType.branch)
        with self.assertRaisesRegex(core.BuildHelperError, '^Unsupported coverage type: '):
            self.help_run('pytest', coverage_type=core.CoverageType.multiple_condition)

    def help_run(self, test_runner, coverage_type=core.CoverageType.branch):
        build_helper = self.construct_build_helper()
        build_helper.test_runner = test_runner
        py_v = build_helper.get_python_version()

        tempdirname = tempfile.mkdtemp()
        shutil.rmtree(tempdirname)
        build_helper.proj_tests_xml_dir = tempdirname

        """ test API """
        latest_results_filename = os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
            build_helper.proj_tests_xml_latest_filename, 0, 1, py_v))
        lastest_cov_filename = os.path.join(self.tmp_dirname, '.coverage.{}-{}.{}'.format(0, 1, py_v))
        if os.path.isdir(build_helper.proj_tests_xml_dir):
            shutil.rmtree(build_helper.proj_tests_xml_dir)
        if os.path.isfile(latest_results_filename):
            os.remove(latest_results_filename)
        if os.path.isfile(lastest_cov_filename):
            os.remove(lastest_cov_filename)

        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname,
            coverage_type=coverage_type)

        self.assertTrue(os.path.isfile(latest_results_filename))
        self.assertTrue(os.path.isfile(lastest_cov_filename))

        """ test CLI """
        argv = [
            'run-tests',
            '--test-path', self.DUMMY_TEST,
            '--with-xunit',
            '--with-coverage', '--coverage-dirname', tempdirname,
        ]
        with self.construct_environment():
            with __main__.App(argv=argv) as app:
                app.run()
                self.assertEqual(self.DUMMY_TEST, app.pargs.test_path)
                self.assertTrue(app.pargs.with_xunit)
                self.assertTrue(app.pargs.with_coverage)

        shutil.rmtree(tempdirname)

    @unittest.skip('Todo')
    def test_run_tests_multiple_workers(self):
        pass

    def test_run_tests_default_path(self):
        with self.construct_environment():
            with __main__.App(argv=['run-tests']) as app:
                with mock.patch.object(core.BuildHelper, 'run_tests', return_value=None):
                    app.run()

    def test_run_tests_with_test_path_env_var(self):
        env = self.construct_environment()
        env.set('test_path', self.DUMMY_TEST)
        with env:
            with __main__.App(argv=['run-tests']) as app:
                app.run()

    def test_run_tests_with_verbose(self):
        build_helper = self.construct_build_helper()

        build_helper.test_runner = 'pytest'
        build_helper.run_tests(test_path=self.DUMMY_TEST, verbose=True)

        build_helper.test_runner = 'nose'
        build_helper.run_tests(test_path=self.DUMMY_TEST, verbose=True)

    def test_run_tests_error(self):
        build_helper = self.construct_build_helper()

        tempdirname = tempfile.mkdtemp()
        shutil.rmtree(tempdirname)
        build_helper.proj_tests_xml_dir = tempdirname

        build_helper.test_runner = 'unsupported_runner'
        with self.assertRaisesRegex(core.BuildHelperError, '^Unsupported test runner'):
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

    def test__get_test_cases(self):
        build_helper = self.construct_build_helper()

        dummy_test_case = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__)) + \
            '::TestKarrLabBuildUtils::test_dummy_test'

        self.assertEqual(
            build_helper._get_test_cases(test_path=dummy_test_case, n_workers=1, i_worker=0),
            [dummy_test_case])
        self.assertEqual(
            build_helper._get_test_cases(test_path=dummy_test_case, n_workers=2, i_worker=0),
            [dummy_test_case])
        self.assertEqual(
            build_helper._get_test_cases(test_path=dummy_test_case, n_workers=2, i_worker=1),
            [])

        test_cases = [
            'tests/test_api.py::ApiTestCase',
            'tests/test_core.py::TestCircleCi',
            'tests/test_core.py::TestKarrLabBuildUtils',
        ]
        self.assertEqual(
            build_helper._get_test_cases(test_path='tests', n_workers=1, i_worker=0),
            test_cases)
        self.assertEqual(
            build_helper._get_test_cases(test_path='tests', n_workers=2, i_worker=0),
            [test_cases[0], test_cases[2]])
        self.assertEqual(
            build_helper._get_test_cases(test_path='tests', n_workers=2, i_worker=1),
            [test_cases[1]])
        self.assertEqual(
            build_helper._get_test_cases(test_path='tests', n_workers=4, i_worker=3, with_xunit=True),
            [])

        with self.assertRaisesRegex(core.BuildHelperError, 'less than'):
            build_helper._get_test_cases(n_workers=1, i_worker=1)

    def test_docker_help(self):
        with __main__.App(argv=['docker']) as app:
            app.run()

    @unittest.skipIf(whichcraft.which('docker') is None, (
        'Test requires Docker and Docker isn''t installed. '
        'See installation instructions at `https://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html`'
    ))
    def test_low_level_docker_commands(self):
        with capturer.CaptureOutput(merged=False, relay=True) as captured:
            with __main__.App(argv=['docker', 'create-container']) as app:
                app.run()
                stdout = captured.stdout.get_text()
                self.assertRegex(stdout, ('Created Docker container (build[\-0-9]+) with volume (build[\-0-9]+)'))
        match = re.search('Created Docker container (build[\-0-9]+) ', stdout, re.IGNORECASE)
        container = match.group(1)

        with __main__.App(argv=['docker', 'install-package-to-container', container]) as app:
            app.run()

        with __main__.App(argv=['docker', 'run-tests-in-container', container, '--test-path', self.DUMMY_TEST]) as app:
            app.run()

        with __main__.App(argv=['docker', 'remove-container', container]) as app:
            app.run()

    @unittest.skipIf(whichcraft.which('docker') is None, (
        'Test requires Docker and Docker isn''t installed. '
        'See installation instructions at `https://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html`'
    ))
    def test_run_tests_docker(self):
        if not os.path.isdir('tests/__pycache__'):
            os.mkdir(os.path.join('tests/__pycache__'))

        build_helper = self.construct_build_helper()
        build_helper.proj_tests_xml_dir = self.tmp_dirname

        # test success
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname,
            environment=core.Environment.docker, verbose=True)

        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])
        self.assertEqual(len(list(glob(os.path.join(
            self.tmp_dirname, '.coverage.{}-{}.{}.*'.format(0, 1, py_v))))), 1)
        self.assertEqual(len(list(glob(os.path.join(
            self.tmp_dirname, '{}.{}-{}.{}.*.xml'.format(build_helper.proj_tests_xml_latest_filename, 0, 1, py_v))))), 1)

        # :todo: test failure

    @unittest.skipIf(whichcraft.which('docker') is None, (
        'Test requires Docker and Docker isn''t installed. '
        'See installation instructions at `https://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html`'
    ))
    def test__run_docker_command_capture_stdout(self):
        build_helper = self.construct_build_helper()
        with capturer.CaptureOutput(merged=False, relay=False) as capture_output:
            out = build_helper._run_docker_command(['images'])
            self.assertRegex(out, '^REPOSITORY')
            self.assertEqual(capture_output.stdout.get_text(), '')

    @unittest.skipIf(whichcraft.which('docker') is None, (
        'Test requires Docker and Docker isn''t installed. '
        'See installation instructions at `https://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html`'
    ))
    def test__run_docker_command_exception(self):
        build_helper = self.construct_build_helper()
        with self.assertRaisesRegex(core.BuildHelperError, 'is not a docker command'):
            build_helper._run_docker_command(['XXXXX'])

    def test_run_tests_unsupported_env(self):
        build_helper = self.construct_build_helper()
        with self.assertRaisesRegex(core.BuildHelperError, '^Unsupported environment:'):
            build_helper.run_tests(test_path=self.DUMMY_TEST, environment=None)

    def test_do_post_test_tasks(self):
        down_pkgs_return = []
        notify_return = {
            'is_fixed': False,
            'is_old_error': False,
            'is_new_error': False,
            'is_other_error': False,
            'is_new_downstream_error': False,
        }
        with mock.patch.object(core.BuildHelper, 'make_and_archive_reports', return_value=None):
            with mock.patch.object(core.BuildHelper, 'trigger_tests_of_downstream_dependencies', return_value=down_pkgs_return):
                with mock.patch.object(core.BuildHelper, 'send_email_notifications', return_value=notify_return):
                    # test api
                    build_helper = self.construct_build_helper()
                    build_helper.do_post_test_tasks(False, False)

                    # test cli
                    with self.construct_environment():
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            with __main__.App(argv=['do-post-test-tasks', '0', '0']) as app:
                                app.run()

                                time.sleep(0.1)

                                self.assertEqual(app.pargs.installation_exit_code, 0)
                                self.assertEqual(app.pargs.tests_exit_code, 0)
                                self.assertRegex(captured.stdout.get_text(), 'No downstream builds were triggered.')
                                self.assertRegex(captured.stdout.get_text(), 'No notifications were sent.')
                                self.assertEqual(captured.stderr.get_text(), '')

        down_pkgs_return = ['pkg_1', 'pkg_2']
        notify_return = {
            'is_fixed': True,
            'is_old_error': True,
            'is_new_error': True,
            'is_other_error': True,
            'is_new_downstream_error': True,
        }
        with mock.patch.object(core.BuildHelper, 'make_and_archive_reports', return_value=None):
            with mock.patch.object(core.BuildHelper, 'trigger_tests_of_downstream_dependencies', return_value=down_pkgs_return):
                with mock.patch.object(core.BuildHelper, 'send_email_notifications', return_value=notify_return):
                    with self.construct_environment():
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            with __main__.App(argv=['do-post-test-tasks', '0', '1']) as app:
                                with self.assertRaisesRegex(core.BuildHelperError, 'Post-test tasks were not successful'):
                                    app.run()
                                self.assertEqual(app.pargs.installation_exit_code, 0)
                                self.assertEqual(app.pargs.tests_exit_code, 1)
                                self.assertRegex(captured.stdout.get_text(), '2 downstream builds were triggered')
                                self.assertRegex(captured.stdout.get_text(), '  pkg_1')
                                self.assertRegex(captured.stdout.get_text(), '  pkg_2')
                                self.assertRegex(captured.stdout.get_text(), '5 notifications were sent')
                                self.assertRegex(captured.stdout.get_text(), '  Build fixed')
                                self.assertRegex(captured.stdout.get_text(), '  Recurring error')
                                self.assertRegex(captured.stdout.get_text(), '  New error')
                                self.assertRegex(captured.stdout.get_text(), '  Other error')
                                self.assertRegex(captured.stdout.get_text(), '  Downstream error')
                                self.assertEqual(captured.stderr.get_text(), '')

        def make_and_archive_reports():
            raise Exception()
        down_pkgs_return = []
        notify_return = {
            'is_fixed': False,
            'is_old_error': False,
            'is_new_error': False,
            'is_other_error': True,
            'is_new_downstream_error': False,
        }
        smtp = attrdict.AttrDict({
            'ehlo': lambda: None,
            'starttls': lambda: None,
            'login': lambda user, pwd: None,
            'sendmail': lambda from_addr, to_addrs, msg: None,
            'quit': lambda: None,
        })
        with mock.patch.object(core.BuildHelper, 'make_and_archive_reports', make_and_archive_reports):
            with mock.patch.object(core.BuildHelper, 'trigger_tests_of_downstream_dependencies', return_value=down_pkgs_return):
                with mock.patch.object(core.BuildHelper, 'send_email_notifications', return_value=notify_return):
                    with mock.patch('smtplib.SMTP', return_value=smtp):
                        with self.construct_environment():
                            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                                with __main__.App(argv=['do-post-test-tasks', '0', '0']) as app:
                                    with self.assertRaisesRegex(core.BuildHelperError, 'Post-test tasks were not successful'):
                                        app.run()
                                    self.assertRegex(captured.stdout.get_text(), '1 notifications were sent')
                                    self.assertRegex(captured.stdout.get_text(), '  Other error')
                                    self.assertEqual(captured.stderr.get_text(), '')

    def test_get_test_results(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{0}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{0}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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
        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }

        with self.construct_environment(build_num=1):
            build_helper = self.construct_build_helper(build_num=1)
            with mock.patch('requests.get', side_effect=[requests_get_1]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications(False, False, False, static_analyses)
                    self.assertEqual(result, {
                        'is_fixed': True,
                        'is_new_error': False,
                        'is_old_error': False,
                        'is_other_error': False,
                        'is_new_downstream_error': False,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_fixed(self):
        build_helper = self.construct_build_helper(build_num=10)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{0}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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
        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }

        with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
            with mock.patch('smtplib.SMTP', return_value=smtp):
                result = build_helper.send_email_notifications(False, False, False, static_analyses)
                self.assertEqual(result, {
                    'is_fixed': True,
                    'is_new_error': False,
                    'is_old_error': False,
                    'is_other_error': False,
                    'is_new_downstream_error': False,
                })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_no_upstream(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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
        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }

        with mock.patch('requests.get', side_effect=[requests_get_1]):
            with mock.patch('smtplib.SMTP', return_value=smtp):
                result = build_helper.send_email_notifications(False, False, False, static_analyses)
                self.assertEqual(result, {
                    'is_fixed': False,
                    'is_new_error': True,
                    'is_old_error': False,
                    'is_other_error': False,
                    'is_new_downstream_error': False,
                })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_no_previous_builds(self):
        build_helper = self.construct_build_helper(build_num=1)

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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
        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }

        with mock.patch('requests.get', side_effect=[requests_get_1]):
            with mock.patch('smtplib.SMTP', return_value=smtp):
                with env:
                    build_helper = self.construct_build_helper(build_num=1)
                    result = build_helper.send_email_notifications(False, False, False, static_analyses)
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': True,
                        'is_old_error': False,
                        'is_other_error': False,
                        'is_new_downstream_error': False,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_existing_error(self):
        build_helper = self.construct_build_helper()

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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
        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': [],
        }

        with env:
            build_helper = self.construct_build_helper(build_num=51)
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications(False, False, False, static_analyses)
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': False,
                        'is_old_error': True,
                        'is_other_error': False,
                        'is_new_downstream_error': False,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_tests_exit_code_failure(self):
        build_helper = self.construct_build_helper()

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

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
        env = self.construct_environment(build_num=51)
        env.set('CIRCLE_PROJECT_REPONAME', 'test_repo_2')
        env.set('CIRCLE_SHA1', 'yyyyyyyyyyyyyyyyyyyy')
        env.set('CIRCLE_BUILD_NUM', '51')
        env.set('UPSTREAM_REPONAME', 'test_repo')
        env.set('UPSTREAM_BUILD_NUM', '101')

        # test API
        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }

        with env:
            build_helper = self.construct_build_helper(build_num=51)
            with mock.patch('requests.get', side_effect=[requests_get_1]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications(False, True, False, static_analyses)
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': False,
                        'is_old_error': False,
                        'is_other_error': True,
                        'is_new_downstream_error': False,
                    })

    def test_send_email_notifications_send_email(self):
        build_helper = self.construct_build_helper()

        # mock test results
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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

        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }

        with env:
            build_helper = self.construct_build_helper(build_num=51)
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_3]):
                with mock.patch('smtplib.SMTP', return_value=smtp):
                    result = build_helper.send_email_notifications(False, False, False, static_analyses)
                    self.assertEqual(result, {
                        'is_fixed': False,
                        'is_new_error': True,
                        'is_old_error': False,
                        'is_other_error': False,
                        'is_new_downstream_error': True,
                    })

        # cleanup
        os.remove(filename)

    def test_send_email_notifications_dry_run(self):
        build_helper = self.construct_build_helper()

        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        static_analyses = {
            'missing_requirements': [('missing_1',), ('missing_2',)],
            'unused_requirements': ['unused_1', 'unused_2'],
        }
        result = build_helper.send_email_notifications(False, False, False, static_analyses, dry_run=True)
        self.assertEqual(result, {
            'is_fixed': False,
            'is_new_error': False,
            'is_old_error': False,
            'is_other_error': False,
            'is_new_downstream_error': False,
        })

    def test_make_and_archive_reports(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

        py_v = build_helper.get_python_version()
        shutil.copyfile(
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                build_helper.proj_tests_xml_latest_filename, 0, 1, py_v)),
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                10000000000000001, 0, 1, py_v))
        )
        shutil.copyfile(
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                build_helper.proj_tests_xml_latest_filename, 0, 1, py_v)),
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                10000000000000002, 0, 1, py_v))
        )

        """ test API """
        build_helper.make_and_archive_reports(coverage_dirname=self.tmp_dirname, dry_run=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['make-and-archive-reports', '--coverage-dirname', self.tmp_dirname, '--dry-run']) as app:
                app.run()

    def test_make_and_archive_reports_with_missing_req(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

        py_v = build_helper.get_python_version()
        shutil.copyfile(
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                build_helper.proj_tests_xml_latest_filename, 0, 1, py_v)),
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                10000000000000001, 0, 1, py_v))
        )
        shutil.copyfile(
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                build_helper.proj_tests_xml_latest_filename, 0, 1, py_v)),
            os.path.join(build_helper.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                10000000000000002, 0, 1, py_v))
        )

        shutil.copy('requirements.txt', 'requirements.txt.save')
        with open('requirements.txt', 'w') as file:
            pass
        try:
            with self.assertRaisesRegex(core.BuildHelperError, 'The following requirements are missing:\n  '):
                warning = 'The following requirements appear to be unused:\n  sphinxcontrib_googleanalytics'
                with pytest.warns(UserWarning, match=warning):
                    build_helper.make_and_archive_reports(coverage_dirname=self.tmp_dirname, dry_run=True)
        finally:
            os.remove('requirements.txt')
            os.rename('requirements.txt.save', 'requirements.txt')

    def test_archive_test_report(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

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
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

        class Result(object):

            def raise_for_status(self):
                return

            def json(self):
                return {'success': False, 'message': 'Error!'}

        with mock.patch.object(requests, 'post', return_value=Result()):
            with self.assertRaisesRegex(core.BuildHelperError, '^Error uploading report to test history server:'):
                build_helper.archive_test_report()

    def test_combine_coverage_reports(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)
        shutil.move(
            os.path.join(self.tmp_dirname, '.coverage.0-1.{}'.format(build_helper.get_python_version())),
            os.path.join(self.tmp_dirname, '.coverage.0-1.1'))
        shutil.copyfile(
            os.path.join(self.tmp_dirname, '.coverage.0-1.1'),
            os.path.join(self.tmp_dirname, '.coverage.0-1.2'))

        """ test API """
        if os.path.isfile(os.path.join(self.tmp_dirname, '.coverage')):
            os.remove(os.path.join(self.tmp_dirname, '.coverage'))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.2')))

        build_helper.combine_coverage_reports(coverage_dirname=self.tmp_dirname)

        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.2')))

        """ test CLI """
        if os.path.isfile(os.path.join(self.tmp_dirname, '.coverage')):
            os.remove(os.path.join(self.tmp_dirname, '.coverage'))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.2')))

        with self.construct_environment():
            with __main__.App(argv=['combine-coverage-reports', '--coverage-dirname', self.tmp_dirname]) as app:
                app.run()

        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.1')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dirname, '.coverage.0-1.2')))

    def test_combine_coverage_reports_no_files(self):
        build_helper = self.construct_build_helper()

        self.assertEqual(glob(os.path.join(self.tmp_dirname, '.coverage.*-*.*')), [])

        with pytest.warns(UserWarning, match='No coverage files exist to combine'):
            build_helper.combine_coverage_reports(coverage_dirname=self.tmp_dirname)

    def test_archive_coverage_report(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

        build_helper.combine_coverage_reports(coverage_dirname=self.tmp_dirname)

        """ test API """
        build_helper.archive_coverage_report(coverage_dirname=self.tmp_dirname, dry_run=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['archive-coverage-report', '--coverage-dirname', self.tmp_dirname, '--dry-run']) as app:
                app.run()

    def test_upload_coverage_report_to_coveralls(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

        shutil.move(
            os.path.join(self.tmp_dirname, '.coverage.{}-{}.{}'.format(0, 1, build_helper.get_python_version())),
            os.path.join(self.tmp_dirname, '.coverage'))

        """ test API """
        build_helper.upload_coverage_report_to_coveralls(coverage_dirname=self.tmp_dirname, dry_run=True)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(
                    argv=['upload-coverage-report-to-coveralls',
                          '--coverage-dirname', self.tmp_dirname,
                          '--dry-run'
                          ]) as app:
                app.run()

    def test_upload_coverage_report_to_coveralls_no_coverage_files(self):
        build_helper = self.construct_build_helper()

        self.assertEqual(glob(os.path.join(self.tmp_dirname, '.coverage')), [])

        with pytest.warns(UserWarning, match='No coverage file exists to upload to Coveralls'):
            build_helper.upload_coverage_report_to_coveralls(coverage_dirname=self.tmp_dirname)

    def test_upload_coverage_report_to_code_climate(self):
        build_helper = self.construct_build_helper()
        build_helper.run_tests(
            test_path=self.DUMMY_TEST,
            with_xunit=True,
            with_coverage=True, coverage_dirname=self.tmp_dirname)

        shutil.move(
            os.path.join(self.tmp_dirname, '.coverage.{}-{}.{}'.format(0, 1, build_helper.get_python_version())),
            os.path.join(self.tmp_dirname, '.coverage'))

        """ test API """
        with mock.patch('subprocess.check_call', return_value=None):
            build_helper.upload_coverage_report_to_code_climate(coverage_dirname=self.tmp_dirname)

        """ test CLI """
        with self.construct_environment():
            with __main__.App(
                    argv=['upload-coverage-report-to-code-climate',
                          '--coverage-dirname', self.tmp_dirname,
                          ]) as app:
                with mock.patch('subprocess.check_call', return_value=None):
                    app.run()

    def test_upload_coverage_report_to_code_climate_no_coverage_files(self):
        build_helper = self.construct_build_helper()

        self.assertEqual(glob(os.path.join(self.tmp_dirname, '.coverage')), [])

        with pytest.warns(UserWarning, match='No coverage file exists to upload to Code Climate'):
            build_helper.upload_coverage_report_to_code_climate(coverage_dirname=self.tmp_dirname)

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

        with self.assertRaisesRegex(ValueError, '^Sphinx configuration auto-generation only supports'):
            build_helper.create_documentation_template(tempdirname)

        shutil.rmtree(tempdirname)

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

    def test_make_documentation_error(self):
        build_helper = self.construct_build_helper()

        """ test API """
        if os.path.isdir(build_helper.proj_docs_build_html_dir):
            shutil.rmtree(build_helper.proj_docs_build_html_dir)
        if os.path.isdir(build_helper.proj_docs_static_dir):
            shutil.rmtree(build_helper.proj_docs_static_dir)

        with self.assertRaises(SystemExit):
            with mock.patch.object(Sphinx, '__init__', side_effect=Exception('Test exception')):
                build_helper.make_documentation()

    def test_upload_documentation_to_docs_server(self):
        bh = self.construct_build_helper()
        bh.repo_name = 'test_repo'
        bh.repo_branch = 'master'
        repo_version = '0.0.1a'

        os.makedirs(os.path.join(self.tmp_dirname, bh.repo_name))
        with open(os.path.join(self.tmp_dirname, bh.repo_name, 'VERSION'), 'w') as file:
            file.write(repo_version)

        os.makedirs(os.path.join(self.tmp_dirname, bh.proj_docs_build_html_dir))
        os.makedirs(os.path.join(self.tmp_dirname, bh.proj_docs_build_html_dir, 'a', 'b', 'c'))
        with open(os.path.join(self.tmp_dirname, bh.proj_docs_build_html_dir, 'index.html'), 'w') as file:
            file.write('Test documentation')
        with open(os.path.join(self.tmp_dirname, bh.proj_docs_build_html_dir, 'a', 'b', 'c', 'index.html'), 'w') as file:
            file.write('Test!')

        bh.upload_documentation_to_docs_server(dirname=self.tmp_dirname)

        with ftputil.FTPHost(bh.docs_server_hostname, bh.docs_server_username, bh.docs_server_password) as ftp:
            # check documentation uploaded
            remote_filename = ftp.path.join(bh.docs_server_directory, bh.repo_name, bh.repo_branch, repo_version, 'index.html')
            with ftp.open(remote_filename, 'r') as file:
                self.assertEqual(file.read(), 'Test documentation')

            remote_filename = ftp.path.join(bh.docs_server_directory, bh.repo_name, bh.repo_branch, repo_version, 'a', 'b', 'c', 'index.html')
            with ftp.open(remote_filename, 'r') as file:
                self.assertEqual(file.read(), 'Test!')

            remote_filename = ftp.path.join(bh.docs_server_directory, bh.repo_name, '.htaccess')
            with ftp.open(remote_filename, 'r') as file:
                self.assertRegex(file.read(), 'RewriteRule \^{0}/latest/\(\.\*\)\$ {0}/{1}/\$1 \[R=303,L\]'.format(
                    bh.repo_branch, repo_version))

            # cleanup
            ftp.rmtree(ftp.path.join(bh.docs_server_directory, bh.repo_name))

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
            file.write('git+https://github.com/KarrLab/karr_lab_build_utils.git#egg=karr_lab_build_utils-0.0.1\n')
            file.write('dep_2\n')
        with open(os.path.join(packages_parent_dir, 'pkg_2', 'requirements.txt'), 'w') as file:
            file.write('dep_3\n')
            file.write('dep_4\n')
            file.write('dep_5\n')
        with open(os.path.join(packages_parent_dir, 'pkg_3', 'requirements.txt'), 'w') as file:
            file.write('dep_6\n')
            file.write('dep_7\n')
            file.write('git+https://github.com/KarrLab/karr_lab_build_utils.git#egg=karr_lab_build_utils-0.0.1\n')

        # create temp filename to save dependencies
        tmp_file, config_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(config_filename, 'w') as file:
            file.write('downstream_dependencies: []\n')

        # test api
        build_helper = core.BuildHelper()
        deps = build_helper.compile_downstream_dependencies(
            packages_parent_dir=packages_parent_dir,
            config_filename=config_filename)
        self.assertEqual(sorted(deps), ['pkg_1', 'pkg_3'])

        with open(config_filename, 'r') as file:
            self.assertEqual(sorted(yaml.load(file.read())['downstream_dependencies']), ['pkg_1', 'pkg_3'])

        with open(os.path.join(packages_parent_dir, 'pkg_1', 'setup.cfg'), 'w') as file:
            file.write('[coverage:run]\n')
            file.write('source = \n')
            file.write('    pkg_1\n')
            file.write('    mod_2\n')
        with self.assertRaisesRegex(core.BuildHelperError, 'Package should have only one module'):
            deps = build_helper.compile_downstream_dependencies(
                dirname=os.path.join(packages_parent_dir, 'pkg_1'),
                packages_parent_dir=packages_parent_dir,
                config_filename=config_filename)

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['compile-downstream-dependencies', '--packages-parent-dir', packages_parent_dir]) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(), 'The following downstream dependencies were found')
                    self.assertEqual(captured.stderr.get_text(), '')

        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['compile-downstream-dependencies',
                                        '--packages-parent-dir', os.path.join(packages_parent_dir, 'pkg_1')]) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(), 'No downstream packages were found.')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        shutil.rmtree(packages_parent_dir)
        os.remove(config_filename)

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
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies:\n  - pkg_2\n')
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies:\n  - pkg_3\n')
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies: []\n')

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
                    self.assertRegex(captured.stdout.get_text(), 'The dependencies are acyclic.')
                    self.assertEqual(captured.stderr.get_text(), '')

        """ cyclic """

        with open(os.path.join(packages_parent_dir, 'pkg_3', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies:\n  - pkg_1\n')

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
                    self.assertRegex(captured.stdout.get_text(), 'The dependencies are cyclic.')
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
        with open(os.path.join(packages_parent_dir, 'pkg_1', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies:\n  - pkg_2\n')
        with open(os.path.join(packages_parent_dir, 'pkg_2', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies:\n  - pkg_3\n')
        with open(os.path.join(packages_parent_dir, 'pkg_3', '.karr_lab_build_utils.yml'), 'w') as file:
            file.write('downstream_dependencies:\n  - pkg_1\n')

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

    def test_trigger_tests_of_downstream_dependencies_with_error(self):
        build_helper = core.BuildHelper()
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        filename = os.path.join(build_helper.proj_tests_xml_dir,
                                '{}.0-1.2.7.12.xml'.format(build_helper.proj_tests_xml_latest_filename))
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

        build_helper = self.construct_build_helper()
        deps = build_helper.trigger_tests_of_downstream_dependencies()
        self.assertEqual(deps, [])

    def test_trigger_tests_of_downstream_dependencies_no_downstream(self):
        build_helper = core.BuildHelper()
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        tmp_file, config_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(config_filename, 'w') as file:
            yaml.dump({'downstream_dependencies': []}, file)

        build_helper = self.construct_build_helper()
        deps = build_helper.trigger_tests_of_downstream_dependencies(
            config_filename=config_filename)
        self.assertEqual(deps, [])

    def test_trigger_tests_of_downstream_dependencies_no_upstream(self):
        build_helper = core.BuildHelper()
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        tmp_file, config_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(config_filename, 'w') as file:
            yaml.dump({'downstream_dependencies': ['dep_1', 'dep_2']}, file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'start_time': '2017-01-01T01:01:01-05:00'},
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
                        config_filename=config_filename)
                    self.assertEqual(deps, ['dep_1', 'dep_2'])

                # test cli
                with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_2]):
                    with __main__.App(argv=['trigger-tests-of-downstream-dependencies',
                                            '--config-filename', config_filename]) as app:
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            app.run()
                    self.assertRegex(captured.stdout.get_text(), '2 dependent builds were triggered')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        os.remove(config_filename)

    def test_trigger_tests_of_downstream_dependencies_with_upstream(self):
        build_helper = core.BuildHelper()
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        tmp_file, config_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(config_filename, 'w') as file:
            yaml.dump({'downstream_dependencies': ['dep_1', 'dep_2']}, file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'start_time': '2017-01-01T01:01:01-05:00'},
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
                        config_filename=config_filename)
                    self.assertEqual(deps, [])

                # test cli
                with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2, requests_get_2]):
                    with __main__.App(argv=['trigger-tests-of-downstream-dependencies',
                                            '--config-filename', config_filename]) as app:
                        with capturer.CaptureOutput(merged=False, relay=False) as captured:
                            app.run()
                    self.assertRegex(captured.stdout.get_text(), 'No dependent builds were triggered.')
                    self.assertEqual(captured.stderr.get_text(), '')

        # cleanup
        os.remove(config_filename)

    def test_trigger_tests_of_downstream_dependencies_trigger_original_upstream(self):
        build_helper = core.BuildHelper()
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        tmp_file, config_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(config_filename, 'w') as file:
            yaml.dump({'downstream_dependencies': ['dep_1']}, file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'start_time': '2017-01-01T01:01:01-05:00'},
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
                        config_filename=config_filename)
                    self.assertEqual(deps, [])

        # cleanup
        os.remove(config_filename)

    def test_trigger_tests_of_downstream_dependencies_already_queued(self):
        build_helper = core.BuildHelper()
        filename_pattern = os.path.join(build_helper.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(build_helper.proj_tests_xml_latest_filename))
        for filename in glob(filename_pattern):
            os.remove(filename)

        tmp_file, config_filename = tempfile.mkstemp(suffix='.yml')
        os.close(tmp_file)
        with open(config_filename, 'w') as file:
            yaml.dump({'downstream_dependencies': ['pkg_2']}, file)

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'start_time': '2017-01-01T01:01:01-05:00'},
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
                        config_filename=config_filename)
                    self.assertEqual(deps, [])

        requests_get_1 = attrdict.AttrDict({
            'raise_for_status': lambda: None,
            'json': lambda: {'start_time': '2019-01-01T01:01:01-05:00'},
        })
        with env:
            with mock.patch('requests.get', side_effect=[requests_get_1, requests_get_2]):
                with mock.patch('requests.post', return_value=requests_post):
                    # test api
                    build_helper = core.BuildHelper()
                    deps = build_helper.trigger_tests_of_downstream_dependencies(
                        config_filename=config_filename)
                    self.assertEqual(deps, ['pkg_2'])

        # cleanup
        os.remove(config_filename)

    def test_trigger_tests_of_downstream_dependencies_dry_run(self):
        build_helper = core.BuildHelper()
        self.assertEqual(build_helper.trigger_tests_of_downstream_dependencies(dry_run=True), [])

    def test_analyze_package(self):
        # test api
        build_helper = core.BuildHelper()

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            build_helper.analyze_package('karr_lab_build_utils')
            self.assertRegex(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
            self.assertEqual(captured.stderr.get_text().strip(), '')

        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            build_helper.analyze_package('karr_lab_build_utils', verbose=True)
            self.assertRegex(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
            self.assertEqual(captured.stderr.get_text().strip(), 'No config file found, using default configuration')

        config_filename = os.path.join(self.tmp_dirname, 'pylintrc')
        with open(config_filename, 'w') as file:
            file.write('\n')
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            build_helper.analyze_package('karr_lab_build_utils', verbose=True, config_filename=config_filename)
            self.assertRegex(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
            self.assertEqual(captured.stderr.get_text().strip(), 'Using config file {}'.format(config_filename))

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['analyze-package', 'karr_lab_build_utils']) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
                    self.assertEqual(captured.stderr.get_text().strip(), '')

        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['analyze-package', 'karr_lab_build_utils', '--messages', 'W0611']) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(), '\* Module karr_lab_build_utils.core')
                    self.assertEqual(captured.stderr.get_text().strip(), '')

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
                    self.assertRegex(captured.stdout.get_text(), 'requirements.txt appears to contain all of the dependencies')
                    self.assertEqual(captured.stderr.get_text(), '')

        shutil.copy('requirements.txt', 'requirements.txt.save')
        with open('requirements.txt', 'w') as file:
            pass
        try:
            with self.construct_environment():
                with capturer.CaptureOutput(merged=False, relay=False) as captured:
                    with __main__.App(argv=[
                            'find-missing-requirements', 'karr_lab_build_utils',
                            '--ignore-files', 'karr_lab_build_utils/templates/*']) as app:
                        app.run()
                        self.assertRegex(captured.stdout.get_text(), 'The following dependencies should likely be added to')
                        self.assertEqual(captured.stderr.get_text(), '')
        finally:
            os.remove('requirements.txt')
            os.rename('requirements.txt.save', 'requirements.txt')

    def test_find_unused_requirements(self):
        # test api
        build_helper = core.BuildHelper()
        unused = build_helper.find_unused_requirements('karr_lab_build_utils', ignore_files=['karr_lab_build_utils/templates/*'])
        unused.sort()

        expected_unused = [            
            'sphinx_rtd_theme',
            'sphinxcontrib_addmetahtml',
            'sphinxcontrib_bibtex',
            'sphinxcontrib_googleanalytics',
            'sphinxcontrib_spelling',
            'wheel',
        ]
        if six.PY3:
            expected_unused.insert(0, 'enum34')
        self.assertEqual(unused, expected_unused)

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=[
                        'find-unused-requirements', 'karr_lab_build_utils',
                        '--ignore-file', 'karr_lab_build_utils/templates/*']) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(),
                                             'The following requirements from requirements.txt may not be necessary:')
                    self.assertRegex(captured.stdout.get_text(),
                                             'sphinxcontrib_googleanalytics')
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
                    self.assertRegex(captured.stdout.get_text(), 'All of the dependencies appear to be necessary')
                    self.assertEqual(captured.stderr.get_text(), '')
        os.remove('requirements.txt')
        os.rename('requirements.txt.save', 'requirements.txt')

    def test_upload_package_to_pypi(self):
        dirname = 'tests/fixtures/karr_lab_build_utils_test_package'

        if not os.path.isdir('tests/fixtures/karr_lab_build_utils_test_package/build'):
            os.mkdir('tests/fixtures/karr_lab_build_utils_test_package/build')

        if not os.path.isdir('tests/fixtures/karr_lab_build_utils_test_package/dist'):
            os.mkdir('tests/fixtures/karr_lab_build_utils_test_package/dist')

        # test api
        build_helper = core.BuildHelper()
        with capturer.CaptureOutput(merged=False, relay=False) as captured:
            build_helper.upload_package_to_pypi(dirname=dirname, repository='testpypi')
            self.assertRegex(captured.stdout.get_text(), 'Uploading distributions to https://test\.pypi\.org/legacy/')
            self.assertEqual(captured.stderr.get_text().strip(), '')

        # test cli
        with self.construct_environment():
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                with __main__.App(argv=['upload-package-to-pypi',
                                        '--dirname', dirname,
                                        '--repository', 'testpypi']) as app:
                    app.run()
                    self.assertRegex(captured.stdout.get_text(), 'Uploading distributions to https://test\.pypi\.org/legacy/')
                    self.assertEqual(captured.stderr.get_text().strip(), '')

    def test_download_package_config_files(self):
        build_helper = self.construct_build_helper()
        build_helper.configs_repo_path = tempfile.mkdtemp()
        shutil.rmtree(build_helper.configs_repo_path)

        # download package configs
        build_helper.download_package_config_files()
        self.assertTrue(os.path.isdir(build_helper.configs_repo_path))

        shutil.rmtree(build_helper.configs_repo_path)
        counter = {'count': 0}
        default_func = git.Repo.clone_from

        def side_effect(src, dest):
            counter['count'] += 1
            if counter['count'] == 1:
                raise git.exc.GitCommandError('msg', 'msg')
            else:
                default_func(src, dest)
        with mock.patch('git.Repo.clone_from', side_effect=side_effect):
            build_helper.download_package_config_files()
        self.assertTrue(os.path.isdir(build_helper.configs_repo_path))

        # update package configs
        build_helper.download_package_config_files()

        # cleanup
        shutil.rmtree(build_helper.configs_repo_path)

    def test_install_package_config_files(self):
        build_helper = self.construct_build_helper()
        tmp_dir = build_helper.configs_repo_path = tempfile.mkdtemp()
        os.mkdir(os.path.join(tmp_dir, 'third_party'))
        source = os.path.join(tmp_dir, 'third_party', 'test.cfg')
        dest = os.path.join(tmp_dir, 'a', 'b', 'c', 'test.cfg')
        with open(os.path.join(tmp_dir, 'third_party', 'paths.yml'), 'w') as file:
            yaml.dump({'test.cfg': dest}, file)
        with open(source, 'w') as file:
            file.write('xyz')

        # update package configs
        with EnvironmentVarGuard() as env:
            build_helper.install_package_config_files()

        # test
        with open(dest, 'r') as file:
            self.assertEqual(file.read(), 'xyz')

        # cleanup
        shutil.rmtree(build_helper.configs_repo_path)

    def test_download_install_package_config_files(self):
        with self.construct_environment():
            with __main__.App(argv=['download-install-package-config-files']) as app:
                app.run()

    def test_get_version(self):
        self.assertIsInstance(karr_lab_build_utils.__init__.__version__, str)

        """ setup """
        build_helper = self.construct_build_helper()

        """ test API """
        build_helper.get_version()

        """ test CLI """
        with self.construct_environment():
            with __main__.App(argv=['-v']) as app:
                with capturer.CaptureOutput(merged=False, relay=False) as captured:
                    with self.assertRaises(SystemExit):
                        app.run()
                    self.assertEqual(captured.stdout.get_text(), karr_lab_build_utils.__version__)
                    self.assertEqual(captured.stderr.get_text(), '')

            with __main__.App(argv=['--version']) as app:
                with capturer.CaptureOutput(merged=False, relay=False) as captured:
                    with self.assertRaises(SystemExit):
                        app.run()
                    self.assertEqual(captured.stdout.get_text(), karr_lab_build_utils.__version__)
                    self.assertEqual(captured.stderr.get_text(), '')

    def test_raw_cli(self):
        with mock.patch('sys.argv', ['karr_lab_build_utils', '--help']):
            with self.assertRaises(SystemExit) as context:
                karr_lab_build_utils.__main__.main()
                self.assertRegex(context.Exception, 'usage: karr_lab_build_utils')

        with mock.patch('sys.argv', ['karr_lab_build_utils']):
            with capturer.CaptureOutput(merged=False, relay=False) as captured:
                karr_lab_build_utils.__main__.main()
                self.assertRegex(captured.stdout.get_text(), 'usage: karr_lab_build_utils')
                self.assertEqual(captured.stderr.get_text(), '')

    def test_unsupported_test_runner(self):
        with self.assertRaisesRegex(core.BuildHelperError, 'Unsupported test runner'):
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

    def test_get_config(self):
        config = karr_lab_build_utils.config.core.get_config()
        self.assertIn('karr_lab_build_utils', config)
        self.assertIn('email_password', config['karr_lab_build_utils'])


@unittest.skipIf(whichcraft.which('docker') is None or whichcraft.which('circleci') is None, (
    'Test requires the CircleCI command line utility (local executor) and this isn''t installed. See '
    'installation instructions at `http://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html`.'
))
class TestCircleCi(unittest.TestCase):

    def setUp(self):
        file, self.temp_filename = tempfile.mkstemp(suffix='.yml')
        os.close(file)

        shutil.copyfile(os.path.join('.circleci', 'config.yml'), self.temp_filename)

    def tearDown(self):
        os.remove(os.path.join('.circleci', 'config.yml'))
        shutil.move(self.temp_filename, os.path.join('.circleci', 'config.yml'))

    def test_run_tests_circleci(self):
        if os.path.isdir('circleci_docker_context'):
            shutil.rmtree('circleci_docker_context')

        if not os.path.isdir('tests/__pycache__'):
            os.mkdir(os.path.join('tests/__pycache__'))

        build_helper = TestKarrLabBuildUtils.construct_build_helper()

        # test success
        build_helper.run_tests(test_path=TestKarrLabBuildUtils.DUMMY_TEST, environment=core.Environment.circleci)

    def test_run_tests_circleci_with_ssh_image(self):
        build_helper = TestKarrLabBuildUtils.construct_build_helper()
        return_value = {'jobs': {'build': {'docker': [{'image': 'x.with_ssh_key'}]}}}
        with mock.patch('yaml.load', return_value=return_value):
            with mock.patch('yaml.dump', return_value=None):
                return_value = attrdict.AttrDict({
                    'poll': lambda: True,
                    'returncode': 0,
                    'communicate': lambda: (b'', b''),
                })
                with mock.patch('subprocess.Popen', return_value=return_value):
                    build_helper.run_tests(test_path=TestKarrLabBuildUtils.DUMMY_TEST, environment=core.Environment.circleci)
