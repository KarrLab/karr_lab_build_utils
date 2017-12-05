from datetime import datetime
import setuptools

setuptools.setup(
    name='karr_lab_build_utils_test_package',
    version='{0.year}.{0.month}.{0.day}.{0.hour}.{0.minute}.{0.second}.{0.microsecond}'.format(datetime.now()),
    description="Test package",
    long_description='',
    url='https://github.com/KarrLab/karr_lab_build_utils',
    author="Jonathan Karr",
    author_email="jonrkarr@gmail.com",
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
)
