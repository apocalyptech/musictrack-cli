#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Generates a CSV of yearly tracks-played and hours-listened.  I've
# been slacking off for the past half-decade or so, alas!

import os
import sys
import csv
from app import App, AppArgumentParser

# Parse arguments
parser = AppArgumentParser(description='Generates a CSV of simple yearly stats')

parser.add_argument('-f', '--filename',
    type=str,
    default='-',
    help='Filename to output to.  "-" will go to STDOUT')

args = parser.parse_args()

if args.filename == '-':
    out_file = sys.stdout
else:
    if os.path.exists(args.filename):
        resp = input('File "{}" already exists, overwrite? [y|N] >'.format(args.filename))
        if len(resp) > 0 and resp[0].lower() == 'y':
            print('Continuing...')
        else:
            print('Exiting!')
            sys.exit(1)
    out_file = open(args.filename, 'w')

# Find out which years to process.  Omit the current year
app = App(args.database, load_data=False)
app.curs.execute('select min(timestamp) as min_time, max(timestamp) as max_time from track')
row = app.curs.fetchone()
min_year = row['min_time'].year
max_year = row['max_time'].year

# Write out CSV header
writer = csv.writer(out_file)
writer.writerow(['Year', 'Tracks', 'Hours', 'Minutes Per Track'])

# Now loop through and get our counts
track_counts = {}
seconds_counts = {}
for year in range(min_year, max_year+1):

    where_clause = 'timestamp >= "{thisyear}-01-01 00:00:00" and ' \
            'timestamp < "{nextyear}-01-01 00:00:00"'.format(
                thisyear=year,
                nextyear=year+1,
                )

    # Track counts
    app.curs.execute('select count(id) as track_count from track where {}'.format(where_clause))
    row = app.curs.fetchone()
    track_counts[year] = row['track_count']

    # Hours Listened
    app.curs.execute('select sum(seconds) as seconds_listened from track where {}'.format(where_clause))
    row = app.curs.fetchone()
    seconds_counts[year] = row['seconds_listened']

    # Reports
    writer.writerow([
        year,
        track_counts[year],
        round(seconds_counts[year]/60/60, 2),
        round(seconds_counts[year]/60/track_counts[year], 2),
        ])

# Close our file if we were writing to one
app.close()
if args.filename != '-':
    out_file.close()
print('Done!', file=sys.stderr)
