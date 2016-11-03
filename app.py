#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

import os
import sys
import time
import MySQLdb
import mutagen
import argparse
import datetime
import warnings
import configparser
import parsedatetime

class Transform(object):
    """
    Class to hold a single transform
    """

    def __init__(self, pk, cond_artist=False, cond_album=False, cond_title=False,
            change_artist=False, change_album=False, change_title=False,
            pattern_artist='', pattern_album='', pattern_title='',
            to_artist='', to_album='', to_title=''):
        """
        Constructor
        """
        self.pk = pk
        self.cond_artist = cond_artist
        self.cond_album = cond_album
        self.cond_title = cond_title
        self.change_artist = change_artist
        self.change_album = change_album
        self.change_title = change_title
        self.pattern_artist = pattern_artist
        self.pattern_album = pattern_album
        self.pattern_title = pattern_title
        self.to_artist = to_artist
        self.to_album = to_album
        self.to_title = to_title

    def apply_track(self, track):
        """
        Applies ourself to a track
        """
        # Do our stuff 
        matched = False
        if self.cond_artist or self.cond_album or self.cond_title:
            matched = True
            if self.cond_artist and track.artist != self.pattern_artist:
                matched = False
            if self.cond_album and track.album != self.pattern_album:
                matched = False
            if self.cond_title and track.title != self.pattern_title:
                matched = False

        # Apply our requested changes, if we match
        if matched:
            if self.change_artist:
                if track.artist != self.to_artist:
                    track.artist = self.to_artist
                    track.transformed = True
            if self.change_album:
                if track.album != self.to_album:
                    track.album = self.to_album
                    track.transformed = True
            if self.change_title:
                if track.title != self.to_title:
                    track.title = self.to_title
                    track.transformed = True

        # Update the track with our transform ID
        track.last_transform = self.pk

class TransformList(object):
    """
    Our entire pool of transforms - this is the class that App will
    interact with most of the time.
    """

    def __init__(self):
        """
        Creates a new, empty TransformList object.  These are stored
        in a dict even though they're meant to be looped through sequentially,
        which means that we may end up doing some more work than necessary
        if there are a lot of holes in the numbering, but transforms aren't
        really meant to be deleted (in fact there's no way to do so via the
        web UI where they're added) - if I need to undo a transform I just
        create a newer "undo" type transform.
        """
        self.transforms = {}
        self.max_id = 0

    def add_transform(self, transform):
        """
        Adds a new transform to ourselves.  Note that we only
        accept increasing PKs/IDs on our transforms, and will raise
        an Exception if we get something out of order, or with a
        duplicate ID.
        """

        # Data integrity checks
        if transform.pk in self.transforms:
            raise Exception('Transform with PK %d already in TransformList' % (transform.pk))
        if transform.pk <= self.max_id:
            raise Exception('Max Transform ID in TransformList is %d, refusing to add %d' % (
                self.max_id, transform.pk))

        # Store the new transform
        self.transforms[transform.pk] = transform
        self.max_id = transform.pk

    def apply_track(self, track):
        """
        Applies all necessary transforms to the given track.
        """

        # Return if we have nothing to do
        if track.last_transform >= self.max_id:
            return

        # Otherwise, loop through transforms starting with
        # the one after track.last_transform
        for num in range(track.last_transform+1, self.max_id+1):
            if num in self.transforms:
                self.transforms[num].apply_track(track)

    def __len__(self):
        """
        Convenience function to get our length
        """
        return len(self.transforms)

    @staticmethod
    def int_to_bool(row, varname):
        """
        Convenience method to assign a database boolean to a Python
        boolean
        """
        if row[varname] == 1:
            return True
        else:
            return False

    @staticmethod
    def from_database(curs):
        """
        Given the database cursor ``curs``, return a new TransformList object
        based on the transforms found in the database
        """

        tflist = TransformList()

        curs.execute('select * from transform order by tid')
        for row in curs.fetchall():
            tflist.add_transform(Transform(row['tid'],
                cond_artist = TransformList.int_to_bool(row, 'artistcond'),
                cond_album = TransformList.int_to_bool(row, 'albumcond'),
                cond_title = TransformList.int_to_bool(row, 'titlecond'),
                change_artist = TransformList.int_to_bool(row, 'artistchange'),
                change_album = TransformList.int_to_bool(row, 'albumchange'),
                change_title = TransformList.int_to_bool(row, 'titlechange'),
                pattern_artist = row['artistpat'],
                pattern_album = row['albumpat'],
                pattern_title = row['titlepat'],
                to_artist = row['artistto'],
                to_album = row['albumto'],
                to_title = row['titleto'],
            ))

        return tflist

