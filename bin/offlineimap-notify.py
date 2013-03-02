#!/usr/bin/python2

"""Run OfflineImap and send notifications for new mail.

When an account is finished, messages synced to the local repository are
reported using D-Bus (through pynotify) or a fallback notifier command.
"""

from __future__ import print_function

import collections
import ConfigParser
from datetime import datetime
import email.parser
from email.utils import parsedate_tz, mktime_tz
import functools
import inspect
import os
import shlex
import subprocess
import sys
import textwrap

import offlineimap
try:
    import pynotify
except ImportError:
    pass

__author__ = 'Raymond Wagenmaker'
__copyright__ = 'Copyright 2013 ' + __author__

OptSpec = collections.namedtuple('OptSpec', ('descr', 'default'))
CONFIG_SECTION = 'notifications'
CONFIG_DEFAULTS = collections.OrderedDict((  # TODO: add options for formatting single notification when exceeding max
    ('summary',  OptSpec(default='New mail for {account} in {folder}',
                         descr='format for notification summary')),
    ('body',     OptSpec(default='From: {hdr[from]}\nSubject: {hdr[subject]}',
                         descr='format for notification body')),
    ('max',      OptSpec(default=2,
                         descr="""maximum number of notifications; when an
                               account has more new messages, send one summary
                               notification""")),
    ('notifier', OptSpec(default="notify-send -a {appname} '{summary}' '{body}'",
                         descr='fallback command for notifications'))
))

def send_notification(ui, summary, body, fallback_cmd):
    appname = os.path.basename(sys.argv[0])
    try:
        pynotify.init(appname)
        pynotify.Notification(summary, body).show()
    except NameError, RuntimeError:  # no pynotify or no notification service
        format_args = {'appname': appname, 'summary': summary, 'body': body}
        try:
            subprocess.call(shlex.split(fallback_cmd.format(format_args)))
        except ValueError as e:
            ui.error(e, msg='While parsing fallback notifier command')
        except OSError as e:
            ui.error(e, msg='While calling fallback notifier')

def add_notifications(ui_cls):

    def extend(extender):
        old = getattr(ui_cls, extender.__name__)
        uibase_spec = inspect.getargspec(getattr(offlineimap.ui.UIBase.UIBase,
                                                 extender.__name__))

        @functools.wraps(old)
        def new(*args, **kwargs):
            old_args = inspect.getcallargs(old, *args, **kwargs)
            extender(**{arg: old_args[arg] for arg in uibase_spec.args})
            old(*args, **kwargs)

        setattr(ui_cls, extender.__name__, new)
        return new

    @extend
    def acct(self, account):
        self.new_messages = collections.defaultdict(list)

    @extend
    def acctdone(self, account):
        if self.new_messages:
            notify(self)
        del self.new_messages

    @extend
    def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
        if (destfolder.getrepository().getname() == 'local' and
            'S' not in src.getmessageflags(uid)):
            self.new_messages[destfolder].append(uid)

    return ui_cls

def notify(ui):
    conf = {opt: spec.default for opt, spec in CONFIG_DEFAULTS.iteritems()}
    try:
        conf.update(ui.config.items(CONFIG_SECTION))
    except ConfigParser.NoSectionError:
        pass
    send_notification = functools.partial(send_notification, ui,
                                          fallback_cmd=conf['notifier'])
    count = 0
    body = []
    for folder, uids in ui.new_messages.iteritems():
        count += len(uids)
        body.append('{} in {}'.format(len(uids), folder))
    account = folder.accountname()

    if count > conf['max']:
        summary = 'New mail for {} ({})'.format(account, count)
        return send_notification(summary, '\n'.join(body))

    need_body = '{body' in options.body or '{body' in options.summary
    parser = email.parser.Parser()
    for folder, uids in ui.new_messages.iteritems():
        format_args = {'account': account, 'folder': folder}
        for uid in uids:
            message = parser.parsestr(folder.getmessage(uid),
                                      headersonly=not need_body)
            timestamp = mktime_tz(parsedate_tz(message['date']))
            format_args['h'] = message
            format_args['date'] = datetime.fromtimestamp(timestamp)
            if need_body:
                for part in message.walk():
                    if part.get_content_type() == 'text/plain':
                        format_args['body'] = part  # FIME: need to .get_payload(decode=True),
                        # but should study multipart handling more too
                        break
                else:
                    format_args['body'] = 'FIXME'
            try:
                send_notification(conf['summary'].format(**format_args),
                                  conf['body'].format(**format_args))
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                ui.error(e, msg='While formatting notification')

def decorate_uis(uis):
    for name, cls in uis.iteritems():
        uis[name] = add_notifications(cls)

def print_help():
    try:
        text_width = os.environ['COLUMNS']
    except (KeyError, ValueError):
        text_width = 80
    tw = textwrap.TextWrapper(width=text_width)

    paragraphs = ('Notification wrapper -- ' + __copyright__, __doc__,
                  """The following options can be specified in a [{}] section
                  in '~/.offlineimaprc (and overridden using the -k option on
                  the command line).""".format(CONFIG_SECTION))
    print('\n\n'.join(tw.fill(par) for par in paragraphs))

    indent = column_sep = '  '
    option_width = max(len(option) for option in CONFIG_DEFAULTS)
    for option, spec in CONFIG_DEFAULTS.iteritems():
        tw.initial_indent = (option_width - len(option)) * ' ' + column_sep
        tw.subsequent_indent = indent + option_width * ' ' + column_sep
        print(indent, option, tw.fill(spec.descr), sep='')
        tw.initial_indent = tw.subsequent_indent
        print(tw.fill('(default: {!r})'.format(spec.default)))
    print()

if __name__ == '__main__':
    decorate_uis(offlineimap.ui.UI_LIST)
    if '-h' in sys.argv or '--help' in sys.argv:
        print_help()
    offlineimap.OfflineImap().run()
