from setuptools import setup, find_packages
import os
import pip
import re
pip.main(['install', 'git+https://github.com/davidfischer/requirements-parser.git'])
import requirements
import sys

# get long description
if os.path.isfile('README.rst'):
    with open('README.rst', 'r') as file:
        long_description = file.read()
else:
    long_description = ''

# get version
with open('karr_lab_build_utils/VERSION', 'r') as file:
    version = file.read().strip()

# parse dependencies and their links from requirements.txt files
def parse_requirements(filename, install_requires, extras_require, dependency_links):
    if os.path.isfile(filename):
        with open(filename, 'r') as file:
            for req in requirements.parse(file):
                line = req.line
                if '#egg=' in line:
                    if line.find('#') < line.find('#egg='):
                        line = line[0:line.find('#')]
                    else:
                        line = line[0:line.find('#', line.find('#egg=')+5)]
                else:
                    if '#' in line:
                        line = line[0:line.find('#')]
                if ';' in line:
                    marker = line[line.find(';')+1:].strip()
                    marker_match = pkg_resources.Requirement.parse(req.name + '; ' + marker).marker.evaluate()

                else:
                    marker = ''
                    marker_match = True

                req_setup = req.name + ','.join([''.join(spec) for spec in req.specs]) + ('; ' if marker else '') + marker

                if req.extras:
                    for option in req.extras:
                        if option not in extras_require:
                            extras_require[option] = set()
                        extras_require[option].add(req_setup)
                else:
                    install_requires.add(req_setup)

                if req.uri:
                    if req.revision:
                        dependency_links[marker_match].add(req.uri + '@' + req.revision)
                    else:
                        dependency_links[marker_match].add(req.uri)

install_requires = set()
tests_require = set()
docs_require = set()
extras_require = {}
dependency_links = {True: set(), False: set()}

parse_requirements('requirements.txt', install_requires, extras_require, dependency_links)
parse_requirements('tests/requirements.txt', tests_require, extras_require, dependency_links)
parse_requirements('docs/requirements.txt', docs_require, extras_require, dependency_links)

tests_require = tests_require.difference(install_requires)
docs_require = docs_require.difference(install_requires)

extras_require['tests'] = tests_require
extras_require['docs'] = docs_require

install_requires = list(install_requires)
tests_require = list(tests_require)
docs_require = list(docs_require)
for option, reqs in extras_require.items():
    extras_require[option] = list(reqs)
for marker_match, reqs in dependency_links.items():
    dependency_links[marker_match] = list(reqs)

# install non-PyPI dependencies because setup doesn't do this correctly
for dependency_link in dependency_links:
    pip.main(['install', dependency_link])

# read old console scripts
egg_dir = os.path.join(os.path.dirname(__file__), 'karr_lab_build_utils.egg-info')
had_egg_dir = os.path.isdir(egg_dir)
if had_egg_dir:
    pip.main(['install', 'configparser'])
    import configparser
    parser = configparser.ConfigParser()
    parser.read(os.path.join(egg_dir, 'entry_points.txt'))
    scripts = {script: func for script, func in parser.items('console_scripts')}

# install package
setup(
    name="karr_lab_build_utils",
    version=version,
    description="Karr Lab build utilities",
    long_description=long_description,
    url="https://github.com/KarrLab/karr_lab_build_utils",
    download_url='https://github.com/KarrLab/karr_lab_build_utils',
    author="Jonathan Karr",
    author_email="jonrkarr@gmail.com",
    license="MIT",
    keywords='unit test coverage API documentation nose xunit junit unitth HTML Coveralls Sphinx',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'karr_lab_build_utils': [
            'VERSION',
            'templates',
        ],
    },
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=tests_require,
    dependency_links=dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'karr_lab_build_utils = karr_lab_build_utils.__main__:main',
            'karr_lab_build_utils{:d} = karr_lab_build_utils.__main__:main'.format(
                sys.version_info[0]),
            'karr_lab_build_utils{:d}.{:d} = karr_lab_build_utils.__main__:main'.format(
                sys.version_info[0], sys.version_info[1]),
            'karr_lab_build_utils{:d}.{:d}.{:d} = karr_lab_build_utils.__main__:main'.format(
                sys.version_info[0], sys.version_info[1], sys.version_info[2]),
        ],
    },
)

# restore old console scripts
if had_egg_dir:
    parser = configparser.ConfigParser()

    parser.read(os.path.join(egg_dir, 'entry_points.txt'))
    for script, func in parser.items('console_scripts'):
        scripts[script] = func

    for script, func in scripts.items():
        parser.set('console_scripts', script, func)

    with open(os.path.join(egg_dir, 'entry_points.txt'), 'w') as file:
        parser.write(file)
