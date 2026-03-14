from setuptools import find_packages, setup

setup(
    name='feedback_analyzer',
    version='0.0.1',
    license='MIT',
    author='VV',
    author_email='example@gmail.com',
    description='User feedback analysis system',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
)