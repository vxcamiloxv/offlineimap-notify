#!/usr/bin/python2

"""
poep
"""

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

import offlineimap
try:
    import pynotify
except ImportError:
    pass

CONFIG_SECTION = 'notifications'
CONFIG_DEFAULTS = {  # TODO: add options for formatting single notification when exceeding max
    'summary':  '',
    'body':     '',
    'max':      2,
    'notifier': "notify-send -a {appname} '{summary}' '{body}'"
}

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
    conf = CONFIG_DEFAULTS.copy()
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
    # TODO: add __copyright__ and __author__ (e.g., 'Notification wrapper (c) {author})
    print(__doc__.strip())

if __name__ == '__main__':
    decorate_uis(offlineimap.ui.UI_LIST)
    if '-h' in sys.argv or '--help' in sys.argv:
        print_help()
    offlineimap.OfflineImap().run()
