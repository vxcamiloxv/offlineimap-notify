#!/usr/bin/python2

from argparse import ArgumentParser
from collections import defaultdict
from contextlib import contextmanager
import inspect
import logging
import os
from os import path
import subprocess
import sys

from offlineimap import OfflineImap
from offlineimap.ui import UI_LIST, UIBase
try:
    import pynotify
    def notify(summary, body):
        pynotify.init(path.basename(sys.argv[0]))
        pynotify.Notification(summary, body).show()
except ImportError:
    def notify(summary, body):
        try:
            subprocess.call(['notify-send', summary, body])
        except OSError:
            logging.error('failed to send notification')

# TODO: is this necessary/useful?
ARGS_IGNORE = ('--info', '-u', '--version', '--dry-run', '-P')

def notify_ui(loglevel, console_output=False):
    class NotifyUI(UIBase.UIBase):
        def __init__(self, config, loglevel = loglevel):
            super(NotifyUI, self).__init__(config, loglevel)
            self.copiedmessages = defaultdict(list)

        _ismaildir = lambda f: isinstance(f, MaildirFolder)

        def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
            if _ismaildir(destfolder):
                self.copiedmessages[destfolder].append(uid)
            UIBase.copyingmessage(self, uid, num, num_to_copy, src, destfolder)

        if 'have to print {new}':
            def skippingfolder

        if not console_output:
            def setup_consolehandler(self):
                """Override to disable logging to console."""
                # TODO: reconsider this feature
                pass
    return NotifyUI

@contextmanager
def sys_argv(argv):
    argv_old = sys.argv
    sys.argv = argv
    yield
    sys.argv = argv_old

def parse_args():
    fmt_default = " (default: %(default)s)"
    parser = ArgumentParser(description=__doc__,
                            epilog='''Additional arguments will be passed
                                   on to offlineimap, but {} are discarded.
                                   '''.format(', '.join(ARGS_IGNORE)))
    parser.add_argument('-p', '--print', dest='format',
                        help='''print total (not limited to this sync)
                             number of new and queued mails
                             (use {new} and/or {queued} in FORMAT)''',
                        nargs='?', const='new: {new}, queued: {queued}')
    parser.add_argument('-Q', '--queue', metavar='DIR',
                        help='location of msmtpq queue, to print {queued}' +
                             fmt_default,
                        default=path.join('~', '.msmtp.queue'))
    parser.add_argument('-n', help='do not send a notification',
                        dest='notify', action='store_false')
    return parser.parse_known_args()

if __name__ == '__main__':
    args, offlineimap_args = parse_args()
    UI_LIST = {'notify': notify_ui(args.loglevel)}
    offlineimap_args = filter(lambda a: a not in ARGS_IGNORE, offlineimap_args)
    offlineimap_args.extend(['-u', 'notify'])
    with sys_argv(offlineimap_args):
        oi = OfflineImap()
        oi.run()
