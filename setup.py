# -*- coding: utf-8 -*-
"""Installer for the pas.plugins.headers package."""

from setuptools import find_packages
from setuptools import setup


long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CONTRIBUTORS.rst').read(),
    open('CHANGES.rst').read(),
])


setup(
    name='pas.plugins.headers',
    version='1.3.2',
    description="PAS plugin for authentication based on request headers",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords='Python Plone Zope PAS acl_users SAML',
    author='Maurits van Rees',
    author_email='m.van.rees@zestsoftware.nl',
    url='https://github.com/collective/pas.plugins.headers',
    license='GPL version 2',
    packages=find_packages('src', exclude=['ez_setup']),
    namespace_packages=['pas', 'pas.plugins'],
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        # 'plone.api>=1.8.4',
        'Products.GenericSetup>=1.8.2',
        'Products.PluggableAuthService',
        'setuptools',
        'six>=1.12.0',
    ],
    extras_require={
        'test': [
            'plone.api',
            'plone.app.testing',
            'plone.testing',
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
