from setuptools import setup

VERSION = '0.5.1'

with open('offlineimap-notify.rst') as man_page:
    long_description = man_page.read()

setup(name='offlineimap-notify',
      version=VERSION,
      author='Raymond Wagenmaker',
      author_email='raymondwagenmaker@gmail.com',
      description='Wrapper that adds notification sending to OfflineIMAP',
      long_description=long_description,
      url='https://bitbucket.org/raymonad/offlineimap-notify',
      download_url='https://bitbucket.org/raymonad/offlineimap-notify/get/v'+VERSION+'.tar.gz',
      py_modules=['offlineimap_notify'],
      classifiers=[
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)'
          'Programming Language :: Python :: 2.7'
      ],
      entry_points={
          'console_scripts': ['offlineimap-notify = offlineimap_notify:main']
      },
      install_requires=['offlineimap'])
