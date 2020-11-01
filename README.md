# offlineimap-notify

The default branch is now [main](https://framagit.org/distopico/offlineimap-notify). check it to see the most recent changes

Wrapper for add notification sending to OfflineIMAP.

Run OfflineIMAP after adding notification sending to its UIs.  When an account
finishes syncing, messages synced to the local repository will be reported
using D-Bus (through `notify2`) or a fallback notifier command.

## Quick Start

* Install the package
```sh
  pip2 install offlineimap-notify
```

* Call `offlineimap-notify` instead of `offlineimap`

```sh
 offlineimap-notify
```

## Requirements
* Python 2.7.x
* OfflineIMAP
* [notify2](https://pypi.org/project/notify2) (Optional)

## Usage
For configuration options and usage check [Docs](https://framagit.org/distopico/offlineimap-notify/-/blob/master/docs/offlineimap-notify.md)

## License
[![GNU General Public License version 3](https://www.gnu.org/graphics/gplv3-127x51.png)](https://framagit.org/distopico/offlineimap-notify/-/blob/master/LICENSE)
