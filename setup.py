from setuptools import setup
import offlineimap_notify

VERSION = offlineimap_notify.__version__

with open('README.md') as readme_page:
    long_description = readme_page.read()

setup(
    name='offlineimap-notify',
    version=VERSION,
    author=offlineimap_notify.__author__,
    author_email='distopico@riseup.net',
    description='Wrapper for add notification sending to OfflineIMAP',
    long_description=long_description,
    url='https://framagit.org/distopico/offlineimap-notify',
    download_url='https://framagit.org/distopico/offlineimap_notify/-/archive/v' + VERSION + '/offlineimap_notify-v' + VERSION + '.tar.gz',
    py_modules=['offlineimap_notify'],
    classifiers=[
        'Programming Language :: Python :: 2.7'
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)'
    ],
    entry_points={
        'console_scripts': ['offlineimap-notify = offlineimap_notify:main']
    },
    install_requires=['offlineimap'],
    python_requires='>=2.7',
)
