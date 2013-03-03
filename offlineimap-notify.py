#!/usr/bin/python2

"""Run OfflineImap and send notifications for new mail.

When an account is finished, messages synced to the local repository are
reported using D-Bus (through pynotify) or a fallback notifier command.
"""

from __future__ import print_function

import cgi
from collections import defaultdict, OrderedDict, namedtuple
import ConfigParser
from datetime import datetime
import email.parser
from email.utils import parseaddr, parsedate_tz, mktime_tz
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

OptSpec = namedtuple('OptSpec', ('descr', 'default'))
CONFIG_SECTION = 'notifications'
CONFIG_DEFAULTS = OrderedDict((
    ('summary',        OptSpec(default='New mail for {account} in {folder}',
                               descr='format for notification summary')),
    ('body',           OptSpec(default='From: {h[from]}\nSubject: {h[subject]}',
                               descr='format for notification body')),
    ('icon',           OptSpec(default='mail-unread',
                               descr='notification icon')),
    ('max',            OptSpec(default=2,
                               descr='maximum number of notifications; when an '
                                     'account has more new messages, send a '
                                     'single digest notification')),
    ('digest-summary', OptSpec(default='New mail for {account} ({count})',
                               descr='summary for digest notification')),
    ('digest-body',    OptSpec(default='{count} in {folder}',
                               descr='body for digest notification; this line '
                                     'is repeated for each folder')),
    ('notifier',       OptSpec(default='notify-send -a {appname} -i {icon}',
                               descr='fallback command for notifications; '
                                     'notification summary and body will be '
                                     'passed as additional arguments'))
))

def send_notification(ui, conf, summary, body):
    # FIXME: escaping entire body makes it impossible to use markup in format spec
    body = cgi.escape(body, quote=True)
    appname = os.path.basename(sys.argv[0])
    try:
        pynotify.init(appname)
        pynotify.Notification(summary, body, conf['icon']).show()
    except (NameError, RuntimeError):  # no pynotify or no notification service
        try:
            notifier = conf['notifier'].format(appname=appname, icon=conf['icon'])
            subprocess.call(shlex.split(notifier) + [summary, body])
        except ValueError as e:
            ui.error(e, msg='While parsing fallback notifier command')
        except OSError as e:
            ui.error(e, msg='While calling fallback notifier')

def add_notifications(ui_cls):

    def extend(extension):
        old = getattr(ui_cls, extension.__name__)
        uibase_spec = inspect.getargspec(getattr(offlineimap.ui.UIBase.UIBase,
                                                 extension.__name__))

        @functools.wraps(old)
        def new(*args, **kwargs):
            old_args = inspect.getcallargs(old, *args, **kwargs)
            extension(**{arg: old_args[arg] for arg in uibase_spec.args})
            old(*args, **kwargs)

        setattr(ui_cls, extension.__name__, new)

    @extend
    def __init__(self, *args, **kwargs):
        self.local_repo_names = {}
        self.new_messages = defaultdict(lambda: defaultdict(list))

    @extend
    def acct(self, account):
        self.local_repo_names[account] = account.localrepos.getname()

    @extend
    def acctdone(self, account):
        if self.new_messages[account]:
            notify(self, account)
            self.new_messages[account].clear()

    @extend
    def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
        repository = destfolder.getrepository()
        account = repository.getaccount()
        if (repository.getname() == self.local_repo_names[account] and
            'S' not in src.getmessageflags(uid)):
            self.new_messages[account][destfolder].append(uid)

    return ui_cls

def notify(ui, account):
    conf = {opt: spec.default for opt, spec in CONFIG_DEFAULTS.iteritems()}
    try:
        conf.update(ui.config.items(CONFIG_SECTION))
    except ConfigParser.NoSectionError:
        pass
    notify_send = functools.partial(send_notification, ui, conf)
    count = 0
    body = []
    for folder, uids in ui.new_messages[account].iteritems():
        count += len(uids)
        body.append(conf['digest-body'].format(count=len(uids), folder=folder))

    if count > int(conf['max']):
        summary = conf['digest-summary'].format(account=account.getname(),
                                                count=count)
        return notify_send(summary, '\n'.join(body))

    need_body = '{body' in conf['body'] or '{body' in conf['summary']
    parser = email.parser.Parser()
    for folder, uids in ui.new_messages[account].iteritems():
        format_args = {'account': account.getname(), 'folder': folder}
        for uid in uids:
            message = parser.parsestr(folder.getmessage(uid),
                                      headersonly=not need_body)
            timestamp = mktime_tz(parsedate_tz(message['date']))
            realname, _ = parseaddr(message['from'])
            format_args['h'] = message
            format_args['from'] = realname or message['from']
            format_args['date'] = datetime.fromtimestamp(timestamp)
            if need_body:
                for part in message.walk():
                    if part.get_content_type() == 'text/plain':
                        format_args['body'] = part  # FIXME: need to .get_payload(decode=True),
                        # but should study multipart handling more too
                        break
                else:
                    format_args['body'] = 'FIXME'
            try:
                notify_send(conf['summary'].format(**format_args),
                            conf['body'].format(**format_args))
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                ui.error(e, msg='In notification format specification')

def print_help():
    try:
        text_width = int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        text_width = 80
    tw = textwrap.TextWrapper(width=text_width)

    paragraphs = ('Notification wrapper -- ' + __copyright__,
                  __doc__,
                  ('The following options can be specified in a [{}] section '
                   'in ~/.offlineimaprc (and overridden using the -k option on '
                   'the command line).'.format(CONFIG_SECTION)))
    print('\n\n'.join(map(tw.fill, paragraphs)))

    indent = column_sep = '  '
    option_width = max(map(len, CONFIG_DEFAULTS))
    for option, spec in CONFIG_DEFAULTS.iteritems():
        tw.initial_indent = indent + option.ljust(option_width) + column_sep
        tw.subsequent_indent = indent + option_width * ' ' + column_sep
        print(tw.fill(spec.descr))
        tw.initial_indent = tw.subsequent_indent
        print(*map(tw.fill, '(default: {})'.format(spec.default).splitlines()),
              sep='\n')
    print()

    tw.initial_indent = tw.subsequent_indent = ''
    paragraphs = ("The {var} notation in format specifications is used by "
                  "Python's str.format() for replacement fields. The defaults "
                  "show most of the available fields for all options except "
                  "body and summary.",)
    print('\n\n'.join(map(tw.fill, paragraphs)))
    # TODO: ^ extend description once the formatting stuff stabilizes

if __name__ == '__main__':
    for name, cls in offlineimap.ui.UI_LIST.iteritems():
        offlineimap.ui.UI_LIST[name] = add_notifications(cls)
    try:
        offlineimap.OfflineImap().run()
    except SystemExit:
        if '-h' in sys.argv or '--help' in sys.argv:
            print('\n')
            print_help()
        raise