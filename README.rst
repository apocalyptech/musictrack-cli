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
databases.

The media player plugin was originally for XMMS, then later BMP (Beep 
Media Player, I think?), and finally Audacious.  That plugin can be found
at my `audacious-songchange <https://github.com/apocalyptech/audacious-songchange>`_
project.  The PHP web stuff I'll probably put up in a separate project here
at some point.

The Perl utilities I'm now in the process of rewriting into Python, which
is what I prefer nowadays.

At the moment, I'm just going through and replicating the Perl behavior,
though the end goal is to extend this thing to support classical fields
such as ensemble, composer, and conductor.

So yeah: unlikely to be of interest to anyone else, really.
