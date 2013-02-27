#!/usr/bin/python2

from argparse import ArgumentParser
from collections import defaultdict
from contextlib import contextmanager
#import inspect
import logging
import os
#from os import path
import re
import subprocess
import sys

import offlineimap
from offlineimap.folder.Maildir import MaildirFolder
try:
    import pynotify
    def notify(summary, body):
        pynotify.init('OfflineImap')
        pynotify.Notification(summary, body).show()
except ImportError:
    def notify(summary, body):
        try:
            subprocess.call(['notify-send', '-a', 'OfflineImap', summary, body])
        except OSError:
            logging.error('failed to send notification')

def notify_ui(loglevel):
    class NotifyUI(offlineimap.ui.UIBase.UIBase):
        def __init__(self, config, loglevel=loglevel):
            print('init NotifyUI')
            super(NotifyUI, self).__init__(config, loglevel)
            self.newmessages = defaultdict(list)

        def copyingmessage(self, uid, num, num_to_copy, src, destfolder):
            if (isinstance(destfolder, MaildirFolder) and
                'S' not in src.getmessageflags(uid)):
                # TODO: using folder object as key assumes that:
                #   f1.name == f2.name => id(f1) == id(f2)
                self.newmessages[destfolder].append(uid)
            super(NotifyUI, self).copyingmessage(uid, num, num_to_copy, src, destfolder)

        def terminate(self, exitstatus=0, errortitle=None, errormsg=None):
            send_notification(self.newmessages)
            # TODO: check exceptions, change exitstatus to >0
            print('exitstatus={}'.format(exitstatus))
            super(NotifyUI, self).terminate(exitstatus, errortitle, errormsg)

    return NotifyUI

def send_notification(new_mails):
    summary = 'New mail in ' + ', '.join(map(str, new_mails.keys()))
    if len(new_mails) == 1:
        folder, uids = new_mails.pop_item()
        summary += ' in ' + folder
    else:
        pass
    notify(summary, 'body')

def parse_args():
    parser = ArgumentParser(description=__doc__,
                            epilog='''Additional arguments will be passed on to
                                   offlineimap, except for --info.''')
    parser.add_argument('-u', default=logging.WARNING, dest='loglevel',
                        choices={'basic': logging.INFO, 'quiet': logging.WARNING},
                        help='''specify (non-interactive) user interface to use
                             (default: quiet)''')
    parser.add_argument('-n', help='do not send a notification',
                        dest='notify', action='store_false')
    # TODO:
    # -n defeats the purpose of using this script, until exitstatus is
    # influenced (and even then it's probably a bit silly)
    return parser.parse_known_args()

@contextmanager
def sys_argv(argv, prog=None):
    argv_old = sys.argv
    sys.argv = argv[:]
    sys.argv.insert(0, prog or argv_old[0])
    yield
    sys.argv = argv_old

if __name__ == '__main__':
    args, offlineimap_args = parse_args()
    offlineimap.ui.UI_LIST['notify'] = notify_ui(args.loglevel)
    try:
        offlineimap_args.remove('--info')
    except ValueError:
        pass
    offlineimap_args.extend(['-u', 'notify'])
    with sys_argv(offlineimap_args, prog='offlineimap'):
        oi = offlineimap.OfflineImap()
        oi.run()
