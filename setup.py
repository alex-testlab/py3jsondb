from setuptools import setup

setup(
    name='pyjsondb',
    version='1.0.0',
    description='searchable json database, easy to add,update,delete and search in any level nested json tree',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=['pyjsondb', 'pyjsondb.utils'],
    url='https://github.com/alex-testlab/pyjsondb',
    license='MIT',
    author='jarbasAI,Alex',
    author_email='',
    install_requires=["pyxdg", "fasteners"],
)
