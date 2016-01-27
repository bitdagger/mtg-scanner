from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import os

import mtgscanner

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md', 'CHANGES.txt')

setup(
    name='mtgscanner',
    description='Scanner for Magic: The Gathering cards',
    version=mtgscanner.__version__,
    url='http://github.com/bitdagger/mtg-scanner/',
    license='MIT License',
    author='Matt Fields',
    author_email='mafields@bitdagger.com',
    install_requires=['cv2>=1.0',
                    'numpy>=1.10.4',
                    'phash>=0.2.0',
                    'progressbar>=2.3',
                    ],
    entry_points={
        'console_scripts': [
            'mtgscanner = mtgscanner.mtgscanner:run',
            ],
        },
    long_description=long_description,
    packages=['mtgscanner'],
    include_package_data=True,
    platforms='any',
)
