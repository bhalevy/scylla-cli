from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='scylla-api-client',
    description='Command line tool for managing Scylla database nodes',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/scylladb/scylla-api-client',
    author='ScyllaDB',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=['requests'],
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    entry_points={
        'console_scripts': [
            'scylla-api-client=scylla_api_client.__main__:main',
        ],
    },
    license='GNU AGPL 3.0',
    license_files=('LICENSE.AGPL',),
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/scylladb/scylla-api-client/issues',
    },
)
