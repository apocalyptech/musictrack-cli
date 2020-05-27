#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

import os
import uuid
import shutil
import unittest
import datetime
import tempfile

from mutagen import id3

from app import App, AppArgumentParser, Album, Track, Transform, TransformList

class DatabaseTest(unittest.TestCase):
    """
    Class for our music tracker which require a testing database.
    """

    def setUp(self):
        self.app = App('dbtests.ini')
        self.app._truncate_db()

    def tearDown(self):
        self.app.close()

    def add_transform(self, cond_artist=False, cond_album=False, cond_title=False,
            cond_ensemble=False, cond_composer=False, cond_conductor=False,
            change_artist=False, change_album=False, change_title=False,
            change_ensemble=False, change_composer=False, change_conductor=False,
            pattern_artist='', pattern_album='', pattern_title='',
            pattern_ensemble='', pattern_composer='', pattern_conductor='',
            to_artist='', to_album='', to_title='',
            to_ensemble='', to_composer='', to_conductor='',
            commit=True):
        """
        Adds a new transform to our database, given the specified attributes.  Will
        commit by default, but if you pass in ``commit`` = ``False`` we will not.
        Returns the primary key of the new transform.
        """
        self.app.curs.execute("""insert into transform (
            artistcond, albumcond, titlecond,
            ensemblecond, composercond, conductorcond,
            artistchange, albumchange, titlechange,
            ensemblechange, composerchange, conductorchange,
            artistpat, albumpat, titlepat,
            ensemblepat, composerpat, conductorpat,
            artistto, albumto, titleto,
            ensembleto, composerto, conductorto) values (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s)""", (
                cond_artist, cond_album, cond_title,
                cond_ensemble, cond_composer, cond_conductor,
                change_artist, change_album, change_title,
                change_ensemble, change_composer, change_conductor,
                pattern_artist, pattern_album, pattern_title,
                pattern_ensemble, pattern_composer, pattern_conductor,
                to_artist, to_album, to_title,
                to_ensemble, to_composer, to_conductor,
        ))
        if commit:
            self.app.db.commit()
        return self.app.curs.lastrowid

    def add_album(self, artist='', album='', totaltracks=0, totalseconds=0,
            altype='album', commit=True):
        """
        Adds a new album to our database, given the specified attributes.  Will
        commit by default, but if you pass in ``commit`` = ``False`` we will not.
        Returns the primary key of the new album.
        """
        self.app.curs.execute("""insert into album(
            alartist, alalbum, totaltracks, totalseconds, altype
            ) values ( %s, %s, %s, %s, %s)""", (
                artist, album, totaltracks, totalseconds, altype
        ))
        if commit:
            self.app.db.commit()
        return self.app.curs.lastrowid

    def get_album_count(self):
        """
        Gets a count of albums in our database
        """
        self.app.curs.execute('select count(*) c from album')
        if self.app.curs.rowcount == 1:
            row = self.app.curs.fetchone()
            return row['c']
        else:   # pragma: no cover
            return 0

    def get_track_count(self):
        """
        Gets a count of tracks in our database
        """
        self.app.curs.execute('select count(*) c from track')
        if self.app.curs.rowcount == 1:
            row = self.app.curs.fetchone()
            return row['c']
        else:   # pragma: no cover
            return 0

    def get_album_by_id(self, album_id):
        """
        Gets an album by album ID.  Returns the row.
        """
        self.app.curs.execute('select * from album where alid=%s', (album_id,))
        if self.app.curs.rowcount == 1:
            return self.app.curs.fetchone()
        else:   # pragma: no cover
            return None

    def get_track_by_id(self, track_id):
        """
        Gets a track by track ID.  Returns the row.
        """
        self.app.curs.execute('select * from track where id=%s', (track_id,))
        if self.app.curs.rowcount == 1:
            return self.app.curs.fetchone()
        else:   # pragma: no cover
            return None

