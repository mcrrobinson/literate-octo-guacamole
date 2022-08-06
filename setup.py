import os
from setuptools import setup

def read(fname):
    """Utility function to read the README file.

    Used for the long_description.  It's nice, because now 1) we have a top
    level README file and 2) it's easier to type in the README file than to put
    a raw string in below.

    Args:
        fname (str): Name of the file to read.

    Returns:
        _OpenFile: Open function with the file contents.
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "livelong",
    version = "0.1",
    author = "Team 31",
    description = ("Live Long is a climate change application that advises \
                   users whether or not they should purchase property in a \
                   specific area based on different environmental factors that \
                   will change in the coming 20 years in that area. "),

    packages=['aggregator','models','tests'],
    install_requires=[
        'fastapi==0.70.0',
        'uvicorn==0.15.0',
        'redis==3.5.3',
        'psycopg2==2.9.3',
        'databases==0.5.5',
    ],
    setup_requires=['pytest-runner', 'pytest-cov'],
    tests_require=['pytest'],
)
