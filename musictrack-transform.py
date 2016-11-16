#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Transforms all data in the database which still needs it.

from app import App
App.cli_transform()
