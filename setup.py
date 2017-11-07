from setuptools import setup, find_packages
import karr_lab_build_utils
import os
import pip
import re
import sys

# parse dependencies and their links from requirements.txt files
install_requires = []
tests_require = []
dependency_links = []

for line in open('requirements.txt'):
    pkg_src = line.rstrip()
    match = re.match('^.+#egg=(.*?)$', pkg_src)
    if match:
        pkg_id = match.group(1)
        dependency_links.append(pkg_src)
    else:
        pkg_id = pkg_src
    install_requires.append(pkg_id)

for line in open('tests/requirements.txt'):
    pkg_src = line.rstrip()
    match = re.match('^.+#egg=(.*?)$', pkg_src)
    if match:
        pkg_id = match.group(1)
        dependency_links.append(pkg_src)
    else:
        pkg_id = pkg_src
    tests_require.append(pkg_id)
dependency_links = list(set(dependency_links))

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
    version=karr_lab_build_utils.__version__,
    description="Karr Lab build utilities",
    url="https://github.com/KarrLab/karr_lab_build_utils",
    download_url='https://github.com/KarrLab/karr_lab_build_utils/tarball/{}'.format(karr_lab_build_utils.__version__),
    author="Jonathan Karr",
    author_email="jonrkarr@gmail.com",
    license="MIT",
    keywords='unit test coverage API documentation nose xunit junit unitth HTML Coveralls Sphinx',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'karr_lab_build_utils': ['templates'],
    },
    install_requires=install_requires,
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
