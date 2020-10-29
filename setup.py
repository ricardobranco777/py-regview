#!/usr/bin/env python3
"""
Setup script
"""

from setuptools import setup


def read(path):
    """
    Read a file
    """
    with open(path) as file_:
        return file_.read()


setup(
    name='regview',
    version="0.9.0",
    description="View instance information on all supported cloud providers",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    author="Ricardo Branco",
    author_email='rbranco@suse.de',
    url='https://github.com/ricardobranco777/regview',
    package_dir={'regview': '.'},
    include_package_data=True,
    python_requires='>=3.5',
    install_requires=read('requirements.txt'),
    license='MIT License',
    zip_safe=False,
    keywords=['regview', 'docker registry'],
    scripts=['regview'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: '
        'MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