class TransformTests(unittest.TestCase):
    """
    Testing our Transform class
    """
    
    def test_transform_track_no_changes(self):
        """
        Given a track, apply a transformation which does nothing
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', conductor='Conductor', composer='Composer',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_artist=True, change_artist=True,
            pattern_artist='Foo', to_artist='Bar')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.ensemble, 'Ensemble')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_empty_transform(self):
        """
        Given a track, apply a transformation which will never match on
        anything.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', conductor='Conductor', composer='Composer',
            tracknum=1, seconds=60)
        transform = Transform(1,
            change_artist=True, pattern_artist='Artist', to_artist='Artist 2',
            change_album=True, pattern_album='Album', to_album='Album 2',
            change_title=True, pattern_title='Title', to_title='Title 2',
            change_ensemble=True, pattern_ensemble='Ensemble', to_ensemble='Ensemble 2',
            change_composer=True, pattern_composer='Composer', to_composer='Composer 2',
            change_conductor=True, pattern_conductor='Conductor', to_conductor='Conductor 2',
            )

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.ensemble, 'Ensemble')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_change_artist(self):
        """
        Given a track, apply a transformation which changes the artist
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_change_album(self):
        """
        Given a track, apply a transformation which changes the album
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_change_title(self):
        """
        Given a track, apply a transformation which changes the title
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_title=True, change_title=True,
            pattern_title='Title', to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_change_ensemble(self):
        """
        Given a track, apply a transformation which changes the ensemble
        """
        track = Track(artist='Artist', album='Album', ensemble='Ensemble',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_ensemble=True, change_ensemble=True,
            pattern_ensemble='Ensemble', to_ensemble='Ensemble 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.ensemble, 'Ensemble 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_change_composer(self):
        """
        Given a track, apply a transformation which changes the composer
        """
        track = Track(artist='Artist', album='Album', composer='Composer',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_composer=True, change_composer=True,
            pattern_composer='Composer', to_composer='Composer 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.composer, 'Composer 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_change_conductor(self):
        """
        Given a track, apply a transformation which changes the conductor
        """
        track = Track(artist='Artist', album='Album', conductor='Conductor',
            tracknum=1, seconds=60)
        transform = Transform(1, cond_conductor=True, change_conductor=True,
            pattern_conductor='Conductor', to_conductor='Conductor 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.conductor, 'Conductor 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_full_transform(self):
        """
        Given a track, apply a transformation which matches on all fields.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', conductor='Conductor', composer='Composer',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True, pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True, pattern_album='Album', to_album='Album 2',
            cond_title=True, change_title=True, pattern_title='Title', to_title='Title 2',
            cond_ensemble=True, change_ensemble=True, pattern_ensemble='Ensemble', to_ensemble='Ensemble 2',
            cond_composer=True, change_composer=True, pattern_composer='Composer', to_composer='Composer 2',
            cond_conductor=True, change_conductor=True, pattern_conductor='Conductor', to_conductor='Conductor 2',
            )

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.ensemble, 'Ensemble 2')
        self.assertEqual(track.conductor, 'Conductor 2')
        self.assertEqual(track.composer, 'Composer 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_album_based_on_artist_album_match(self):
        """
        Given a track, transform its album based on matching both the artist and album.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_album_based_on_artist_album_no_match_album(self):
        """
        Given a track, transform its album based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect album.
        """
        track = Track(artist='Artist', album='Album 3', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 3')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_album_based_on_artist_album_no_match_artist(self):
        """
        Given a track, transform its album based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 2', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_artist_based_on_artist_album_match(self):
        """
        Given a track, transform its artist based on matching both the artist and album.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_album=True, pattern_album='Album',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_artist_based_on_artist_album_no_match_album(self):
        """
        Given a track, transform its artist based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect album.
        """
        track = Track(artist='Artist', album='Album 2', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_album=True, pattern_album='Album',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_artist_based_on_artist_album_no_match_artist(self):
        """
        Given a track, transform its artist based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 3', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_album=True, pattern_album='Album',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 3')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_title_based_on_artist_title_match(self):
        """
        Given a track, transform its title based on matching both the artist and title.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_title_based_on_artist_title_no_match_title(self):
        """
        Given a track, transform its title based on matching both the artist and title.
        Will NOT match the tested track, based on an incorrect title.
        """
        track = Track(artist='Artist', album='Album', title='Title 3',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 3')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_title_based_on_artist_title_no_match_artist(self):
        """
        Given a track, transform its title based on matching both the artist and title.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 2', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_artist_based_on_artist_title_match(self):
        """
        Given a track, transform its artist based on matching both the artist and title.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_title=True, pattern_title='Title',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_artist_based_on_artist_title_no_match_title(self):
        """
        Given a track, transform its artist based on matching both the artist and title.
        Will NOT match the tested track, based on an incorrect title.
        """
        track = Track(artist='Artist', album='Album', title='Title 2',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_title=True, pattern_title='Title',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_artist_based_on_artist_title_no_match_artist(self):
        """
        Given a track, transform its artist based on matching both the artist and title.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 3', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_title=True, pattern_title='Title',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 3')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_album_based_on_album_title_match(self):
        """
        Given a track, transform its album based on matching both the album and title.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_album=True, pattern_album = 'Album',
            cond_title=True, pattern_title='Title',
            change_album=True, to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_album_based_on_album_title_no_match_title(self):
        """
        Given a track, transform its album based on matching both the album and title.
        Will NOT match the tested track, based on an incorrect title.
        """
        track = Track(artist='Artist', album='Album', title='Title 2',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_album=True, pattern_album = 'Album',
            cond_title=True, pattern_title='Title',
            change_album=True, to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_album_based_on_album_title_no_match_album(self):
        """
        Given a track, transform its album based on matching both the album and title.
        Will NOT match the tested track, based on an incorrect album.
        """
        track = Track(artist='Artist', album='Album 3', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_album=True, pattern_album = 'Album',
            cond_title=True, pattern_title='Title',
            change_album=True, to_album='Album 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 3')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_title_based_on_album_title_match(self):
        """
        Given a track, transform its title based on matching both the album and title.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_album=True, pattern_album = 'Album',
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_title_based_on_album_title_no_match_title(self):
        """
        Given a track, transform its title based on matching both the album and title.
        Will NOT match the tested track, based on an incorrect title.
        """
        track = Track(artist='Artist', album='Album', title='Title 3',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_album=True, pattern_album = 'Album',
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 3')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_title_based_on_album_title_no_match_album(self):
        """
        Given a track, transform its title based on matching both the album and title.
        Will NOT match the tested track, based on an incorrect album.
        """
        track = Track(artist='Artist', album='Album 2', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_album=True, pattern_album = 'Album',
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_title_based_on_artist_album_match(self):
        """
        Given a track, transform its title based on matching both the artist and album.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, pattern_album = 'Album',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_track_title_based_on_artist_album_no_match_artist(self):
        """
        Given a track, transform its title based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 2', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, pattern_album = 'Album',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_title_based_on_artist_album_no_match_album(self):
        """
        Given a track, transform its title based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect album.
        """
        track = Track(artist='Artist', album='Album 2', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, pattern_album = 'Album',
            change_title=True, to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

    def test_transform_track_ensemble_based_on_artist_ensemble_match(self):
        """
        Given a track, transform its ensemble based on matching both the artist and ensemble.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_ensemble=True, change_ensemble=True,
            pattern_ensemble='Ensemble', to_ensemble='Ensemble 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.ensemble, 'Ensemble 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_ensemble_based_on_artist_ensemble_no_match_ensemble(self):
        """
        Given a track, transform its ensemble based on matching both the artist and ensemble.
        Will NOT match the tested track, based on an incorrect ensemble.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble 3',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_ensemble=True, change_ensemble=True,
            pattern_ensemble='Ensemble', to_ensemble='Ensemble 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.ensemble, 'Ensemble 3')
        self.assertEqual(track.transformed, False)

    def test_transform_track_ensemble_based_on_artist_ensemble_no_match_artist(self):
        """
        Given a track, transform its ensemble based on matching both the artist and ensemble.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 2', album='Album', title='Title',
            ensemble='Ensemble',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_ensemble=True, change_ensemble=True,
            pattern_ensemble='Ensemble', to_ensemble='Ensemble 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.ensemble, 'Ensemble')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

    def test_transform_track_conductor_based_on_artist_conductor_match(self):
        """
        Given a track, transform its conductor based on matching both the artist and conductor.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            conductor='Conductor',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_conductor=True, change_conductor=True,
            pattern_conductor='Conductor', to_conductor='Conductor 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.conductor, 'Conductor 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_conductor_based_on_artist_conductor_no_match_conductor(self):
        """
        Given a track, transform its conductor based on matching both the artist and conductor.
        Will NOT match the tested track, based on an incorrect conductor.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            conductor='Conductor 3',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_conductor=True, change_conductor=True,
            pattern_conductor='Conductor', to_conductor='Conductor 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.conductor, 'Conductor 3')
        self.assertEqual(track.transformed, False)

    def test_transform_track_conductor_based_on_artist_conductor_no_match_artist(self):
        """
        Given a track, transform its conductor based on matching both the artist and conductor.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 2', album='Album', title='Title',
            conductor='Conductor',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_conductor=True, change_conductor=True,
            pattern_conductor='Conductor', to_conductor='Conductor 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

    def test_transform_track_composer_based_on_artist_composer_match(self):
        """
        Given a track, transform its composer based on matching both the artist and composer.
        Will match the tested track.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            composer='Composer',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_composer=True, change_composer=True,
            pattern_composer='Composer', to_composer='Composer 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.composer, 'Composer 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_composer_based_on_artist_composer_no_match_composer(self):
        """
        Given a track, transform its composer based on matching both the artist and composer.
        Will NOT match the tested track, based on an incorrect composer.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            composer='Composer 3',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_composer=True, change_composer=True,
            pattern_composer='Composer', to_composer='Composer 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.composer, 'Composer 3')
        self.assertEqual(track.transformed, False)

    def test_transform_track_composer_based_on_artist_composer_no_match_artist(self):
        """
        Given a track, transform its composer based on matching both the artist and composer.
        Will NOT match the tested track, based on an incorrect artist.
        """
        track = Track(artist='Artist 2', album='Album', title='Title',
            composer='Composer',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_composer=True, change_composer=True,
            pattern_composer='Composer', to_composer='Composer 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_album_no_changes(self):
        """
        Given an album, apply a transformation which does nothing
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1, cond_artist=True, change_artist=True,
            pattern_artist='Foo', to_artist='Bar')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_empty_transform(self):
        """
        Given an album, apply a transformation which will never match on
        anything.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            change_artist=True, pattern_artist='Artist', to_artist='Artist 2',
            change_album=True, pattern_album='Album', to_album='Album 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_titlecond_specified(self):
        """
        Given an album, apply a transformation which has a condition on the
        title (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            cond_title=True,
            pattern_title='Title')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_titlechange_specified(self):
        """
        Given an album, apply a transformation which has a change on the
        title (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            change_title=True,
            to_title='Title 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_ensemblecond_specified(self):
        """
        Given an album, apply a transformation which has a condition on the
        ensemble (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            cond_ensemble=True,
            pattern_ensemble='Ensemble')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_ensemblechange_specified(self):
        """
        Given an album, apply a transformation which has a change on the
        ensemble (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            change_ensemble=True,
            to_ensemble='Ensemble 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_conductorcond_specified(self):
        """
        Given an album, apply a transformation which has a condition on the
        conductor (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            cond_conductor=True,
            pattern_conductor='Conductor')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_conductorchange_specified(self):
        """
        Given an album, apply a transformation which has a change on the
        conductor (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            change_conductor=True,
            to_conductor='Conductor 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_composercond_specified(self):
        """
        Given an album, apply a transformation which has a condition on the
        composer (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            cond_composer=True,
            pattern_composer='Composer')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_with_composerchange_specified(self):
        """
        Given an album, apply a transformation which has a change on the
        composer (the transform should not be applied at all)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2',
            change_composer=True,
            to_composer='Composer 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_change_artist(self):
        """
        Given an album, apply a transformation which changes the artist
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1, cond_artist=True, change_artist=True,
            pattern_artist='Artist', to_artist='Artist 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.transformed, True)
    
    def test_transform_album_change_album(self):
        """
        Given an album, apply a transformation which changes the album
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1, cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)
    
    def test_transform_album_full_transform(self):
        """
        Given an album, apply a transformation which matches on all fields.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True, pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True, pattern_album='Album', to_album='Album 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)
    
    def test_transform_album_album_based_on_artist_album_match(self):
        """
        Given an album, transform its album based on matching both the artist and album.
        Will match the tested album.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)
    
    def test_transform_album_album_based_on_artist_album_no_match_album(self):
        """
        Given an album, transform its album based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect album.
        """
        album = Album(artist='Artist', album='Album 3',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album 3')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_album_based_on_artist_album_no_match_artist(self):
        """
        Given an album, transform its album based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect artist.
        """
        album = Album(artist='Artist 2', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist='Artist',
            cond_album=True, change_album=True,
            pattern_album='Album', to_album='Album 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_artist_based_on_artist_album_match(self):
        """
        Given an album, transform its artist based on matching both the artist and album.
        Will match the tested album.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_album=True, pattern_album='Album',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, True)
    
    def test_transform_album_artist_based_on_artist_album_no_match_album(self):
        """
        Given an album, transform its artist based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect album.
        """
        album = Album(artist='Artist', album='Album 2',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_album=True, pattern_album='Album',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, False)
    
    def test_transform_album_artist_based_on_artist_album_no_match_artist(self):
        """
        Given an album, transform its artist based on matching both the artist and album.
        Will NOT match the tested track, based on an incorrect artist.
        """
        album = Album(artist='Artist 3', album='Album',
            totaltracks=1, totalseconds=60)
        transform = Transform(1,
            cond_artist=True, pattern_artist = 'Artist',
            cond_album=True, pattern_album='Album',
            change_artist=True, to_artist='Artist 2')

        self.assertEqual(album.last_transform, 0)
        transform.apply_album(album)
        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist 3')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)

class TransformListTests(unittest.TestCase):
    """
    Tests for our TransformList class
    """

    def test_empty_transformlist(self):
        """
        Ensure that a newly-created transformlist contains no transforms
        """
        tflist = TransformList()
        self.assertEqual(len(tflist), 0)

    def test_add_single_transform(self):
        """
        Add a single transform to our transformlist
        """
        tflist = TransformList()
        tflist.add_transform(Transform(1))
        self.assertEqual(len(tflist), 1)

    def test_add_two_transforms(self):
        """
        Add two transforms to our transformlist
        """
        tflist = TransformList()
        tflist.add_transform(Transform(1))
        tflist.add_transform(Transform(2))
        self.assertEqual(len(tflist), 2)

    def test_add_duplicate_transform_id(self):
        """
        Test adding a duplicate transform ID to our list - should raise an Exception
        """
        tflist = TransformList()
        tflist.add_transform(Transform(1))
        with self.assertRaises(Exception):
            tflist.add_transform(Transform(1))
        self.assertEqual(len(tflist), 1)

    def test_add_transforms_out_of_order(self):
        """
        Test adding transform IDs out of order to our list - should raise an Exception
        """
        tflist = TransformList()
        tflist.add_transform(Transform(2))
        with self.assertRaises(Exception):
            tflist.add_transform(Transform(1))
        self.assertEqual(len(tflist), 1)

    def test_int_to_bool_true(self):
        """
        Test our static helper ``int_to_bool`` method with a true value
        """
        self.assertEqual(TransformList.int_to_bool({'varname': 1}, 'varname'), True)

    def test_int_to_bool_false(self):
        """
        Test our static helper ``int_to_bool`` method with a false value
        """
        self.assertEqual(TransformList.int_to_bool({'varname': 0}, 'varname'), False)

    def test_transform_album_with_single_transform(self):
        """
        Transforms an album with a single transform in the database
        """
        album = Album(artist='Artist', album='Album')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.transformed, True)

    def test_transform_album_with_single_transform_high_id(self):
        """
        Transforms an album with a single transform in the database, with
        a high ID in the database.
        """
        album = Album(artist='Artist', album='Album')
        tflist = TransformList()
        tflist.add_transform(Transform(100,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 100)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.transformed, True)

    def test_transform_album_with_two_transforms(self):
        """
        Transforms an album with a two transforms in the database
        """
        album = Album(artist='Artist', album='Album')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(2,
            cond_album=True, pattern_album='Album',
            change_album=True, to_album='Album 2',
        ))

        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 2)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)

    def test_transform_album_with_two_transforms_with_gap_in_numbering(self):
        """
        Transforms an album with a two transforms in the database, when
        there's a gap in the numbering
        """
        album = Album(artist='Artist', album='Album')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(3,
            cond_album=True, pattern_album='Album',
            change_album=True, to_album='Album 2',
        ))

        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 3)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)

    def test_transform_album_with_two_transforms_with_gap_in_numbering_and_one_already_applied(self):
        """
        Transforms an album with a two transforms in the database, when
        there's a gap in the numbering, and the earlier transform has
        already been applied.
        """
        album = Album(artist='Artist', album='Album', last_transform=2)
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(3,
            cond_album=True, pattern_album='Album',
            change_album=True, to_album='Album 2',
        ))

        self.assertEqual(album.last_transform, 2)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 3)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)

    def test_transform_album_with_two_transforms_undo(self):
        """
        Transforms an album with a two transforms in the database, which
        undo each other.  Technically we should probably have something
        smart enough to find out if the end result has changed, but in
        the interests of laziness we'll just cope with possibly having
        superfluous database calls.
        """
        album = Album(artist='Artist', album='Album')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(2,
            cond_artist=True, pattern_artist='Artist 2',
            change_artist=True, to_artist='Artist',
        ))

        self.assertEqual(album.last_transform, 0)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 2)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, True)

    def test_no_transform_album_with_already_applied_transform(self):
        """
        Sets up an album to have already been processed by a transform.
        Ensure that it is not processed again.  (Note that the actual
        data in the track would indicate that the transform hasn't been
        applied, but that's just to make testing easier.)
        """
        album = Album(artist='Artist', album='Album', last_transform=1)
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.transformed, False)

    def test_two_transforms_album_with_one_already_applied(self):
        """
        Transforms an album with a two transforms in the database, where
        the first one has already been applied.  (Note that the actual
        data in the track would indicate that the transform hasn't been
        applied, but that's just to make testing easier.)
        """
        album = Album(artist='Artist', album='Album', last_transform=1)
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(2,
            cond_album=True, pattern_album='Album',
            change_album=True, to_album='Album 2',
        ))

        self.assertEqual(album.last_transform, 1)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.transformed, False)

        tflist.apply_album(album)

        self.assertEqual(album.last_transform, 2)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album 2')
        self.assertEqual(album.transformed, True)

    def test_transform_track_with_single_transform(self):
        """
        Transforms a track with a single transform in the database
        """
        track = Track(artist='Artist', title='Title')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(track.last_transform, 0)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_with_single_transform_high_id(self):
        """
        Transforms a track with a single transform in the database, with
        a high ID in the database.
        """
        track = Track(artist='Artist', title='Title')
        tflist = TransformList()
        tflist.add_transform(Transform(100,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(track.last_transform, 0)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 100)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_with_two_transforms(self):
        """
        Transforms a track with a two transforms in the database
        """
        track = Track(artist='Artist', title='Title')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(2,
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2',
        ))

        self.assertEqual(track.last_transform, 0)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 2)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_with_two_transforms_with_gap_in_numbering(self):
        """
        Transforms a track with a two transforms in the database, when
        there's a gap in the numbering
        """
        track = Track(artist='Artist', title='Title')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(3,
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2',
        ))

        self.assertEqual(track.last_transform, 0)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 3)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_with_two_transforms_with_gap_in_numbering_and_one_already_applied(self):
        """
        Transforms a track with a two transforms in the database, when
        there's a gap in the numbering, and the earlier transform has
        already been applied.
        """
        track = Track(artist='Artist', title='Title')
        track.last_transform = 2
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(3,
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2',
        ))

        self.assertEqual(track.last_transform, 2)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 3)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)

    def test_transform_track_with_two_transforms_undo(self):
        """
        Transforms a track with a two transforms in the database, which
        undo each other.  Technically we should probably have something
        smart enough to find out if the end result has changed, but in
        the interests of laziness we'll just cope with possibly having
        superfluous database calls.
        """
        track = Track(artist='Artist', title='Title')
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(2,
            cond_artist=True, pattern_artist='Artist 2',
            change_artist=True, to_artist='Artist',
        ))

        self.assertEqual(track.last_transform, 0)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 2)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, True)

    def test_no_transform_track_with_already_applied_transform(self):
        """
        Sets up a track to have already been processed by a transform.
        Ensure that it is not processed again.  (Note that the actual
        data in the track would indicate that the transform hasn't been
        applied, but that's just to make testing easier.)
        """
        track = Track(artist='Artist', title='Title')
        track.last_transform = 1
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.transformed, False)

    def test_no_transform_track_with_song_with_transform_id_greater(self):
        """
        Sets up a track to have already been processed by a transform.
        Ensure that it is not processed again.  (Note that the actual
        data in the track would indicate that the transform hasn't been
        applied, but that's just to make testing easier.)
        """
        track = Track(artist='Artist', title='Title')
        track.last_transform = 1
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))

        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.transformed, False)

    def test_two_transforms_track_with_one_already_applied(self):
        """
        Transforms a track with a two transforms in the database, where
        the first one has already been applied.  (Note that the actual
        data in the track would indicate that the transform hasn't been
        applied, but that's just to make testing easier.)
        """
        track = Track(artist='Artist', title='Title')
        track.last_transform = 1
        tflist = TransformList()
        tflist.add_transform(Transform(1,
            cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2',
        ))
        tflist.add_transform(Transform(2,
            cond_title=True, pattern_title='Title',
            change_title=True, to_title='Title 2',
        ))

        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)

        tflist.apply_track(track)

        self.assertEqual(track.last_transform, 2)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)

class TransformListDatabaseTests(DatabaseTest):
    """
    Class to test our transform list database integration.
    """

    def test_load_zero_transforms(self):
        """
        Load our transform lists when there are none in the database
        """
        self.app.load_data()
        self.assertEqual(len(self.app.transforms), 0)

    def test_load_one_transform(self):
        """
        Load our transform lists when there is one transform in the database
        """
        self.add_transform(cond_artist=True, pattern_artist='Foo',
            change_artist=True, to_artist='Bar')
        self.app.load_data()
        self.assertEqual(len(self.app.transforms), 1)

    def test_load_ten_transforms(self):
        """
        Load our transform lists when there are 10 transforms in the database
        """
        for num in range(10):
            self.add_transform(cond_artist=True, pattern_artist='Foo',
                change_artist=True, to_artist='Bar',
                commit=False)
        self.app.db.commit()
        self.app.load_data()
        self.assertEqual(len(self.app.transforms), 10)

    def test_load_empty_transform(self):
        """
        Load our transform lists when there's one in the database, with all
        "empty" values
        """
        self.add_transform()
        self.app.load_data()
        self.assertEqual(len(self.app.transforms), 1)
        transform = self.app.transforms.transforms[1]
        self.assertEqual(transform.cond_artist, False)
        self.assertEqual(transform.cond_album, False)
        self.assertEqual(transform.cond_title, False)
        self.assertEqual(transform.cond_ensemble, False)
        self.assertEqual(transform.cond_conductor, False)
        self.assertEqual(transform.cond_composer, False)
        self.assertEqual(transform.change_artist, False)
        self.assertEqual(transform.change_album, False)
        self.assertEqual(transform.change_title, False)
        self.assertEqual(transform.change_ensemble, False)
        self.assertEqual(transform.change_conductor, False)
        self.assertEqual(transform.change_composer, False)
        self.assertEqual(transform.pattern_artist, '')
        self.assertEqual(transform.pattern_album, '')
        self.assertEqual(transform.pattern_title, '')
        self.assertEqual(transform.pattern_ensemble, '')
        self.assertEqual(transform.pattern_conductor, '')
        self.assertEqual(transform.pattern_composer, '')
        self.assertEqual(transform.to_artist, '')
        self.assertEqual(transform.to_album, '')
        self.assertEqual(transform.to_title, '')
        self.assertEqual(transform.to_ensemble, '')
        self.assertEqual(transform.to_conductor, '')
        self.assertEqual(transform.to_composer, '')

    def test_load_full_transform(self):
        """
        Load our transform lists when there's one in the database, with all
        possible values set.
        """
        self.add_transform(cond_artist=True, cond_album=True, cond_title=True,
            cond_ensemble=True, cond_composer=True, cond_conductor=True,
            change_artist=True, change_album=True, change_title=True,
            change_ensemble=True, change_composer=True, change_conductor=True,
            pattern_artist='Artist', pattern_album='Album', pattern_title='Title',
            pattern_ensemble='Ensemble', pattern_composer='Composer', pattern_conductor='Conductor',
            to_artist='Artist 2', to_album='Album 2', to_title='Title 2',
            to_ensemble='Ensemble 2', to_composer='Composer 2', to_conductor='Conductor 2')
        self.app.load_data()
        self.assertEqual(len(self.app.transforms), 1)
        transform = self.app.transforms.transforms[1]
        self.assertEqual(transform.cond_artist, True)
        self.assertEqual(transform.cond_album, True)
        self.assertEqual(transform.cond_title, True)
        self.assertEqual(transform.cond_ensemble, True)
        self.assertEqual(transform.cond_composer, True)
        self.assertEqual(transform.cond_conductor, True)
        self.assertEqual(transform.change_artist, True)
        self.assertEqual(transform.change_album, True)
        self.assertEqual(transform.change_title, True)
        self.assertEqual(transform.change_ensemble, True)
        self.assertEqual(transform.change_composer, True)
        self.assertEqual(transform.change_conductor, True)
        self.assertEqual(transform.pattern_artist, 'Artist')
        self.assertEqual(transform.pattern_album, 'Album')
        self.assertEqual(transform.pattern_title, 'Title')
        self.assertEqual(transform.pattern_ensemble, 'Ensemble')
        self.assertEqual(transform.pattern_composer, 'Composer')
        self.assertEqual(transform.pattern_conductor, 'Conductor')
        self.assertEqual(transform.to_artist, 'Artist 2')
        self.assertEqual(transform.to_album, 'Album 2')
        self.assertEqual(transform.to_title, 'Title 2')
        self.assertEqual(transform.to_ensemble, 'Ensemble 2')
        self.assertEqual(transform.to_composer, 'Composer 2')
        self.assertEqual(transform.to_conductor, 'Conductor 2')

class AlbumTests(unittest.TestCase):
    """
    Tests for our Album class
    """

    def test_ensure_data_no_totaltracks(self):
        """
        Tests our function to ensure that we have totaltracks
        """
        album = Album(artist='Artist', album='Album', totalseconds=120)
        with self.assertRaises(Exception):
            album.ensure_data()

    def test_ensure_data_no_totalseconds(self):
        """
        Tests our function to ensure that we have totalseconds
        """
        album = Album(artist='Artist', album='Album', totaltracks=2)
        with self.assertRaises(Exception):
            album.ensure_data()

class TrackTests(unittest.TestCase):
    """
    Tests for our Track class
    """

    def track_path(self, filename):
        """
        Returns the full path of one of our testdata files
        """
        return os.path.join(os.path.dirname(__file__), 'testdata', filename)

    def test_load_mp3_file(self):
        """
        Tests loading an mp3 file
        """
        track = Track.from_filename(self.track_path('silence.mp3'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Track')
        self.assertEqual(track.ensemble, 'Group')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(track.seconds, 2.0)

    def test_load_mp3_file_total_tracks(self):
        """
        Tests loading an mp3 file with tags that include the total number
        of tracks
        """
        track = Track.from_filename(self.track_path('silence-totalnum.mp3'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Track')
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(track.seconds, 2.0)

    def test_load_ogg_file(self):
        """
        Tests loading an ogg vorbis file
        """
        track = Track.from_filename(self.track_path('silence.ogg'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Track')
        self.assertEqual(track.ensemble, 'Group')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(track.seconds, 2.0)

    def test_load_opus_file(self):
        """
        Tests loading an ogg opus file
        """
        track = Track.from_filename(self.track_path('silence.opus'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Track')
        self.assertEqual(track.ensemble, 'Group')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(track.seconds, 2.0)

    def test_load_m4a_file(self):
        """
        Tests loading an m4a file.  Note that m4a tags don't seem to
        actually support ensemble or conductor.
        """
        track = Track.from_filename(self.track_path('silence.m4a'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.ensemble, '')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.conductor, '')
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(round(track.seconds), 2)

    def test_load_flac_file(self):
        """
        Tests loading a flac file
        """
        track = Track.from_filename(self.track_path('silence.flac'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Track')
        self.assertEqual(track.ensemble, 'Group')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(track.seconds, 2.0)

    def test_load_invalid_file(self):
        """
        Tests loading an invalid file
        """
        with self.assertRaises(Exception):
            track = Track.from_filename(__file__)

    def test_load_missing_file(self):
        """
        Tests loading a file which doesn't exist.
        """
        # Technically there's a race condition here, but... I'm not
        # particularly fussed about it.

        filename = '/%s' % (uuid.uuid4())
        while os.path.exists(filename): # pragma: no cover
            filename = '/%s' % (uuid.uuid4())

        with self.assertRaises(Exception):
            track = Track.from_filename(filename)

class AlbumDatabaseTests(DatabaseTest):
    """
    Tests of our Album object which require a database.
    """

    def test_insert_simple(self):
        """
        Tests a simple album insert
        """
        album = Album(artist='Artist', album='Album', album_type='ep',
            totaltracks=5, totalseconds=42, last_transform=3)
        pk = album.insert(self.app.db, self.app.curs)

        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist')
        self.assertEqual(album_row['alalbum'], 'Album')
        self.assertEqual(album_row['altype'], 'ep')
        self.assertEqual(album_row['totaltracks'], 5)
        self.assertEqual(album_row['totalseconds'], 42)
        self.assertEqual(album_row['lasttransform'], 3)

    def test_insert_minimal(self):
        """
        Tests a minimal album insert
        """
        album = Album(artist='Artist', album='Album',
            totalseconds=120, totaltracks=2)
        pk = album.insert(self.app.db, self.app.curs)

        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist')
        self.assertEqual(album_row['alalbum'], 'Album')
        self.assertEqual(album_row['altype'], 'album')
        self.assertEqual(album_row['totaltracks'], 2)
        self.assertEqual(album_row['totalseconds'], 120)
        self.assertEqual(album_row['lasttransform'], 0)

    def test_insert_invalid_type(self):
        """
        Tests an album insert with an invalid type.
        """
        album = Album(artist='Artist', album='Album', album_type='xyzzy',
            totalseconds=120, totaltracks=2)
        with self.assertRaises(Exception):
            pk = album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 0)

    def test_insert_empty_totalseconds(self):
        """
        Tests an album insert with no Total Seconds
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=2)
        with self.assertRaises(Exception):
            pk = album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 0)

    def test_insert_empty_totaltracks(self):
        """
        Tests an album insert with no Total Tracks
        """
        album = Album(artist='Artist', album='Album',
            totalseconds=120)
        with self.assertRaises(Exception):
            pk = album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 0)

    def test_insert_no_commit(self):
        """
        Tests an insert where we do not commit the transaction.
        """
        album = Album(artist='Artist', album='Album',
            totalseconds=120, totaltracks=1)
        pk = album.insert(self.app.db, self.app.curs, commit=False)
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist')
        self.assertEqual(album_row['alalbum'], 'Album')
        self.app.db.rollback()
        self.assertEqual(self.get_album_by_id(pk), None)
        self.assertEqual(self.get_album_count(), 0)

    def test_insert_duplicate(self):
        """
        Tests a duplicate album insert - should raise an exception
        """
        album = Album(artist='Artist', album='Album',
            totalseconds=120, totaltracks=2)
        album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 1)

        with self.assertRaises(Exception):
            album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 1)

    def test_update(self):
        """
        Tests an update of ourselves.
        """
        album = Album(artist='Artist', album='Album', album_type='ep',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist')
        self.assertEqual(album_row['alalbum'], 'Album')
        self.assertEqual(album_row['altype'], 'ep')
        self.assertEqual(album_row['totaltracks'], 1)
        self.assertEqual(album_row['totalseconds'], 120)

        # Now update the object and save out, and test.
        album.artist = 'Artist 2'
        album.album = 'Album 2'
        album.album_type = 'live'
        album.totaltracks = 2
        album.totalseconds = 240
        album.update(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist 2')
        self.assertEqual(album_row['alalbum'], 'Album 2')
        self.assertEqual(album_row['altype'], 'live')
        self.assertEqual(album_row['totaltracks'], 2)
        self.assertEqual(album_row['totalseconds'], 240)

    def test_update_no_commit(self):
        """
        Tests an update of ourselves without committing
        """
        album = Album(artist='Artist', album='Album', album_type='ep',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist')
        self.assertEqual(album_row['alalbum'], 'Album')
        self.assertEqual(album_row['altype'], 'ep')
        self.assertEqual(album_row['totaltracks'], 1)
        self.assertEqual(album_row['totalseconds'], 120)

        # Now update the object and save out, and test.
        album.artist = 'Artist 2'
        album.album = 'Album 2'
        album.album_type = 'live'
        album.totaltracks = 2
        album.totalseconds = 240
        album.update(self.app.db, self.app.curs, commit=False)
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist 2')
        self.assertEqual(album_row['alalbum'], 'Album 2')
        self.assertEqual(album_row['altype'], 'live')
        self.assertEqual(album_row['totaltracks'], 2)
        self.assertEqual(album_row['totalseconds'], 240)
        self.app.db.rollback()
        self.assertEqual(self.get_album_count(), 1)
        album_row = self.get_album_by_id(pk)
        self.assertEqual(album_row['alartist'], 'Artist')
        self.assertEqual(album_row['alalbum'], 'Album')
        self.assertEqual(album_row['altype'], 'ep')
        self.assertEqual(album_row['totaltracks'], 1)
        self.assertEqual(album_row['totalseconds'], 120)

    def test_update_no_pk(self):
        """
        Tests an update when the Album object has no PK (should raise
        an Exception)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120)
        with self.assertRaises(Exception):
            album.update(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 0)

    def test_from_database_row(self):
        """
        Tests creation of an Album object from a database row.
        """
        orig_album = Album(artist='Artist', album='Album', album_type='ep',
            totaltracks=1, totalseconds=120, last_transform=5)
        pk = orig_album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 1)

        album = Album.from_database_row(self.get_album_by_id(pk))
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'ep')
        self.assertEqual(album.totalseconds, 120)
        self.assertEqual(album.totaltracks, 1)
        self.assertEqual(album.last_transform, 5)
        self.assertEqual(album.pk, pk)

    def test_get_all_need_transform_no_albums(self):
        """
        Test for when there are no albums in the database to return
        """
        self.assertEqual(Album.get_all_need_transform(self.app.curs, 1), [])

    def test_get_all_need_transform_no_albums_matched(self):
        """
        Test for when there is an album in the database but it doesn't match.
        """
        orig_album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120, last_transform=1)
        pk = orig_album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 1)

        self.assertEqual(Album.get_all_need_transform(self.app.curs, 1), [])

    def test_get_all_need_transform_one_album(self):
        """
        Test for when there is one album returned.
        """
        orig_album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120)
        pk = orig_album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 1)

        albums = Album.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].pk, pk)

    def test_get_all_need_transform_one_album_another_already_applied(self):
        """
        Test for when there is one album returned when there's also another
        album which has already had the transform applied.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120, last_transform=1)
        pk = album.insert(self.app.db, self.app.curs)
        album = Album(artist='Artist', album='Album 2',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 2)

        albums = Album.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0].pk, pk)

    def test_get_all_need_transform_two_albums(self):
        """
        Test for when there are two albums returned.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        album = Album(artist='Artist', album='Album 2',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        self.assertEqual(self.get_album_count(), 2)

        albums = Album.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(albums), 2)

class TrackDatabaseTests(DatabaseTest):
    """
    Tests of our Track object which require a database.
    """

    def test_insert_simple(self):
        """
        Tests a simple track insert
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', composer='Composer', conductor='Conductor',
            tracknum=1, seconds=10, album_id=42, last_transform=5)
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Title')
        self.assertEqual(track_row['ensemble'], 'Ensemble')
        self.assertEqual(track_row['composer'], 'Composer')
        self.assertEqual(track_row['conductor'], 'Conductor')
        self.assertEqual(track_row['source'], 'xmms')
        self.assertEqual(track_row['album_id'], 42)
        self.assertEqual(track_row['tracknum'], 1)
        self.assertEqual(track_row['seconds'], 10)
        self.assertEqual(track_row['lasttransform'], 5)

    def test_insert_minimal(self):
        """
        Tests a minimal track insert
        """
        track = Track(artist='Artist', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], '')
        self.assertEqual(track_row['title'], 'Title')
        self.assertEqual(track_row['ensemble'], '')
        self.assertEqual(track_row['composer'], '')
        self.assertEqual(track_row['conductor'], '')
        self.assertEqual(track_row['source'], 'xmms')
        self.assertEqual(track_row['album_id'], 0)
        self.assertEqual(track_row['tracknum'], None)
        self.assertEqual(track_row['seconds'], 0)
        self.assertEqual(track_row['lasttransform'], 0)

    def test_insert_invalid_source(self):
        """
        Tests a track insert when using an invalid source
        """
        track = Track(artist='Artist', title='Title')
        with self.assertRaises(Exception):
            pk = track.insert(self.app.db,
                self.app.curs,
                'foobar',
                datetime.datetime.now())

    def test_insert_no_commit(self):
        """
        Tests an insert where we do not commit the transaction.
        """
        track = Track(artist='Artist', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now(),
            commit=False)
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['title'], 'Title')
        self.app.db.rollback()
        self.assertEqual(self.get_track_by_id(pk), None)
        self.assertEqual(self.get_track_count(), 0)

    def test_update(self):
        """
        Tests an update of ourselves.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', conductor='Conductor', composer='Composer')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Title')
        self.assertEqual(track_row['ensemble'], 'Ensemble')
        self.assertEqual(track_row['composer'], 'Composer')
        self.assertEqual(track_row['conductor'], 'Conductor')

        # Now update the object and save out, and test.
        track.artist = 'Artist 2'
        track.album = 'Album 2'
        track.title = 'Title 2'
        track.ensemble = 'Ensemble 2'
        track.composer = 'Composer 2'
        track.conductor = 'Conductor 2'
        track.update(self.app.db, self.app.curs)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album 2')
        self.assertEqual(track_row['title'], 'Title 2')
        self.assertEqual(track_row['ensemble'], 'Ensemble 2')
        self.assertEqual(track_row['composer'], 'Composer 2')
        self.assertEqual(track_row['conductor'], 'Conductor 2')

    def test_update_no_commit(self):
        """
        Tests an update of ourselves without committing
        """
        track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', conductor='Conductor', composer='Composer')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertNotEqual(pk, None)
        self.assertNotEqual(pk, 0)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Title')
        self.assertEqual(track_row['ensemble'], 'Ensemble')
        self.assertEqual(track_row['composer'], 'Composer')
        self.assertEqual(track_row['conductor'], 'Conductor')

        # Now update the object and save out, and test.
        track.artist = 'Artist 2'
        track.album = 'Album 2'
        track.title = 'Title 2'
        track.ensemble = 'Ensemble 2'
        track.composer = 'Composer 2'
        track.conductor = 'Conductor 2'
        track.update(self.app.db, self.app.curs, commit=False)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album 2')
        self.assertEqual(track_row['title'], 'Title 2')
        self.assertEqual(track_row['ensemble'], 'Ensemble 2')
        self.assertEqual(track_row['composer'], 'Composer 2')
        self.assertEqual(track_row['conductor'], 'Conductor 2')
        self.app.db.rollback()
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Title')
        self.assertEqual(track_row['ensemble'], 'Ensemble')
        self.assertEqual(track_row['composer'], 'Composer')
        self.assertEqual(track_row['conductor'], 'Conductor')

    def test_update_no_pk(self):
        """
        Tests an update when the Track object has no PK (should raise
        an Exception)
        """
        track = Track(artist='Artist', album='Album', title='Title')
        with self.assertRaises(Exception):
            track.update(self.app.db, self.app.curs)
        self.assertEqual(self.get_track_count(), 0)

    def test_from_database_row(self):
        """
        Tests creation of a Track object from a database row.
        """
        orig_track = Track(artist='Artist', album='Album', title='Title',
            ensemble='Ensemble', conductor='Conductor', composer='Composer',
            tracknum=1, seconds=10, album_id=42, last_transform=5)
        pk = orig_track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 1)

        track = Track.from_database_row(self.get_track_by_id(pk))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.ensemble, 'Ensemble')
        self.assertEqual(track.composer, 'Composer')
        self.assertEqual(track.conductor, 'Conductor')
        self.assertEqual(track.seconds, 10)
        self.assertEqual(track.album_id, 42)
        self.assertEqual(track.last_transform, 5)
        self.assertEqual(track.pk, pk)

    def test_get_all_need_transform_no_tracks(self):
        """
        Test for when there are no tracks in the database to return
        """
        self.assertEqual(Track.get_all_need_transform(self.app.curs, 1), [])

    def test_get_all_need_transform_no_tracks_matched(self):
        """
        Test for when there is a track in the database but it doesn't match.
        """
        track = Track(artist='Artist', album='Album', title='Title', last_transform=1)
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 1)

        tracks = Track.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(tracks), 0)

    def test_get_all_need_transform_one_track(self):
        """
        Test for when there is one track returned.
        """
        track = Track(artist='Artist', album='Album', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 1)

        tracks = Track.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].pk, pk)

    def test_get_all_need_transform_one_track_another_already_applied(self):
        """
        Test for when there is one track returned when there's also another
        track which has already had the transform applied.
        """
        track = Track(artist='Artist', album='Album', title='Title', last_transform=1)
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        track = Track(artist='Artist', album='Album', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 2)

        tracks = Track.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].pk, pk)

    def test_get_all_need_transform_two_tracks(self):
        """
        Test for when there are two tracks returned.
        """
        track = Track(artist='Artist', album='Album', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 2)

        tracks = Track.get_all_need_transform(self.app.curs, 1)
        self.assertEqual(len(tracks), 2)

    def test_get_all_unassociated_no_tracks(self):
        """
        No tracks in the database, should return an empty list
        """
        self.assertEqual(self.get_track_count(), 0)
        tracks = Track.get_all_unassociated(self.app.curs)
        self.assertEqual(tracks, [])

    def test_get_all_unassociated_single_track_without_album(self):
        """
        A single unassociated track in the database, but without an
        album title so it should not be returned.
        """
        track = Track(artist='Artist', title='Title')
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 1)
        tracks = Track.get_all_unassociated(self.app.curs)
        self.assertEqual(len(tracks), 0)

    def test_get_all_unassociated_single_track_with_album(self):
        """
        A single unassociated track in the database
        """
        track = Track(artist='Artist', album='Album', title='Title')
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 1)
        tracks = Track.get_all_unassociated(self.app.curs)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].artist, 'Artist')
        self.assertEqual(tracks[0].title, 'Title')
        self.assertEqual(tracks[0].album_id, 0)

    def test_get_all_unassociated_two_tracks_with_album(self):
        """
        Two unassociated tracks in the database
        """
        track = Track(artist='Artist', album='Album', title='Title')
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 2)
        tracks = Track.get_all_unassociated(self.app.curs)
        self.assertEqual(len(tracks), 2)
        for tracknum in [0, 1]:
            with self.subTest(tracknum=tracknum):
                self.assertEqual(tracks[tracknum].artist, 'Artist')
                self.assertEqual(tracks[tracknum].title, 'Title')
                self.assertEqual(tracks[tracknum].album_id, 0)

    def test_get_all_unassociated_single_track_already_associated(self):
        """
        A single associated track in the database, no data should be returned.
        """
        track = Track(artist='Artist', album='Album',
            title='Title', album_id=1)
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 1)
        tracks = Track.get_all_unassociated(self.app.curs)
        self.assertEqual(len(tracks), 0)

    def test_get_all_unassociated_two_tracks_one_unassociated(self):
        """
        Two tracks in the database - one is associated, the other is not.
        """
        track = Track(artist='Artist', album='Album',
            title='Title', album_id=1)
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        track = Track(artist='Artist 2', album='Album 2', title='Title 2')
        track.insert(self.app.db, self.app.curs,
            'xmms', datetime.datetime.now())
        self.assertEqual(self.get_track_count(), 2)
        tracks = Track.get_all_unassociated(self.app.curs)
        self.assertEqual(tracks[0].artist, 'Artist 2')
        self.assertEqual(tracks[0].title, 'Title 2')
        self.assertEqual(tracks[0].album_id, 0)

class AppTests(unittest.TestCase):
    """
    Some tests of our main App object
    """

    def test_missing_database_file(self):
        """
        Tests what happens when we're given a database file that doesn't
        exist
        """
        # Technically there's a race condition here, but... I'm not
        # particularly fussed about it.

        filename = '/%s' % (uuid.uuid4())
        while os.path.exists(filename): # pragma: no cover
            filename = '/%s' % (uuid.uuid4())

        with self.assertRaises(Exception):
            app = App(filename)

    def test_invalid_database_file(self):
        """
        Tests what happens when we're given a database file that's invalid
        """
        with self.assertRaises(Exception):
            app = App(__file__)

    def test_ini_file_without_database_section(self):
        """
        Tests what happens when we're given a database file without a [database]
        section in it.
        """
        with self.assertRaises(Exception) as cm:
            app = App(os.path.join('testdata', 'ini_no_section.ini'))
        self.assertIn('configuration not found', str(cm.exception))

    def test_ini_file_without_variables(self):
        """
        Tests what happens when we're given a database file with a [database]
        section but without one of our required vars.
        """
        for varname in ['host', 'name', 'user', 'pass']:
            with self.subTest(varname=varname):
                with self.assertRaises(Exception) as cm:
                    app = App(os.path.join('testdata', 'ini_no_%s.ini' % (varname)))
                self.assertIn('Configuration val "%s"' % (varname), str(cm.exception))

class AppDatabaseTests(DatabaseTest):
    """
    Tests on our main App class which require a database.
    """

    def test_get_album_id_none_found(self):
        """
        Look up an album ID when we don't have one.
        """
        track = Track(artist='Artist', album='Album', title='Title')
        album_id = self.app.set_album_id(track)
        self.assertEqual(album_id, 0)
        self.assertEqual(track.album_id, 0)

    def test_get_album_id_regular_album(self):
        """
        Look up an album ID when we have a 'regular' album match
        """
        album_id = self.add_album(artist='Artist', album='Album')
        self.assertNotEqual(album_id, 0)
        track = Track(artist='Artist', album='Album', title='Title')
        track_album_id = self.app.set_album_id(track)
        self.assertEqual(track_album_id, album_id)
        self.assertEqual(track.album_id, album_id)

    def test_get_album_id_various_album(self):
        """
        Look up an album ID when we have a Various Artists album match
        """
        album_id = self.add_album(artist='Various', album='Album')
        self.assertNotEqual(album_id, 0)
        track = Track(artist='Artist', album='Album', title='Title')
        track_album_id = self.app.set_album_id(track)
        self.assertEqual(track_album_id, album_id)
        self.assertEqual(track.album_id, album_id)

    def test_get_album_id_regular_and_various_album(self):
        """
        Look up an album ID when we have both a regular and Various Artists
        album match.  We should default to the regular one.
        """
        var_album_id = self.add_album(artist='Various', album='Album')
        self.assertNotEqual(var_album_id, 0)
        reg_album_id = self.add_album(artist='Artist', album='Album')
        self.assertNotEqual(reg_album_id, 0)
        track = Track(artist='Artist', album='Album', title='Title')
        track_album_id = self.app.set_album_id(track)
        self.assertEqual(track_album_id, reg_album_id)
        self.assertEqual(track.album_id, reg_album_id)

class LogTrackTests(DatabaseTest):
    """
    Tests for our log_track function, which handles the addition of a single
    Track object to the database (applying transforms and associating to
    albums, etc).
    """

    def track_path(self, filename):
        """
        Returns the full path of one of our testdata files
        """
        return os.path.join(os.path.dirname(__file__), 'testdata', filename)
    
    def track_obj(self, filename='silence.mp3'):
        """
        Returns a Track object given a music filename inside our testdata
        directory.
        """
        return Track.from_filename(self.track_path(filename))

    def test_log_track_regular(self):
        """
        Logs a track.
        """
        track = self.app.log_track(self.track_obj('silence.mp3'))
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(track.pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['ensemble'], 'Group')
        self.assertEqual(track_row['composer'], 'Composer')
        self.assertEqual(track_row['conductor'], 'Conductor')
        self.assertEqual(track_row['source'], 'xmms')
        self.assertEqual(track_row['album_id'], 0)
        self.assertEqual(track_row['tracknum'], 1)
        self.assertEqual(track_row['seconds'], 2)
        self.assertEqual(track_row['lasttransform'], 0)
        
        # This is a bit fuzzy, since in a worst-case scenario we may have
        # timestamps differing by a second or so.  To be extra-cautious,
        # we'll just make sure the timestamp is +/- ten seconds of
        # what we think it should be.
        timestamp = track_row['timestamp'].timestamp()
        now_ts = datetime.datetime.now().timestamp()
        self.assertGreater(timestamp, now_ts-10)
        self.assertLess(timestamp, now_ts+10)

    def test_log_track_alternate_source(self):
        """
        Logs a track using an alternate source
        """
        track = self.app.log_track(self.track_obj('silence.mp3'), source='car')
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(track.pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'car')
        self.assertEqual(track_row['album_id'], 0)
        self.assertEqual(track_row['tracknum'], 1)
        self.assertEqual(track_row['seconds'], 2)
        self.assertEqual(track_row['lasttransform'], 0)
        
        # This is a bit fuzzy, since in a worst-case scenario we may have
        # timestamps differing by a second or so.  To be extra-cautious,
        # we'll just make sure the timestamp is +/- ten seconds of
        # what we think it should be.
        timestamp = track_row['timestamp'].timestamp()
        now_ts = datetime.datetime.now().timestamp()
        self.assertGreater(timestamp, now_ts-10)
        self.assertLess(timestamp, now_ts+10)

    def test_log_track_invalid_source(self):
        """
        Logs a track using an invalid source
        """
        with self.assertRaises(Exception):
            self.app.log_track(self.track_obj('silence.mp3'), source='foo')
        self.assertEqual(self.get_track_count(), 0)

    def test_log_track_with_album_association(self):
        """
        Tests logging a track with an album association.
        """
        album_id = self.add_album(artist='Artist', album='Album')
        self.assertNotEqual(album_id, 0)

        track = self.app.log_track(self.track_obj('silence.mp3'))
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(track.pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'xmms')
        self.assertEqual(track_row['album_id'], album_id)

    def test_log_track_with_transform(self):
        """
        Tests logging a track when we have a transform in the DB
        """
        tf_id = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        self.assertNotEqual(tf_id, 0)
        self.app.load_data()

        track = self.app.log_track(self.track_obj('silence.mp3'))
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(track.pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['lasttransform'], tf_id)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'xmms')

    def test_log_track_with_transform_and_album(self):
        """
        Tests logging a track when we have a transform in the DB, and also an
        album which we'll get associated with, post-transform.
        """

        album_id = self.add_album(artist='Artist 2', album='Album')
        self.assertNotEqual(album_id, 0)

        tf_id = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        self.assertNotEqual(tf_id, 0)
        self.app.load_data()

        track = self.app.log_track(self.track_obj('silence.mp3'))
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(track.pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['lasttransform'], tf_id)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'xmms')
        self.assertEqual(track_row['album_id'], album_id)

    def test_log_track_with_transform_and_nonmatching_album(self):
        """
        Tests logging a track when we have a transform in the DB, and also an
        album, though the album would only match if the transforms weren't
        done.  So the track should remain albumless.
        """

        album_id = self.add_album(artist='Artist', album='Album')
        self.assertNotEqual(album_id, 0)

        tf_id = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        self.assertNotEqual(tf_id, 0)
        self.app.load_data()

        track = self.app.log_track(self.track_obj('silence.mp3'))
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(track.pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['lasttransform'], tf_id)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'xmms')
        self.assertEqual(track_row['album_id'], 0)

class LogFilenamesTests(DatabaseTest):
    """
    Tests for our log_filenames function, which serves as the main entry point
    for our CLI log function, and handles loading filenames into Track objects,
    parsing user-provided dates, and looping through multiple files if required.
    """

    def track_path(self, filename):
        """
        Returns the full path of one of our testdata files
        """
        return os.path.join(os.path.dirname(__file__), 'testdata', filename)

    def test_log_filenames_file_not_found(self):
        """
        Tries logging a track which doesn't exist
        """

        filename = '/%s' % (uuid.uuid4())
        while os.path.exists(filename): # pragma: no cover
            filename = '/%s' % (uuid.uuid4())

        with self.assertRaises(Exception):
            self.app.log_filenames([filename])
        self.assertEqual(self.get_track_count(), 0)

    def test_log_filenames_invalid_file(self):
        """
        Tries logging a track which isn't actually a music file
        """
        with self.assertRaises(Exception):
            self.app.log_filenames([__file__])
        self.assertEqual(self.get_track_count(), 0)

    def test_log_filenames_timestamp_2hr(self):
        """
        Logs a track with a custom time field ("2 hours ago")
        """
        (tracks, statuses) = self.app.log_filenames(self.track_path('silence.mp3'),
            timestamp='2 hours ago')
        self.assertEqual(self.get_track_count(), 1)
        self.assertEqual(len(tracks), 1)
        track_row = self.get_track_by_id(tracks[0].pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'xmms')
        
        # This is a bit fuzzy, since in a worst-case scenario we may have
        # timestamps differing by a second or so.  To be extra-cautious,
        # we'll just make sure the timestamp is +/- ten seconds of
        # what we think it should be.
        timestamp = track_row['timestamp'].timestamp()
        two_hours = datetime.datetime.now().timestamp() - 7200
        self.assertGreater(timestamp, two_hours-10)
        self.assertLess(timestamp, two_hours+10)

    def test_log_filenames_timestamp_specific_date(self):
        """
        Logs a track with a specific time field ("2016-07-01 12:00:00")
        """
        (tracks, statuses) = self.app.log_filenames(self.track_path('silence.mp3'),
            timestamp='2016-07-01 12:00:00')
        self.assertEqual(self.get_track_count(), 1)
        self.assertEqual(len(tracks), 1)
        track_row = self.get_track_by_id(tracks[0].pk)
        self.assertNotEqual(track_row, None)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Track')
        self.assertEqual(track_row['source'], 'xmms')
        
        timestamp = track_row['timestamp']
        compare_date = datetime.datetime(2016, 7, 1, 12, 0, 0)
        self.assertEqual(timestamp, compare_date)

    def test_log_filenames_invalid_timestamp(self):
        """
        Logs a track using a completely invalid timestamp
        """
        with self.assertRaises(Exception):
            self.app.log_filenames(self.track_path('silence.mp3'), timestamp='foo')
        self.assertEqual(self.get_track_count(), 0)

    def test_log_filenames_no_filenames(self):
        """
        Calls our method without actually passing in any filenames.
        """
        (tracks, statuses) = self.app.log_filenames([])
        self.assertEqual(len(tracks), 0)
        self.assertEqual(len(statuses), 1)
        self.assertIn('No filenames', statuses[0])

    def test_log_filenames_multiple_no_date(self):
        """
        Log multiple filenames at the same time, without specifying a date.
        Inserted timestamps should all occur before the current time.
        """
        now = datetime.datetime.now()
        (tracks, statuses) = self.app.log_filenames([self.track_path('silence.mp3')]*5)
        self.assertEqual(len(tracks), 5)
        self.assertEqual(self.get_track_count(), 5)
        track_objs = []
        for (idx, track) in enumerate(tracks):
            with self.subTest(idx=idx):
                track_obj = self.get_track_by_id(track.pk)
                track_objs.append(track_obj)
                self.assertLess(track_obj['timestamp'], now)
                if idx > 0:
                    self.assertGreater(track_obj['timestamp'],
                        track_objs[idx-1]['timestamp'])

    def test_log_filenames_multiple_date_in_past(self):
        """
        Log multiple filenames at the same time, specifying a date in the
        past.  All tracks should be at the start date or later.  Being a bit
        fuzzy on the comparison time since technically we could end up with
        at least a second difference.
        """
        time_lower = datetime.datetime.now() - datetime.timedelta(seconds=7210)
        time_upper = time_lower + datetime.timedelta(seconds=20)
        (tracks, statuses) = self.app.log_filenames(
            [self.track_path('silence.mp3')]*5,
            timestamp='2 hours ago'
        )
        self.assertEqual(len(tracks), 5)
        self.assertEqual(self.get_track_count(), 5)
        track_objs = []
        for (idx, track) in enumerate(tracks):
            with self.subTest(idx=idx):
                track_obj = self.get_track_by_id(track.pk)
                track_objs.append(track_obj)
                self.assertGreaterEqual(track_obj['timestamp'], time_lower)
                self.assertLess(track_obj['timestamp'], time_upper)
                if idx > 0:
                    self.assertGreater(track_obj['timestamp'],
                        track_objs[idx-1]['timestamp'])

class ApplyTransformsTests(DatabaseTest):
    """
    Tests for our apply_transforms function, used to apply transforms to all
    tracks/albums in the database which need them.  The majority of our
    transform logic is tested elsewhere in here, so we're mostly just interested
    in making sure that our transform ID gets updated where appropriate.
    """

    def test_apply_transform_single_album_no_match(self):
        """
        A single album in the database needs an update, where the
        album does not match the transform.  (Should still update the
        last_transform ID.)
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Foo',
            change_artist=True, to_artist='Bar')
        self.assertNotEqual(tf_pk, 0)
        self.app.load_data()

        row = self.get_album_by_id(pk)
        self.assertEqual(row['lasttransform'], 0)

        for line in self.app.apply_transforms():
            pass

        row = self.get_album_by_id(pk)
        self.assertEqual(row['lasttransform'], tf_pk)

    def test_apply_transform_single_album_match(self):
        """
        A single album in the database needs an update, where the
        album matches the transform.
        """
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120)
        pk = album.insert(self.app.db, self.app.curs)
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='New Artist')
        self.assertNotEqual(tf_pk, 0)
        self.app.load_data()

        row = self.get_album_by_id(pk)
        self.assertEqual(row['lasttransform'], 0)

        for line in self.app.apply_transforms():
            pass

        row = self.get_album_by_id(pk)
        self.assertEqual(row['lasttransform'], tf_pk)
        self.assertEqual(row['alartist'], 'New Artist')

    def test_apply_transform_two_albums_one_matches(self):
        """
        Two albums are in the database, one already has the transform applied but
        the other does not.  Both should end up at the same last_transform ID.
        The album whose last_transform is already high enough should remain
        untouched even though the transform theoretically matches.
        """
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        self.assertNotEqual(tf_pk, 0)

        self.app.load_data()
        album = Album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=120, last_transform=tf_pk)
        pk_first = album.insert(self.app.db, self.app.curs)
        album = Album(artist='Artist', album='Album 2',
            totaltracks=1, totalseconds=120)
        pk_second = album.insert(self.app.db, self.app.curs)

        row = self.get_album_by_id(pk_first)
        self.assertEqual(row['lasttransform'], tf_pk)
        row = self.get_album_by_id(pk_second)
        self.assertEqual(row['lasttransform'], 0)

        for line in self.app.apply_transforms():
            pass

        row = self.get_album_by_id(pk_first)
        self.assertEqual(row['lasttransform'], tf_pk)
        self.assertEqual(row['alartist'], 'Artist')

        row = self.get_album_by_id(pk_second)
        self.assertEqual(row['lasttransform'], tf_pk)
        self.assertEqual(row['alartist'], 'Artist 2')

    def test_apply_transform_single_track_no_match(self):
        """
        A single track in the database needs an update, where the
        track does not match the transform.  (Should still update the
        last_transform ID.)
        """
        track = Track(artist='Artist', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Foo',
            change_artist=True, to_artist='Bar')
        self.assertNotEqual(tf_pk, 0)
        self.app.load_data()

        row = self.get_track_by_id(pk)
        self.assertEqual(row['lasttransform'], 0)

        for line in self.app.apply_transforms():
            pass

        row = self.get_track_by_id(pk)
        self.assertEqual(row['lasttransform'], tf_pk)

    def test_apply_transform_single_track_match(self):
        """
        A single track in the database needs an update, where the
        track matches the transform.
        """
        track = Track(artist='Artist', title='Title')
        pk = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='New Artist')
        self.assertNotEqual(tf_pk, 0)
        self.app.load_data()

        row = self.get_track_by_id(pk)
        self.assertEqual(row['lasttransform'], 0)

        for line in self.app.apply_transforms():
            pass

        row = self.get_track_by_id(pk)
        self.assertEqual(row['lasttransform'], tf_pk)
        self.assertEqual(row['artist'], 'New Artist')

    def test_apply_transform_two_tracks_one_matches(self):
        """
        Two tracks are in the database, one already has the transform applied but
        the other does not.  Both should end up at the same last_transform ID.
        The track whose last_transform is already high enough should remain
        untouched even though the transform theoretically matches.
        """
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        self.assertNotEqual(tf_pk, 0)

        self.app.load_data()
        track = Track(artist='Artist', title='Title', last_transform=tf_pk)
        pk_first = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())
        track = Track(artist='Artist', title='Title')
        pk_second = track.insert(self.app.db,
            self.app.curs,
            'xmms',
            datetime.datetime.now())

        row = self.get_track_by_id(pk_first)
        self.assertEqual(row['lasttransform'], tf_pk)
        row = self.get_track_by_id(pk_second)
        self.assertEqual(row['lasttransform'], 0)

        for line in self.app.apply_transforms():
            pass

        row = self.get_track_by_id(pk_first)
        self.assertEqual(row['lasttransform'], tf_pk)
        self.assertEqual(row['artist'], 'Artist')

        row = self.get_track_by_id(pk_second)
        self.assertEqual(row['lasttransform'], tf_pk)
        self.assertEqual(row['artist'], 'Artist 2')

