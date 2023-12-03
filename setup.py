from setuptools import setup

desc = 'Functions for working with dotted and square-bracketed paths against a recursive dict/list structure'
url = 'https://github.com/ashafer01/python-datapath'

setup(
    name='python-datapath',
    version='0.1.0',

    author='Alex Shafer',
    author_email='ashafer@pm.me',
    description=desc,
    long_description=f'{desc}\n\nDocs at {url}',
    url=url,
    license='MIT',

    packages=['datapath'],
    python_requires='>=3.10.0',
    install_requires=[
        'regex',
    ],
)
