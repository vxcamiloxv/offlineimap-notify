# offlineimap-notify

Wrapper for add notification sending to OfflineIMAP.

Run OfflineIMAP after adding notification sending to its UIs.  When an account
finishes syncing, messages synced to the local repository will be reported
using D-Bus (through pynotify) or a fallback notifier command.

## Quick Start

* Call `offlineimap-notify` instead of `offlineimap`

```sh
 offlineimap-notify
```

## Usage
For configuration options and usage check [Docs](https://framagit.org/distopico/offlineimap-notify/-/blob/master/docs/offlineimap-notify.md)

## License
[![GNU General Public License version 3](https://www.gnu.org/graphics/gplv3-127x51.png)](https://framagit.org/distopico/offlineimap-notify/-/blob/master/LICENSE)
