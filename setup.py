#!/usr/bin/env python3

from setuptools import setup


with open("README.md", "r") as f:
    long_description = f.read()

setup(
    author='Filip Krestan',
    author_email='krestfi1@fit.cvut.cz',
    description='Flask application for Bloom filter recording and aggregation.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    name='blooming_history_aggregator_service',
    url='https://github.com/fkrestan/blooming_history_aggregator_service',
    version='0.0.1',
    packages=['blooming_history_aggregator'],
    install_requires=["cffi>=1.0.0", "flask>=1.0.0", "uwsgi>=2.0.0"],
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["blooming_history_aggregator/bindings.py:ffibuilder"],
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Education",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Security",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking",
    ),
)
