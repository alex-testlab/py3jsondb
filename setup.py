from setuptools import setup

setup(
    name='pyjsondb',
    version='1.0.0',
    packages=['pyjsondb', 'pyjsondb.utils'],
    url='',
    license='MIT',
    author='jarbasAI,Alex',
    author_email='',
    install_requires=["pyxdg", "fasteners"],
    description='searchable json database, easy to add,update,delete and search in any level nested json tree'
)