class AddAlbumTests(DatabaseTest):
    """
    Tests for dealing with adding a new album to the DB.  This is only ever
    done via reading in groups of files, so we have some extra work to do
    in setUp and tearDown.
    """

    def setUp(self):
        super(AddAlbumTests, self).setUp()
        self.mp3_dir = tempfile.mkdtemp()
        self.source_file = os.path.join(os.path.dirname(__file__), 'testdata',
            'silence.mp3')
        self.filenames = []

    def tearDown(self):
        super(AddAlbumTests, self).tearDown()
        shutil.rmtree(self.mp3_dir)

    def add_mp3(self, filename='song.mp3', set_artist=False, artist=None,
            set_album=False, album=None):
        """
        Adds an mp3 to our temporary mp3 dir, based on ``testdata/silence.mp3``.
        Returns the full path to the mp3.  If ``set_artist`` or ``set_album``
        are ``True``, mutagen will be used to alter the mp3 tags after
        copying.  If ``artist`` or ``album`` are ``None`` in this case, it
        will remove those tags entirely.

        Will also add the path to ``self.filenames``, which can then be used
        to pass into ``App.add_album()``.
        """
        full_filename = os.path.join(self.mp3_dir, filename)
        shutil.copyfile(self.source_file, full_filename)
        self.assertEqual(os.path.exists(full_filename), True)

        if set_artist or set_album:
            tags = id3.ID3(full_filename)

            if set_artist:
                tags.delall('TPE1')
                if artist is not None:
                    tags.add(id3.TPE1(encoding=3, text=artist))
            
            if set_album:
                tags.delall('TALB')
                if album is not None:
                    tags.add(id3.TALB(encoding=3, text=album))

            tags.save()

        self.filenames.append(full_filename)
        return full_filename

    def test_no_tracks(self):
        """
        Tests adding when there are no tracks.
        """
        (added, status) = self.app.add_album([])
        self.assertEqual(added, False)
        self.assertIn('No files', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_single_track(self):
        """
        Tests adding a single-track album
        """
        self.add_mp3()
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)
        album = Album.get_by_artist_album(self.app.curs, 'Artist', 'Album')
        self.assertNotEqual(album, None)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'album')
        self.assertEqual(album.totalseconds, 2)
        self.assertEqual(album.totaltracks, 1)

    def test_single_track_ep(self):
        """
        Tests adding a single-track album as an EP
        """
        self.add_mp3()
        (added, status) = self.app.add_album(self.filenames, 'ep')
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)
        album = Album.get_by_artist_album(self.app.curs, 'Artist', 'Album')
        self.assertNotEqual(album, None)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'ep')
        self.assertEqual(album.totalseconds, 2)
        self.assertEqual(album.totaltracks, 1)

    def test_single_track_no_artist(self):
        """
        Tests adding a single-track album but without an artist tag (should fail)
        """
        self.add_mp3(set_artist=True)
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('has no artist tag', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_single_track_blank_artist(self):
        """
        Tests adding a single-track album but without a blank artist tag (should fail)
        """
        self.add_mp3(set_artist=True, artist='')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('has no artist tag', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_single_track_no_album(self):
        """
        Tests adding a single-track album but without an album tag (should fail)
        """
        self.add_mp3(set_album=True)
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('has no album tag', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_single_track_blank_album(self):
        """
        Tests adding a single-track album but without a blank album tag (should fail)
        """
        self.add_mp3(set_album=True, album='')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('has no album tag', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_two_tracks_same_album(self):
        """
        Tests adding a two-track album
        """
        self.add_mp3(filename='1.mp3')
        self.add_mp3(filename='2.mp3')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)
        album = Album.get_by_artist_album(self.app.curs, 'Artist', 'Album')
        self.assertNotEqual(album, None)
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'album')
        self.assertEqual(album.totalseconds, 4)
        self.assertEqual(album.totaltracks, 2)

    def test_two_tracks_various_artists(self):
        """
        Tests adding a two-track various artists album
        """
        self.add_mp3(filename='1.mp3')
        self.add_mp3(filename='2.mp3', set_artist=True, artist='Artist 2')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)
        album = Album.get_by_artist_album(self.app.curs, 'Various', 'Album')
        self.assertNotEqual(album, None)
        self.assertEqual(album.artist, 'Various')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'album')
        self.assertEqual(album.totalseconds, 4)
        self.assertEqual(album.totaltracks, 2)

    def test_two_tracks_mismatched_album(self):
        """
        Tests trying to add two tracks which don't share an album name.  Should
        fail.
        """
        self.add_mp3(filename='1.mp3')
        self.add_mp3(filename='2.mp3', set_album=True, album='Album 2')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('changed to', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_single_track_artist_too_long(self):
        """
        Tests adding a file with an artist name that's too long.
        """
        self.add_mp3(set_artist=True, artist='z'*(App.max_artist_album_length+10))
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('is longer than', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_single_track_album_too_long(self):
        """
        Tests adding a file with an album name that's too long.
        """
        self.add_mp3(set_album=True, album='z'*(App.max_artist_album_length+10))
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('is longer than', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_adding_album_twice(self):
        """
        Tests adding the same album twice (should fail if we don't specify
        force_update).  Will add a second track and a different album type,
        just for comparison's sake.
        """
        self.add_mp3(filename='1.mp3')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)

        self.add_mp3(filename='2.mp3')
        (added, status) = self.app.add_album(self.filenames, 'ep')
        self.assertEqual(added, False)
        self.assertIn('Would update to', status)
        self.assertEqual(self.get_album_count(), 1)

        album = Album.get_by_artist_album(self.app.curs, 'Artist', 'Album')
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'album')
        self.assertEqual(album.totalseconds, 2)
        self.assertEqual(album.totaltracks, 1)

    def test_adding_album_twice_forced(self):
        """
        Tests adding the same album twice, forcing the update.  Will add
        a second track so that we can check for updated variables.
        """
        self.add_mp3(filename='1.mp3')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)

        self.add_mp3(filename='2.mp3')
        (added, status) = self.app.add_album(self.filenames, 'ep', force_update=True)
        self.assertEqual(added, True)
        self.assertIn('Updated to', status)
        self.assertEqual(self.get_album_count(), 1)

        album = Album.get_by_artist_album(self.app.curs, 'Artist', 'Album')
        self.assertEqual(album.artist, 'Artist')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'ep')
        self.assertEqual(album.totalseconds, 4)
        self.assertEqual(album.totaltracks, 2)

    def test_single_track_with_transform(self):
        """
        Tests adding a single-track album, when a transform is in place.
        """
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        self.app.load_data()

        self.add_mp3()
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)
        album = Album.get_by_artist_album(self.app.curs, 'Artist 2', 'Album')
        self.assertNotEqual(album, None)
        self.assertEqual(album.artist, 'Artist 2')
        self.assertEqual(album.album, 'Album')
        self.assertEqual(album.album_type, 'album')
        self.assertEqual(album.totalseconds, 2)
        self.assertEqual(album.totaltracks, 1)
        self.assertEqual(album.last_transform, tf_pk)

    def test_adding_existing_album_with_dependant_transform(self):
        """
        Tests adding an album when we already have the same album in the
        database, though the matching album will ONLY be matched if transforms
        are applied at the correct spot.
        """
        tf_pk = self.add_transform(cond_artist=True, pattern_artist='Artist',
            change_artist=True, to_artist='Artist 2')
        album_id = self.add_album(artist='Artist 2', album='Album')
        self.app.load_data()
        self.assertEqual(self.get_album_count(), 1)

        self.add_mp3()
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, False)
        self.assertIn('Would update to', status)
        self.assertEqual(self.get_album_count(), 1)

    def test_adding_invalid_file(self):
        """
        Tests adding a file which isn't actually a music file.
        """
        (added, status) = self.app.add_album(__file__)
        self.assertEqual(added, False)
        self.assertIn('Unable to load', status)
        self.assertEqual(self.get_album_count(), 0)

    def test_add_unicode_char(self):
        """
        Tests adding an album with a unicode char in the album namae
        """
        self.add_mp3(set_artist=True, artist='Artist',
            set_album=True, album='Unicode Char: œ')
        (added, status) = self.app.add_album(self.filenames)
        self.assertEqual(added, True)
        self.assertEqual(self.get_album_count(), 1)
        album = Album.get_by_artist_album(self.app.curs, 'Artist', 'Unicode Char: œ')
        self.assertNotEqual(album, None)
        self.assertEqual(album.album, 'Unicode Char: œ')

