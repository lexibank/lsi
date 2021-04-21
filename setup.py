from setuptools import setup
import json


with open("metadata.json", encoding="utf-8") as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_lsi',
    description=metadata['title'],
    license=metadata.get('license', ''),
    url=metadata.get('url', ''),
    py_modules=['lexibank_lsi'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'lsi=lexibank_lsi:Dataset',
        ],
        'cldfbench.commands': [
            'lsi=lsicommands',
        ]
    },
    install_requires=[
        'newick>=1.1.0',
        'pylexibank>=3.1.0',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
