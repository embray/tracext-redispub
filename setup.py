#!/usr/bin/env python

from setuptools import setup

setup(
    name='tracext-redispub',
    version='0.1',
    author='Erik M. Bray',
    author_email='erik.m.bray@gmail.com',
    url='https://github.com/embray/tracext-redispub',
    description='Redis pub/sub channels for Trac events',
    download_url='https://pypi.python.org/pypi/tracext-redispub',
    packages=['tracext', 'tracext.redispub'],
    platforms='all',
    license='BSD',
    # Loose versions for now since this will work with most versions of Trac
    # and most current versions of redis-py
    install_requires=[
        'trac',
        'redis'
    ],
    entry_points={'trac.plugins': [
        'redispub.client = tracext.redispub.redis:RedisClient',
        'redispub.ticket = tracext.redispub.ticket:RedisTicketStream',
        'redispub.wiki = tracext.redispub.wiki:RedisWikiStream'
    ]}
)

