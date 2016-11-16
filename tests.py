#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

import os
import uuid
import unittest
import datetime

from app import App, Track, Transform, TransformList

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
            change_artist=False, change_album=False, change_title=False,
            pattern_artist='', pattern_album='', pattern_title='',
            to_artist='', to_album='', to_title='',
            commit=True):
        """
        Adds a new transform to our database, given the specified attributes.  Will
        commit by default, but if you pass in ``commit`` = ``False`` we will not.
        Returns the primary key of the new transform.
        """
        self.app.curs.execute("""insert into transform (
            artistcond, albumcond, titlecond,
            artistchange, albumchange, titlechange,
            artistpat, albumpat, titlepat,
            artistto, albumto, titleto) values (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s)""", (
                cond_artist, cond_album, cond_title,
                change_artist, change_album, change_title,
                pattern_artist, pattern_album, pattern_title,
                to_artist, to_album, to_title,
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
            tracknum=1, seconds=60)
        transform = Transform(1, cond_artist=True, change_artist=True,
            pattern_artist='Foo', to_artist='Bar')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
        self.assertEqual(track.transformed, False)
    
    def test_transform_track_empty_transform(self):
        """
        Given a track, apply a transformation which will never match on
        anything.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            change_artist=True, pattern_artist='Artist', to_artist='Artist 2',
            change_album=True, pattern_album='Album', to_album='Album 2',
            change_title=True, pattern_title='Title', to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
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
    
    def test_transform_track_full_transform(self):
        """
        Given a track, apply a transformation which matches on all fields.
        """
        track = Track(artist='Artist', album='Album', title='Title',
            tracknum=1, seconds=60)
        transform = Transform(1,
            cond_artist=True, change_artist=True, pattern_artist='Artist', to_artist='Artist 2',
            cond_album=True, change_album=True, pattern_album='Album', to_album='Album 2',
            cond_title=True, change_title=True, pattern_title='Title', to_title='Title 2')

        self.assertEqual(track.last_transform, 0)
        transform.apply_track(track)
        self.assertEqual(track.last_transform, 1)
        self.assertEqual(track.artist, 'Artist 2')
        self.assertEqual(track.album, 'Album 2')
        self.assertEqual(track.title, 'Title 2')
        self.assertEqual(track.transformed, True)
    
    def test_transform_album_based_on_artist_album_match(self):
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
    
    def test_transform_album_based_on_artist_album_no_match_album(self):
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
    
    def test_transform_album_based_on_artist_album_no_match_artist(self):
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
    
    def test_transform_artist_based_on_artist_album_match(self):
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
    
    def test_transform_artist_based_on_artist_album_no_match_album(self):
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
    
    def test_transform_artist_based_on_artist_album_no_match_artist(self):
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
    
    def test_transform_title_based_on_artist_title_match(self):
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
    
    def test_transform_title_based_on_artist_title_no_match_title(self):
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
    
    def test_transform_title_based_on_artist_title_no_match_artist(self):
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
    
    def test_transform_artist_based_on_artist_title_match(self):
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
    
    def test_transform_artist_based_on_artist_title_no_match_title(self):
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
    
    def test_transform_artist_based_on_artist_title_no_match_artist(self):
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
    
    def test_transform_album_based_on_album_title_match(self):
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
    
    def test_transform_album_based_on_album_title_no_match_title(self):
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
    
    def test_transform_album_based_on_album_title_no_match_album(self):
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
    
    def test_transform_title_based_on_album_title_match(self):
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
    
    def test_transform_title_based_on_album_title_no_match_title(self):
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
    
    def test_transform_title_based_on_album_title_no_match_album(self):
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
    
    def test_transform_title_based_on_artist_album_match(self):
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
    
    def test_transform_title_based_on_artist_album_no_match_artist(self):
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
    
    def test_transform_title_based_on_artist_album_no_match_album(self):
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

    def test_transform_with_single_transform(self):
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

    def test_transform_with_single_transform_high_id(self):
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

    def test_transform_with_two_transforms(self):
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

    def test_transform_with_two_transforms_with_gap_in_numbering(self):
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

    def test_transform_with_two_transforms_with_gap_in_numbering_and_one_already_applied(self):
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

    def test_transform_with_two_transforms_undo(self):
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

    def test_no_transform_with_already_applied_transform(self):
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

    def test_no_transform_with_song_with_transform_id_greater(self):
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

    def test_two_transforms_with_one_already_applied(self):
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
        self.assertEqual(transform.change_artist, False)
        self.assertEqual(transform.change_album, False)
        self.assertEqual(transform.change_title, False)
        self.assertEqual(transform.pattern_artist, '')
        self.assertEqual(transform.pattern_album, '')
        self.assertEqual(transform.pattern_title, '')
        self.assertEqual(transform.to_artist, '')
        self.assertEqual(transform.to_album, '')
        self.assertEqual(transform.to_title, '')

    def test_load_full_transform(self):
        """
        Load our transform lists when there's one in the database, with all
        possible values set.
        """
        self.add_transform(cond_artist=True, cond_album=True, cond_title=True,
            change_artist=True, change_album=True, change_title=True,
            pattern_artist='Artist', pattern_album='Album', pattern_title='Title',
            to_artist='Artist 2', to_album='Album 2', to_title='Title 2')
        self.app.load_data()
        self.assertEqual(len(self.app.transforms), 1)
        transform = self.app.transforms.transforms[1]
        self.assertEqual(transform.cond_artist, True)
        self.assertEqual(transform.cond_album, True)
        self.assertEqual(transform.cond_title, True)
        self.assertEqual(transform.change_artist, True)
        self.assertEqual(transform.change_album, True)
        self.assertEqual(transform.change_title, True)
        self.assertEqual(transform.pattern_artist, 'Artist')
        self.assertEqual(transform.pattern_album, 'Album')
        self.assertEqual(transform.pattern_title, 'Title')
        self.assertEqual(transform.to_artist, 'Artist 2')
        self.assertEqual(transform.to_album, 'Album 2')
        self.assertEqual(transform.to_title, 'Title 2')

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
        self.assertEqual(track.tracknum, 1)
        self.assertEqual(track.seconds, 2.0)

    def test_load_m4a_file(self):
        """
        Tests loading an m4a file
        """
        track = Track.from_filename(self.track_path('silence.m4a'))
        self.assertEqual(track.artist, 'Artist')
        self.assertEqual(track.album, 'Album')
        self.assertEqual(track.title, 'Title')
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

class TrackDatabaseTests(DatabaseTest):
    """
    Tests of our Track object which require a database.
    """

    def test_insert_simple(self):
        """
        Tests a simple track insert
        """
        track = Track(artist='Artist', album='Album', title='Title',
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
        track = Track(artist='Artist', album='Album', title='Title')
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

        # Now update the object and save out, and test.
        track.artist = 'Artist 2'
        track.album = 'Album 2'
        track.title = 'Title 2'
        track.update(self.app.db, self.app.curs)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album 2')
        self.assertEqual(track_row['title'], 'Title 2')

    def test_update_no_commit(self):
        """
        Tests an update of ourselves without committing
        """
        track = Track(artist='Artist', album='Album', title='Title')
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

        # Now update the object and save out, and test.
        track.artist = 'Artist 2'
        track.album = 'Album 2'
        track.title = 'Title 2'
        track.update(self.app.db, self.app.curs, commit=False)
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist 2')
        self.assertEqual(track_row['album'], 'Album 2')
        self.assertEqual(track_row['title'], 'Title 2')
        self.app.db.rollback()
        self.assertEqual(self.get_track_count(), 1)
        track_row = self.get_track_by_id(pk)
        self.assertEqual(track_row['artist'], 'Artist')
        self.assertEqual(track_row['album'], 'Album')
        self.assertEqual(track_row['title'], 'Title')

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
