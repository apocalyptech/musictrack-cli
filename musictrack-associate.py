#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Attempts to associate tracks with albums, for tracks which don't already have
# an association.

from app import App, AppArgumentParser

# Parse arguments
parser = AppArgumentParser(description='Associates orphan tracks with albums')
args = parser.parse_args()

# Do the work
app = App(args.database)
for line in app.associate_albums():
    print(line)
app.close()
