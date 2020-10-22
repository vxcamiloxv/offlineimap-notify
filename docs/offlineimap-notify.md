# offlineimap-notify

Wrapper for add notification sending to OfflineIMAP

## Synopsis

offlineimap-notify [*option*] ...

## Description

Run OfflineIMAP after adding notification sending to its UIs.  When an account
finishes syncing, messages synced to the local repository will be reported
using D-Bus (through [notify2][notify2]) or a fallback notifier command.

## Options

Options are not touched by the notification wrapper; see **--help** output for
OfflineIMAP's options.

## Configuration

The following options can be specified in a **[notifications]** section in
*~/.offlineimaprc* (and overridden by using the **-k** option on the command
line).
See **--help** output for the default configuration.

**summary**

    format for notification summary

**body**

    format for notification body

**icon**

    notification icon

**urgency**

    notification urgency level (low, normal, critical)

**timeout**

    notification expiration timeout (in milliseconds; 0=never, -1=default)

**max**

    maximum number of notifications; when an account has more new messages,
    send a single digest notification

**digest-summary**

    summary for digest notification

**digest-body**

    body for digest notification; this line is repeated for each folder

**notifier**

    fallback command for notifications

**failstr**

    replacement string to use in format strings when parts of the message are
    unavailable (missing headers, for example)

## Format strings

The options that specify a format string use Python's `str.format()`
syntax[^1], where `{field}` is replaced by the value of `field`.
The defaults show most of the available fields, but for **summary** and **body**
you can extract more data from the message the notification refers to:

| Field       | Value                                                          |
|-------------|----------------------------------------------------------------|
| `account`   | name of the account                                            |
| `folder`    | name of the folder                                             |
| `body`      | body of the message (taken from the first `text/plain` part)   |
| `h[name]`   | value of the header `name`                                     |

For headers, you can use three custom conversion types: `d` to parse a date
to a `datetime`, which allows you to use a `strftime()` format spec[^2];
`a` to get only the address part of a header like `From`, or
the original header if parsing fails; `n` to get only the name part of such a
header, which may be an empty string (useful combined with `a`); or `N` to
get the name part, or the address in case there is no name. Some examples:

`{body:.20}`

  first 20 characters of the message body

`{h[date]!d:%%H:%%M}`

  time from the `Date` header (hh:mm); remember that a literal '%' has to
  be encoded as '%%' because OfflineIMAP's configuration also supports
  interpolation using `%(field)s` specifications

`<b>{h[from]!n}</b> {h[from]!a}`

  name of the sender (if present) in bold (for notification daemons
  supporting markup) followed by the email address

See also
========

[man offlineimap](https://github.com/OfflineIMAP/offlineimap)
[^1]: http://docs.python.org/2/library/string.html#formatstrings
[^2]: http://docs.python.org/2/library/datetime.html#strftime-strptime-behavior

[notify2]: https://pypi.org/project/notify2/
