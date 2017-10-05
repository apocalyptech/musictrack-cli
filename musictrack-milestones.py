#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Attempts to associate tracks with albums, for tracks which don't already have
# an association.

from app import App, AppArgumentParser

# Parse arguments
parser = AppArgumentParser(description='Lists Listened-to Milestones')

parser.add_argument('-i', '--interval',
    type=int,
    default=10000,
    help='Interval to use')

args = parser.parse_args()

# Find out how many tracks we have
app = App(args.database, load_data=False)
app.curs.execute('select count(id) as track_count from track')
row = app.curs.fetchone()
track_count = row['track_count']
print('{:,d} total tracks listened to'.format(track_count))
print('---')

# Now loop through
cur_idx = args.interval-1
while cur_idx < track_count:
    app.curs.execute('select artist, title, album, album_id from track order by timestamp limit {}, 1'.format(cur_idx))
    row = app.curs.fetchone()
    print('{:,d}: {}\'s {}, from {} ({})'.format(cur_idx+1,
        row['artist'],
        row['title'],
        row['album'],
        row['album_id'],
        ))
    cur_idx += args.interval

app.close()
