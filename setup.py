from setuptools import setup

setup(
    name='py3jsondb',
    version='1.0.0',
    description='searchable json database, easy to add,update,delete and search in any level nested json tree',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=['py3jsondb', 'py3jsondb.utils'],
    url='https://github.com/alex-testlab/py3jsondb',
    license='MIT',
    author='jarbasAI,Alex',
    author_email='',
    install_requires=["pyxdg", "fasteners"],
)
