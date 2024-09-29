from setuptools import setup
from setuptools import find_packages

from spedpyutils import __version__

with open("README.md", "r") as arq:
    readme = arq.read()

setup(name='spedpyutils',
    version=__version__,
    license='MIT License',
    author='Ismael Nascimento',
    long_description=readme,
    long_description_content_type="text/markdown",
    author_email='ismaelnjr@icloud.com.br',
    keywords='sped fiscal receita federal',
    description=u'Biblioteca para visualização de um arquivo sped em estrutura de tabelas hierarquicas. Compatibilidade com a biblioteca python-sped',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['spedpy', 'pandas', 'openpyxl', 'tqdm'],
    classifiers=
        ["Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"],
   
    )

