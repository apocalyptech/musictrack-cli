========================
Music Tracking CLI Utils
========================

These are unlikely to be of interest to anyone but myself.  Some time after
signing up for AudioScrobbler in 2005 (which later became last.fm), I wanted
more flexibility in my music tracking (and specifically the ability to run
statistics based on albums rather than just tracks, something which last.fm
has gotten better at over the years, though is still lacking, IMO).

So, I built a system up with a PHP web frontend, Perl utilities for the
"backend" CLI stuff, and a plugin for my media player to mimic
audioscrobbler/last.fm behavior by logging my track listens to my local
databases.  I've since ported the Perl scripts over to a little more
formalized Python version, which is what's found in this repository.

The media player plugin was originally for XMMS, then later BMP (Beep 
Media Player, I think?), and finally Audacious.  That plugin can be found
at my `audacious-songchange <https://github.com/apocalyptech/audacious-songchange>`_
project.  The PHP web stuff I'll probably put up in a separate project here
at some point.

So yeah: unlikely to be of interest to anyone else, really.

Architecture
------------

More for my own reference than anything.  These are all currently coded for
MySQL.  These are only tested on Python 3.4 and higher, and require the following
third-party modules:

* mutagen
* mysqlclient
* parsedatetime

By default the utils will all use a database definition file of the name ``db.ini``,
though alternate files can be specified on the commandline for all utils.  An
example is in ``db.ini.example``.

There's three tables: album, track, and transform.  Album and track are pretty
self-explanatory; track contains an album_id field back to album which should
probably be a foreign key but actually isn't, yet.  D'oh.  As tracks are
inserted into the database, they're associated with an album based on the
artist and album name, and will match on albums with "Various" for the artist
if no specific album is found.

When I update the tags on my media files (to fix typos or the like), I wanted
to have a way to "transform" all the old records which have been already inserted
into the database, hence the transform table.  This table lets you specify which
fields to match on (artist, album, or trackname), and which ones get changed on
any data which matches.  There aren't any regexes or substrings or anything here -
it literally just matches on the full names.

There's no real way to manually put those in, apart from doing so via SQL.
The web interface allows an admin to set them up, which is the most convenient
way by far, 'cause you can just click on the relevant record you're looking to
fix and it'll pre-fill the information.

The transforms by nature aren't really meant to ever be deleted - all tracks
and albums being added to the system will be subjected to the complete list of
transforms.  Once a track's tags have been updated, the track will just stop
matching on the transform.  If you put in a transform and want to revert it,
generally I just add in another transform to undo the change.

The project has complete test coverage, which can be run with ``tests.py``, though
note that it expects to have a database definition file at ``dbtests.ini``, which
it'll use to test things versus a real database.  The test suite will currently
require that the database specified in the file has "test" somewhere in the name.

Utilities
---------

All the utilities use Python's argparse module, and have help that can be
accessed with ``-h`` or ``--help``.

musictrack-log.py
    This is the main utility which adds in tracks to the database.  Called from
    Audacious, or also from the commandline if I want to inject some data which
    Audacious didn't capture for whatever reason.  Can pass in a timestamp to
    backdate the tracks, if desired.  Multiple "sources" can be specified, as I
    was interested in seeing if I listened to different stuff in the car versus
    at home, for instance, though I basically never use that functionality now.

musictrack-albumadd.py
    Pass in a bunch of filenames and it'll add a new Album object to the database.
    Generally this is the first thing I'll do after ripping a CD or whatever.

musictrack-associate.py
    If you listen to some tracks without having run ``musictrack-albumadd.py`` to
    add the album first, those track rows won't have an explicit ``album_id``, so
    won't be linked into the album properly on the web interface.  This utility
    will associate any non-associated track to albums, if possible, so I'll
    typically end up running it once after I add an album, if I'd accidentally
    missed adding the album first.

musictrack-transform.py
    After a new transform is added to the database, any NEW tracks will be inserted
    using the transform, but old tracks won't have it applied yet.  Running this
    will bring all tracks up to the most recent transform.
