from setuptools import setup, find_packages
import os
import pip
import re

# get long description
if os.path.isfile('README.rst'):
    with open('README.rst', 'r') as file:
        long_description = file.read()
else:
    long_description = ''

# get version
with open('{{ name }}/VERSION', 'r') as file:
    version = file.read().strip()

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

# install package
setup(
    name="{{ name }}",
    version=version,
    description="{{ name }}",
    long_description=long_description,
    url="https://github.com/KarrLab/{{ name }}",
    download_url='https://github.com/KarrLab/{{ name }}',
    author="Karr Lab",
    author_email="karr@mssm.com",
    license="MIT",
    keywords='',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        '{{ name }}': [
            'VERSION',
        ],
    },
    install_requires=install_requires,
    tests_require=tests_require,
    dependency_links=dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
        ],
    },
)
