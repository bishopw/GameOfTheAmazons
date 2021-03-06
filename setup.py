from distutils.core import setup

setup(
    name='Amazons',
    version='1.0.0',
    author='Bishop Wilkins and Justin Gregory',
    author_email='bishopw@gmail.com',
    packages=['amazons','amazons.test'],
    scripts=['bin/amazons.py'],
    url='N/A',
    license='LICENSE.txt',
    description='An implementation of the Game of the Amazons.',
    long_description=open('README.txt').read(),
    install_requires=[
        "py27-game >= 1.9.1_6",
        "pgu >= 0.18"
    ]
)