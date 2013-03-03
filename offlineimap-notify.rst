==================
offlineimap-notify
==================

---------------------------------------------
notification wrapper/shell around OfflineIMAP
---------------------------------------------

:Author: Raymond Wagenmaker
:Manual section: 1

Synopsis
========

offlineimap-notify [*option*] ...

Description
===========

.. TODO

Options
=======

Options are not touched by the notification wrapper; see **--help** output for
OfflineIMAP's options.

Configuration
=============

The following options can be specified in a **[notifications]** section in
*~/.offlineimaprc* (and overridden by using the **-k** option on the command
line). See **--help** output for the default configuration.

summary
    format for notification summary

body
    format for notification body

icon
    notification icon

max
    maximum number of notifications; when an account has more new messages,
    send a single digest notification

digest-summary
    summary for digest notification

digest-body
    body for digest notification; this line is repeated for each folder

notifier
    fallback command for notifications; notification summary and body will be
    passed as additional arguments

See also
========

**offlineimap**\(1)
