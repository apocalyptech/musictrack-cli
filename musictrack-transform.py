#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Transforms all data in the database which still needs it.

from app import App, AppArgumentParser

# Parse arguments
parser = AppArgumentParser(description='Applies transforms which need to be applied')
args = parser.parse_args()

# Do the work
app = App(args.database)
for line in app.apply_transforms():
    print(line)
app.close()
