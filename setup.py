from setuptools import setup

setup(
    name='python-datapath',
    version='0.1.0',
    description='Functions for working with dotted and square-bracketed paths against a recursive dict/list structure',
    packages=['datapath'],
    python_requires='>=3.10.0',
    install_requires=[
        'regex',
    ],
)
