#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Adds a new album to the database

from app import App, AppArgumentParser

# Parse arguments
parser = AppArgumentParser(description='Adds a new album to the database')

group = parser.add_mutually_exclusive_group()

group.add_argument('-l', '--live',
    action='store_true',
    help='Store as a live album')

group.add_argument('-e', '--ep',
    action='store_true',
    help='Store as an EP')

parser.add_argument('-f', '--force',
    action='store_true',
    help='Force an update, if the album already exists')

parser.add_argument('filenames',
    type=str,
    nargs='+',
    metavar='filename',
    help='Filenames which make up the album')

args = parser.parse_args()

# Collapse our album type down a bit
if args.live:
    album_type = 'live'
elif args.ep:
    album_type = 'ep'
else:
    album_type = 'album'

# Do the work
app = App(args.database)
(added, status) = app.add_album(args.filenames, album_type, force_update=args.force)
print(status)
app.close()
