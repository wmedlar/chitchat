from setuptools import setup

setup(
    name='chitchat',
    version='0.1.0',
    author='necromanteion',
    description='A pure Python module for creating asynchronous IRC bots.',
    keywords='irc async asynchronous asyncio bot',
    url='https://github.com/necromanteion/chitchat',
    packages=['chitchat', 'tests'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications :: Chat :: Internet Relay Chat'
    ]
)