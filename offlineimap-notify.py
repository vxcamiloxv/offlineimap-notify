#!/usr/bin/python2
# Copyright (C) 2013  Raymond Wagenmaker
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Run OfflineIMAP after adding notification sending to its UIs.

When an account finishes syncing, messages copied to the local repository will
be reported using D-Bus (through pynotify) or a fallback notifier command.
"""

import cgi
from collections import defaultdict, OrderedDict
import ConfigParser
from datetime import datetime
import email.parser
import email.utils
import functools
import inspect
import os
import shlex
import string
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

CONFIG_SECTION = 'notifications'
CONFIG_DEFAULTS = OrderedDict((
    ('summary',        'New mail for {account} in {folder}'),
    ('body',           'From: {h[from]}\nSubject: {h[subject]}'),
    ('icon',           'mail-unread'),
    ('max',            '2'),
    ('digest-summary', 'New mail for {account} ({count})'),
    ('digest-body',    '{count} in {folder}'),
    ('notifier',       'notify-send -a {appname} -i {icon} -c {category} {summary} {body}'),
))

def send_notification(ui, conf, summary, body):
    appname = 'OfflineIMAP'
    category = 'email.arrived'
    encode = functools.partial(unicode.encode, errors='replace')
    # TODO: encode icon as well? (find out if conf is decoded already)
    try:
        pynotify.init(appname)
        notification = pynotify.Notification(encode(summary, 'utf-8'),
                                             encode(body, 'utf-8'), conf['icon'])
        notification.set_category(category)
        notification.show()
    except (NameError, RuntimeError):  # no pynotify or no notification service
        try:
            format_args = {'appname': appname, category=category,
                           'summary': encode(summary), 'body': encode(body),
                           'icon': conf['icon']}
            subprocess.call([word.format(**format_args)
                             for word in shlex.split(conf['notifier'])])
        except ValueError as e:
            ui.error(e, msg='While parsing fallback notifier command')
        except OSError as e:
            ui.error(e, msg='While calling fallback notifier')

def add_notifications(ui_cls):

    def extension(method):
        old = getattr(ui_cls, method.__name__)
        uibase_spec = inspect.getargspec(getattr(offlineimap.ui.UIBase.UIBase,
                                                 method.__name__))

        @functools.wraps(old)
        def new(*args, **kwargs):
            old_args = inspect.getcallargs(old, *args, **kwargs)
            method(**{arg: old_args[arg] for arg in uibase_spec.args})
            old(*args, **kwargs)

        setattr(ui_cls, method.__name__, new)

    @extension
    def __init__(self, *args, **kwargs):
        self.local_repo_names = {}
        self.new_messages = defaultdict(lambda: defaultdict(list))

    @extension
    def acct(self, account):
        self.local_repo_names[account] = account.localrepos.getname()

    @extension
    def acctdone(self, account):
        if self.new_messages[account]:
            notify(self, account)
            self.new_messages[account].clear()

    @extension
    def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
        repository = destfolder.getrepository()
        account = repository.getaccount()
        if (repository.getname() == self.local_repo_names[account] and
            'S' not in src.getmessageflags(uid)):
            self.new_messages[account][destfolder].append(uid)

    return ui_cls

class MailNotificationFormatter(string.Formatter):
    _FAILED_DATE_CONVERSION = object()

    # TODO:
    # - decode headers?
    # - how are missing headers handled?

    def __init__(self, escape=False):
        self.escape = escape

    def format_field(self, value, format_spec):
        try:
            result = super(MailNotificationFormatter, self).format_field(value, format_spec)
        except ValueError:
            if value is MailNotificationFormatter._FAILED_DATE_CONVERSION:
                result = ''  # TODO: add config option to customize this string?
            else:
                raise
        return cgi.escape(result, quote=True) if self.escape else result

    def convert_field(self, value, conversion):
        if conversion == 'd':
            datetuple = email.utils.parsedate_tz(value)
            if datetuple is None:
                return MailNotificationFormatter._FAILED_DATE_CONVERSION
            # TODO: skip the mktime_tz step?
            return datetime.fromtimestamp(email.utils.mktime_tz(datetuple))
        elif conversion in 'anN':
            name, address = email.utils.parseaddr(value)
            if not address:
                address = value
            if conversion == 'a':
                return address
            return name if name or conversion == 'n' else address
        return super(MailNotificationFormatter, self).convert_field(value, conversion)

def notify(ui, account):
    summary_formatter = MailNotificationFormatter(escape=False)
    body_formatter = MailNotificationFormatter(escape=True)

    conf = CONFIG_DEFAULTS.copy()
    try:
        conf.update(ui.config.items(CONFIG_SECTION))
    except ConfigParser.NoSectionError:
        pass
    notify_send = functools.partial(send_notification, ui, conf)

    count = 0
    body = []
    for folder, uids in ui.new_messages[account].iteritems():
        count += len(uids)
        body.append(body_formatter.format(conf['digest-body'],
                                          count=len(uids), folder=folder))

    if count > int(conf['max']):
        summary = summary_formatter.format(conf['digest-summary'],
                                           account=account.getname(), count=count)
        return notify_send(summary, '\n'.join(body))

    need_body = '{body' in conf['body'] or '{body' in conf['summary']
    parser = email.parser.Parser()
    for folder, uids in ui.new_messages[account].iteritems():
        format_args = {'account': account.getname(), 'folder': folder}
        for uid in uids:
            message = parser.parsestr(folder.getmessage(uid),
                                      headersonly=not need_body)
            format_args['h'] = message
            if need_body:
                for part in message.walk():
                    if part.get_content_type() == 'text/plain':
                        format_args['body'] = part  # FIXME: need to .get_payload(decode=True),
                        # but should study multipart handling more too
                        break
                else:
                    format_args['body'] = 'FIXME'  # try HTML body.striptags() or same failstr as for date conversion?
            try:
                notify_send(summary_formatter.vformat(conf['summary'], (), format_args),
                            body_formatter.vformat(conf['body'], (), format_args))
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                ui.error(e, msg='In notification format specification')

def print_help():
    try:
        text_width = int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        text_width = 80
    tw = textwrap.TextWrapper(width=text_width)
    print('Notification wrapper -- {}\n'.format(__copyright__))
    print(tw.fill(__doc__))
    print('\nDefault configuration:\n')
    default_config = offlineimap.CustomConfig.CustomConfigParser()
    default_config.add_section(CONFIG_SECTION)
    for option, value in CONFIG_DEFAULTS.iteritems():
        default_config.set(CONFIG_SECTION, option, value)
    default_config.write(sys.stdout)

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
