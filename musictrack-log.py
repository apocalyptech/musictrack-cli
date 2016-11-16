#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Logs an instance of playing a track

import os
import sys
import datetime
from app import App, AppArgumentParser

def activity_log():
    """
    Logs our activity to a logfile in the user's homedir.  Rather improper,
    really, but this is primarily intended for use in our 'log' CLI util
    called from Audacious, and if something fails in actually recording the
    track, I want a log of this stuff that's not dependent on databases
    working, and I'm too lazy to set up a "real" logging system.
    """
    # TODO: If we ever start writing tests for our CLI entry points,
    # we'll have to make sure that this isn't firing.
    try:
        with open(os.path.expanduser(os.path.join('~', 'musictrack-log.txt')), 'a') as df:
            df.write("%s\n" % ('-'*60))
            df.write("Timestamp: %s\n" % (datetime.datetime.now().replace(microsecond=0)))
            df.write("Cwd: %s\n" % (os.getcwd()))
            df.write("Command: %s\n" % (sys.argv))
            df.write("\n")
    except Exception as e:
        print('Error writing to logfile: %s' % (e))

def result_log(line):
    """
    Logs some further activity to our user homedir.  See ``activity_log()``.
    """
    try:
        with open(os.path.expanduser(os.path.join('~', 'musictrack-log.txt')), 'a') as df:
            df.write("%s\n" % (line))
            df.write("\n")
    except Exception as e:
        print('Error writing to logfile: %s' % (e))

def result_logs(lines):
    """
    Logs some further activity to our user homedir.  See ``activity_log()``.
    """
    if len(lines) > 0:
        try:
            with open(os.path.expanduser(os.path.join('~', 'musictrack-log.txt')), 'a') as df:
                for line in lines:
                    df.write("%s\n" % (line))
                df.write("\n")
        except Exception as e:
            print('Error writing to logfile: %s' % (e))

# First up, log what we're doing.
activity_log()

# Now do our stuff:
try:
    # Parse arguments
    parser = AppArgumentParser(
        description='Logs one or more tracks being played.',
        epilog="""For the timestamp argument, many human-readable relative dates
            are supported, such as "2 hours ago."  Anything accepted by the
            parsedatetime module should be fine.  Note that when logging multiple
            tracks at the same time and using the --time option, it will be
            possible to end up with dates in the future if the specified time
            was not far enough in the past.""",
    )

    parser.add_argument('filenames',
        type=str,
        nargs='+',
        metavar='filename',
        help='Filename(s) to log')

    parser.add_argument('-s', '--source',
        choices=['xmms', 'car', 'stereo', 'cafe'],
        default='xmms',
        help='Source of the file being played')

    parser.add_argument('-t', '--time',
        type=str,
        help="""Timestamp to use for the injection.  For a single track,
            defaults to the current time.  For multiple tracks, will default
            to the current time minus the total length of the tracks.""")

    args = parser.parse_args()

    # Do the work
    app = App(args.database)
    (tracks, statuses) = app.log_filenames(args.filenames, source=args.source, timestamp=args.time)
    result_logs(statuses)
    for status in statuses:
        print(status)
    app.close()

except Exception as e:

    result_log(str(e))
    raise e
