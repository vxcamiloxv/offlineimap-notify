#!/usr/bin/python2

from argparse import ArgumentParser
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from email.parser import Parser
from email.utils import parsedate_tz, mktime_tz
import functools
import inspect
import logging
import os
import re
import subprocess
import sys

from offlineimap import OfflineImap, ui
from offlineimap.folder.Maildir import MaildirFolder
try:  # FIXME: pynotify might still raise GError when no dbus notification service is known
    import pynotify
    def send_notification(summary, body):
        pynotify.init('OfflineImap')
        pynotify.Notification(summary, body).show()
except ImportError:
    def send_notification(summary, body):
        try:
            subprocess.call(['notify-send', '-a', 'OfflineImap', summary, body])
        except OSError:
            logging.warning('Failed to send notification.')

def notify_ui(notify, base_ui):
    class NotifyUI(base_ui):
        def acct(self, account):
            self.new_messages = defaultdict(list)
            super(NotifyUI, self).acct(account)

        def acctdone(self, account):
            notify(self.new_messages)
            del self.new_messages
            super(NotifyUI, self).acctdone(account)

        def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
            if (isinstance(destfolder, MaildirFolder) and
                'S' not in src.getmessageflags(uid)):
                self.new_messages[destfolder].append(uid)
            super(NotifyUI, self).copyingmessage(uid, num, num_to_copy, src, destfolder)

    return NotifyUI

def notify(options, new_mails):
    account = None
    count = 0
    body = []
    for folder, uids in new_mails.iteritems():
        account = account or folder.accountname()
        count += len(uids)
        body.append('{} in {}'.format(len(uids), folder))

    if count > options.max:
        summary = 'New mail for {} ({})'.format(account, count)
        return send_notification(summary, '\n'.join(body))

    need_body = '{body' in options.body or '{body' in options.summary
    parser = Parser()
    for folder, uids in new_mails.iteritems():
        for uid in uids:
            format_args = {'account': account, 'folder': folder}
            message = parser.parsestr(folder.getmessage(uid),
                                      headersonly=not need_body)
            timestamp = mktime_tz(parsedate_tz(message['date']))
            format_args['h'] = message
            format_args['date'] = datetime.fromtimestamp(timestamp)
            if need_body:
                for part in message.walk():
                    if part.get_content_type() == 'text/plain':
                        format_args['body'] = part
                        break
            try:
                send_notification(options.summary.format(**format_args),
                                  options.body.format(**format_args))
            except StandardError:
                pass
            # TODO: catch KeyError, AttributeError for incorrect format strings
            # and also TypeError and ValueError, or just catch StandardError?

def parse_args():
    def getdefaultloglevel(ui_name):
        argspec = inspect.getargspec(ui.UI_LIST[ui_name].__init__)
        defaults = dict(zip(reversed(argspec.args), argspec.defaults or ()))
        try:
            return defaults['loglevel']
        except KeyError:
            return logging.NOTSET

    fmt_default = ' (default: %(default){})'.format
    parser = ArgumentParser(description=__doc__,
                            epilog='''Additional arguments will be passed on to
                                   offlineimap, except for --info.''')
    parser.add_argument('-u', default=max(ui.UI_LIST, key=getdefaultloglevel),
                        choices=ui.UI_LIST.keys(), dest='ui',
                        help='specify (non-interactive) user interface to use' +
                             fmt_default('s'))
    parser.add_argument('-s', '--summary',
                        help='format for notification summary' + fmt_default('r'),
                        default='New mail for {account}')
    parser.add_argument('-b', '--body',
                        help='format for notification body' + fmt_default('r'),
                        default='From: {hdr[from]}\nSubject: {hdr[subject]}')
    parser.add_argument('-m', '--max', default=2,
                        help='maximum number of messages' + fmt_default('s'))
    args, offlineimap_args = parser.parse_known_args()
    try:
        offlineimap_args.remove('--info')
    except ValueError:
        pass
    offlineimap_args.extend(['-u', args.ui])
    return args, offlineimap_args

@contextmanager
def sys_argv(argv, prog=None):
    argv_old = sys.argv
    sys.argv = [argv_old[0] if prog is None else prog] + argv
    yield
    sys.argv = argv_old

def disable_interactive_uis():
    is_noninteractive = lambda (_, cls): cls.__module__ == ui.Noninteractive.__name__
    noninteractive_uis = filter(is_noninteractive, ui.UI_LIST.iteritems())
    ui.UI_LIST.clear()
    ui.UI_LIST.update(noninteractive_uis)

if __name__ == '__main__':
    disable_interactive_uis()
    args, offlineimap_args = parse_args()
    notify = functools.partial(notify, options=args)
    ui.UI_LIST[args.ui] = notify_ui(notify, ui.UI_LIST[args.ui])
    with sys_argv(offlineimap_args, prog='offlineimap'):
        oi = OfflineImap()
        oi.run()