class Track(object):
    """
    Information about a track
    """

    def __init__(self, artist='', album='', title='',
            tracknum=None, seconds=0):
        """
        Constructor!
        """
        self.artist = artist
        self.album = album
        self.title = title
        self.tracknum = tracknum
        self.seconds = seconds

        self.album_id = 0

        self.last_transform = 0
        self.transformed = False

        # Only populated when database actions occur
        self.pk = 0

    def insert(self, db, curs, source, timestamp, commit=True):
        """
        Inserts ourself into the database.  ``timestamp`` should be a
        ``datetime.datetime`` object.  Returns the database ID of the
        new track.  If ``commit`` is ``False``, we will not commit
        the transaction (making passing in ``db`` silly, but whatever).
        """

        # Make a list of our fields, and our data
        fields = ['lasttransform', 'album_id', 'artist', 'album',
            'title', 'source', 'timestamp', 'seconds']
        data = [self.last_transform, self.album_id,
            self.artist, self.album, self.title,
            source, timestamp, self.seconds]
        if self.tracknum is not None:
            fields.append('tracknum')
            data.append(self.tracknum)
        
        # Construct our insert sql
        sql = 'insert into track (%s) values (%s)' % (
            ', '.join(fields),
            ', '.join('%s' for field in fields))

        # .... aaand run it!
        curs.execute(sql, data)
        if commit:
            db.commit()

        # Return our created ID
        self.pk = curs.lastrowid
        return curs.lastrowid

    def status_str(self):
        """
        Returns a str which identifies ourself for logging purposes
        """
        return 'ID %d: %s / %s (album %d) - %s' % (
            self.pk, self.artist, self.album, self.album_id, self.title)

    @staticmethod
    def from_filename(filename):
        """
        Reads file information from a filename
        """

        if not os.path.exists(filename):
            raise Exception('"%s" is not found' % (filename))

        audio = mutagen.File(filename)

        artist = ''
        album = ''
        title = ''
        tracknum = None
        seconds = None

        if str(type(audio)) == "<class 'mutagen.mp3.MP3'>":
            if 'TPE1' in audio:
                artist = str(audio['TPE1']).strip().strip("\x00")
            if 'TALB' in audio: 
                album = str(audio['TALB']).strip().strip("\x00")
            if 'TIT2' in audio: 
                title = str(audio['TIT2']).strip().strip("\x00")
            if 'TRCK' in audio:
                tracknum = str(audio['TRCK']).strip().strip("\x00")
                if '/' in tracknum:
                    tracknum = tracknum.split('/', 2)[0]
                try:
                    tracknum = int(tracknum)
                except ValueError: # pragma: no cover
                    tracknum = None
            seconds = audio.info.length

        elif (str(type(audio)) == "<class 'mutagen.oggvorbis.OggVorbis'>" or
                str(type(audio)) == "<class 'mutagen.flac.FLAC'>"):
            if 'artist' in audio:
                artist = str(audio['artist'][0]).strip().strip("\x00")
            if 'album' in audio:
                album = str(audio['album'][0]).strip().strip("\x00")
            if 'title' in audio:
                title = str(audio['title'][0]).strip().strip("\x00")
            if 'tracknumber' in audio:
                tracknum = str(audio['tracknumber'][0]).strip().strip("\x00")
                # Not sure if Ogg tags actually do this or not
                if '/' in tracknum: # pragma: no cover
                    tracknum = tracknum.split('/', 2)[0]
                try:
                    tracknum = int(tracknum)
                except ValueError:  # pragma: no cover
                    tracknum = None
            seconds = audio.info.length

        elif (str(type(audio)) == "<class 'mutagen.mp4.MP4'>"):
            # NOTE: mp4 tags don't seem to support either ensemble/group/tpe2 or
            # conductor/tpe3 tags the way the other tag systems do, so mp4 files
            # will never load in those values.
            if '\xa9ART' in audio:
                artist = str(audio['\xa9ART'][0]).strip().strip("\x00")
            if '\xa9alb' in audio:
                album = str(audio['\xa9alb'][0]).strip().strip("\x00")
            if '\xa9nam' in audio:
                title = str(audio['\xa9nam'][0]).strip().strip("\x00")
            if 'trkn' in audio:
                (tracknum, total_tracks) = audio['trkn'][0]
                try:
                    tracknum = int(tracknum)
                except ValueError:  # pragma: no cover
                    tracknum = None
            seconds = audio.info.length

        else:
            raise Exception('%s: Audio type not understood: %s' % (filename, type(audio)))

        return Track(artist=artist,
            album=album,
            title=title,
            tracknum=tracknum,
            seconds=seconds)

