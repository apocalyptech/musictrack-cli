#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

import unittest

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

if __name__ == '__main__':

    # Create our database
    app = App('dbtests.ini', load_data=False)
    app._initialize_db()
    app.close()

    # Run tests
    unittest.main(exit=False)

    # Tear down database
    pp = App('dbtests.ini', load_data=False)
    pp._drop_db()
    pp.close()
