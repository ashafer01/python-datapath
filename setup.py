from setuptools import setup

setup(
    name='python-datapath',
    version='0.1.0',

    author='Alex Shafer',
    author_email='ashafer@pm.me',
    description='Functions for working with dotted and square-bracketed paths against a recursive dict/list structure',
    url='https://github.com/ashafer01/python-datapath',
    license='MIT',

    python_requires='>=3.10.0',
    packages=['datapath'],
    install_requires=[
        'regex',
    ],
)