class AppArgumentParser(argparse.ArgumentParser):
    """
    Custom argument parser which always supports the --database flag
    """

    def __init__(self, *args, **kwargs):

        super(AppArgumentParser, self).__init__(*args,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            **kwargs)

        self.add_argument('-d', '--database',
            type=str,
            default=App.default_database,
            help="Database definition INI file to connect to")

class App(object):
    """
    Class to hold our main app logic - Static methods for each CLI
    utility are defined, which set up their own argparse configurations,
    and non-static methods do the actual work.
    """

    default_database = 'db.ini'

    schema_track_drop = 'drop table if exists track'
    schema_track_truncate = 'truncate track'
    schema_track = """create table track (   
            id int not null auto_increment,
            timestamp datetime, 
            artist varchar(200) not null,
            title varchar(200) not null,
            album varchar(200),
            tracknum int,
            seconds int, 
            source enum('xmms', 'car', 'stereo', 'cafe'),
            album_id int default 0,
            lasttransform int not null default 0,
            primary key (id),
            index idx_artist (artist),
            index idx_title (title),
            index idx_album (album)
        ) engine=innodb"""

    schema_album_drop = 'drop table if exists album'
    schema_album_truncate = 'truncate album'
    schema_album = """create table album (   
            alid int not null auto_increment,
            alartist varchar(200) not null,
            alalbum varchar(200) not null,
            totaltracks int not null,
            totalseconds int not null,
            lasttransform int not null default 0,
            altype enum('album', 'ep', 'live') default 'album',
            primary key (alid),
            unique index idx_total (alartist, alalbum)
        ) engine=innodb"""

    schema_transform_drop = 'drop table if exists transform'
    schema_transform_truncate = 'truncate transform'
    schema_transform = """create table transform (   
            tid int not null auto_increment,
            artistcond bool not null default 0,
            albumcond bool not null default 0,
            titlecond bool not null default 0,
            artistchange bool not null default 0,
            albumchange bool not null default 0,
            titlechange bool not null default 0,
            artistpat varchar(200),
            albumpat varchar(200),
            titlepat varchar(200),
            artistto varchar(200),
            albumto varchar(200),
            titleto varchar(200), 
            primary key (tid)
        ) engine=innodb"""

    def __init__(self, database, load_data=True):
        """
        Initializations common to all our utils.  Pass in a database INI
        file as ``database``.  If ``load_data`` is passed in as ``False``,
        we won't try to load transforms or association data.
        """

        # Read our configuration variables (database, mostly)
        ini_path = os.path.join(os.path.dirname(__file__), database)
        if not os.path.exists(ini_path):
            raise Exception('Database INI file "%s" not found' % (ini_path))
        config = configparser.ConfigParser()
        config.read(ini_path)
        if 'database' not in config:
            raise Exception('"database" configuration not found in "%s"' % (ini_path))
        section = config['database']
        for name in ['host', 'name', 'user', 'pass']:
            if name not in section:
                raise Exception('Configuration val "%s" not found in "%s"' % (name, ini_path))
        db_host = section['host']
        db_name = section['name']
        db_user = section['user']
        db_pass = section['pass']

        # Now connect to the database to make sure we're good there.
        self.db = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        self.curs = self.db.cursor(MySQLdb.cursors.DictCursor)

        # Set sql_mode to traditional.  This will cause Exceptions to be thrown for stuff
        # which would otherwise only throw warnings
        self.curs.execute('SET @@sql_mode:=TRADITIONAL')

        # Get our transforms
        if load_data:
            self.load_data()
        else:
            self.transforms = None

    def load_data(self):
        """
        Loads our data from the database, such as transforms and associations
        """
        self.transforms = TransformList.from_database(self.curs)

    def set_album_id(self, track):
        """
        Sets the album associated with the passed-in ``track``, if possible.  Updates
        the ``track`` object, and also returns the album ID.  Returns 0 if no album can
        be found.
        """

        # Try a specific album by the artist
        self.curs.execute('select alid from album where alartist=%s and alalbum=%s limit 1',
            (track.artist, track.album))
        if self.curs.rowcount == 1:
            row = self.curs.fetchone()
            track.album_id = row['alid']
            return row['alid']
        
        # Try for Various-Artists albums
        self.curs.execute('select alid from album where alartist=%s and alalbum=%s limit 1',
            ('Various', track.album))
        if self.curs.rowcount == 1:
            row = self.curs.fetchone()
            track.album_id = row['alid']
            return row['alid']

        # Fall back to 0
        track.album_id = 0
        return 0

    def close(self):
        """
        Cleanup routines.  Not *really* needed, but whatever.
        """
        self.curs.close()
        self.db.close()

    def _initialize_db(self):
        """
        Initializes a new database (just creating our schema, basically).  Not really
        intended to be used outside of our test suite.
        """
        self.curs.execute(self.schema_album)
        self.curs.execute(self.schema_track)
        self.curs.execute(self.schema_transform)

    def _truncate_db(self):
        """
        Truncates all tables from our database.  Use with caution, yes?  Not really
        intended to be used outside of our test suite.  In fact, we're going to test
        for the presence of the string 'test' in the database name before we do
        anything.
        """
        self.curs.execute('select database()')
        row = self.curs.fetchone()
        if 'test' in row['database()']:
            self.curs.execute(self.schema_transform_truncate)
            self.curs.execute(self.schema_track_truncate)
            self.curs.execute(self.schema_album_truncate)
        else:   # pragma: no cover
            raise Exception('Refusing to truncate tables on non-test database')

    def _drop_db(self):
        """
        Drops all tables from our database.  Use with caution, yes?  Not really intended
        to be used outside of our test suite.  In fact, we're going to test
        for the presence of the string 'test' in the database name before we do
        anything.
        """
        self.curs.execute('select database()')
        row = self.curs.fetchone()
        if 'test' in row['database()']:
            self.curs.execute(self.schema_transform_drop)
            self.curs.execute(self.schema_track_drop)
            self.curs.execute(self.schema_album_drop)
        else:   # pragma: no cover
            raise Exception('Refusing to drop tables on non-test database')

    def log_track(self, track, source='xmms', timestamp=None, commit=True):
        """
        Logs an instance of playing a track, given a Track object.  Returns
        the Track object.  ``timestamp`` should be a ``datetime.datetime``
        object, but will default to the current time if not specified.
        If ``commit`` is passed in as ``False``, the transaction will not
        be committed.
        """

        # Default to now, if not given a timestamp
        if timestamp is None:
            timestamp = datetime.datetime.now()

        # Apply transforms
        self.transforms.apply_track(track)

        # Associate with an album, if possible
        self.set_album_id(track)

        # Save to the database
        track.insert(self.db, self.curs, source, timestamp, commit=commit)

        # Return
        return track

    def log_filenames(self, filenames, source='xmms', timestamp=None):
        """
        Logs the specified filenames.  ``filenames`` should be a list of
        strings containing the filenames, but can also be a string, in which
        case only that one filename will be processed.  ``timestamp`` should
        be a text value, most likely passed in from the user.  Returns a
        tuple, whose first element is the list of Track objects added, and
        whose second element is a list of statuses suitable for logging or
        displaying to the user.
        """

        # If we've been passed a string, turn it into a list.  Not too proper,
        # but convenient.
        if isinstance(filenames, str):
            filenames = [filenames]

        # Parse our time now, in case it's invalid.
        if timestamp is None:
            timestamp_start = time.localtime()
        else:
            # parsedatetime says that VERSION_FLAG_STYLE (the default) will be deprecated in
            # 2.0 and to start using VERSION_CONTEXT_STYLE instead, but there's no docs for
            # doing so online and naively just setting it causes stuff to Not Work, and I don't
            # particularly feel like grabbing the code and building the docs myself.  So,
            # whatever.  I'm using the soon-to-be-deprecated stuff instead.
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                cal = parsedatetime.Calendar(version=parsedatetime.VERSION_FLAG_STYLE)
                (timestamp_start, status) = cal.parse(timestamp)
                if status == 0:
                    raise Exception('Could not parse requested timestamp of "%s"' % (timestamp))
        timestamp_start = datetime.datetime.fromtimestamp(time.mktime(timestamp_start))

        # Now process
        statuses = []
        tracks = []
        if len(filenames) == 0:
            statuses.append('No filenames specified')
        elif len(filenames) == 1:
            track = self.log_track(
                Track.from_filename(filenames[0]),
                source=source,
                timestamp=timestamp_start)
            tracks.append(track)
            statuses.append('Track logged: %s' % (track.status_str()))
        else:
            total_seconds = 0
            for filename in filenames:
                tracks.append(Track.from_filename(filename))
                total_seconds += tracks[-1].seconds
            if timestamp is None:
                timestamp_start -= datetime.timedelta(seconds=total_seconds)
            for track in tracks:
                self.log_track(track,
                    source=source,
                    timestamp=timestamp_start,
                    commit=False)
                statuses.append('Track logged at "%s": %s' % (
                    timestamp_start.replace(microsecond=0),
                    track.status_str()))
                timestamp_start += datetime.timedelta(seconds=track.seconds)
            self.db.commit()

        # Return what we did
        return (tracks, statuses)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def cli_log():
        """
        Logs an instance of playing one or more tracks.  Static entry for commandline use.
        """

        # First up, log what we're doing.
        App.activity_log()
        
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
            App.result_logs(statuses)
            for status in statuses:
                print(status)
            app.close()

        except Exception as e:

            App.result_log(str(e))
            raise e
