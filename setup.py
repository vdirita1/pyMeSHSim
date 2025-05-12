from setuptools import setup, find_packages
import io
import os

# Read the long description from README.md
here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyMeSHSim',
    version='0.0.1',
    description='MeSH semantic similarity computations using UMLS and ontology metrics',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Victor Di Rita',
    author_email='vdirita1@example.com',
    url='https://github.com/vdirita1/pyMeSHSim',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'bcolz>=1.2.1',
        'numpy>=1.20.0',
        'pandas>=1.3.0',
        'Cython>=0.29.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
)