class AssociateAlbumTests(DatabaseTest):
    """
    Class for our album-association util, which associates any unassociated
    track to an album.
    """

    def test_track_without_association(self):
        """
        Tests a track which doesn't have an association to be made in the
        database.
        """
        track = Track(artist='Artist', album='Album')
        pk = track.insert(self.app.db, self.app.curs,
            'xmms',
            datetime.datetime.now())

        for line in self.app.associate_albums():
            pass

        row = self.get_track_by_id(pk)
        self.assertEqual(row['album_id'], 0)

    def test_track_with_association(self):
        """
        Tests a track which DOES have an association to be made in the
        database.
        """
        album_pk = self.add_album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=2)
        track = Track(artist='Artist', album='Album')
        pk = track.insert(self.app.db, self.app.curs,
            'xmms',
            datetime.datetime.now())

        row = self.get_track_by_id(pk)
        self.assertEqual(row['album_id'], 0)

        for line in self.app.associate_albums():
            pass

        row = self.get_track_by_id(pk)
        self.assertEqual(row['album_id'], album_pk)

    def test_two_tracks_with_association(self):
        """
        Tests two tracks which DO have an association to be made in the
        database.
        """
        album_pk = self.add_album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=2)
        track = Track(artist='Artist', album='Album')
        pk_first = track.insert(self.app.db, self.app.curs,
            'xmms',
            datetime.datetime.now())
        pk_second = track.insert(self.app.db, self.app.curs,
            'xmms',
            datetime.datetime.now())

        row = self.get_track_by_id(pk_first)
        self.assertEqual(row['album_id'], 0)
        row = self.get_track_by_id(pk_second)
        self.assertEqual(row['album_id'], 0)

        for line in self.app.associate_albums():
            pass

        row = self.get_track_by_id(pk_first)
        self.assertEqual(row['album_id'], album_pk)
        row = self.get_track_by_id(pk_second)
        self.assertEqual(row['album_id'], album_pk)

    def test_two_tracks_with_two_associations(self):
        """
        Tests two tracks which have associations to be made, a different
        one for each track.
        """
        album_pk_first = self.add_album(artist='Artist', album='Album',
            totaltracks=1, totalseconds=2)
        album_pk_second = self.add_album(artist='Artist 2', album='Album 2',
            totaltracks=1, totalseconds=2)
        track = Track(artist='Artist', album='Album')
        pk_first = track.insert(self.app.db, self.app.curs,
            'xmms',
            datetime.datetime.now())
        track = Track(artist='Artist 2', album='Album 2')
        pk_second = track.insert(self.app.db, self.app.curs,
            'xmms',
            datetime.datetime.now())

        row = self.get_track_by_id(pk_first)
        self.assertEqual(row['album_id'], 0)
        row = self.get_track_by_id(pk_second)
        self.assertEqual(row['album_id'], 0)

        for line in self.app.associate_albums():
            pass

        row = self.get_track_by_id(pk_first)
        self.assertEqual(row['album_id'], album_pk_first)
        row = self.get_track_by_id(pk_second)
        self.assertEqual(row['album_id'], album_pk_second)

class AppArgumentParserTests(unittest.TestCase):
    """
    Tests of our AppArgumentParser.  Honestly this is only here just so
    coverage.py reports 100% without having to exclude it.
    """

    def test_instantiation(self):
        """
        Just make sure it works.
        """
        parser = AppArgumentParser(description='test')
        self.assertNotEqual(parser, None)

if __name__ == '__main__':

    # Create our database
    app = App('dbtests.ini', load_data=False)
    app._initialize_db()
    app.close()

    # Run tests
    unittest.main(exit=False)

    # Tear down database
    app = App('dbtests.ini', load_data=False)
    app._drop_db()
    app.close()
