from setuptools import setup

with open('offlineimap-notify.rst') as manpage:
    long_description = manpage.read()

setup(name='offlineimap-notify',
      version='0.5.0',
      author='Raymond Wagenmaker',
      author_email='raymondwagenmaker@gmail.com',
      description='Wrapper that adds notification sending to OfflineIMAP',
      long_description=long_description,
      url='https://bitbucket.org/raymonad/offlineimap-notify',
      download_url='https://bitbucket.org/raymonad/offlineimap-notify/downloads#tag-downloads',
      py_modules=['offlineimap_notify'],
      classifiers=[
          'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)'
      ],
      entry_points={
          'console_scripts': ['offlineimap-notify = offlineimap_notify:main']
      },
      install_requires=['offlineimap'])
