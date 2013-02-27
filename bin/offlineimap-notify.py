#!/usr/bin/python2

from argparse import ArgumentParser
from collections import defaultdict
from contextlib import contextmanager
import logging
import os
#from os import path
import re
import subprocess
import sys

from offlineimap import OfflineImap, ui
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

def notify_ui(base_ui):
    class NotifyUI(base_ui):
        def __init__(self, *args, **kwargs):
            super(NotifyUI, self).__init__(*args, **kwargs)
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
    # TODO: get default ui by introspection, selecting the one with min(loglevel)
    parser = ArgumentParser(description=__doc__,
                            epilog='''Additional arguments will be passed on to
                                   offlineimap, except for --info.''')
    parser.add_argument('-u', default='quiet', choices=ui.UI_LIST.keys(),
                        help='''specify (non-interactive) user interface to use
                             (default: quiet)''')
    parser.add_argument('-n', help='do not send a notification',
                        dest='notify', action='store_false')
    # TODO:
    # -n defeats the purpose of using this script, until exitstatus is
    # influenced (and even then it's probably a bit silly)
    args, offlineimap_args = parser.parse_known_args()
    try:
        offlineimap_args.remove('--info')
    except ValueError:
        pass
    offlineimap_args.extend(['-u', args.u])
    return args, offlineimap_args

@contextmanager
def sys_argv(argv, prog=None):
    argv_old = sys.argv
    sys.argv = argv[:]
    sys.argv.insert(0, prog or argv_old[0])
    yield
    sys.argv = argv_old

def modify_ui_list():
    is_noninteractive = lambda (_, cls): cls.__module__ == ui.Noninteractive.__name__
    noninteractive_uis = filter(is_noninteractive, ui.UI_LIST.iteritems())
    ui.UI_LIST.clear()
    ui.UI_LIST.update({name: notify_ui(cls) for name, cls in noninteractive_uis})

if __name__ == '__main__':
    modify_ui_list()
    args, offlineimap_args = parse_args()
    with sys_argv(offlineimap_args, prog='offlineimap'):
        oi = OfflineImap()
        oi.run()
