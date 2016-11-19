drop table if exists track;
create table track
(
    id int not null auto_increment,
    timestamp datetime,
    artist varchar(200) not null,
    title varchar(255) not null,
    album varchar(200) not null,
    ensemble varchar(200) not null default '',
    conductor varchar(200) not null default '',
    composer varchar(200) not null default '',
    tracknum int,
    seconds int,
    source enum('xmms', 'car', 'stereo', 'cafe', 'vinyl') not null default 'xmms',
    album_id int default 0,
    lasttransform int not null default 0,
    primary key (id),
    index idx_artist (artist),
    index idx_title (title),
    index idx_album (album),
    index idx_ensemble (ensemble),
    index idx_composer (composer),
    index idx_conductor (conductor)
) ENGINE=innodb;

drop table if exists album;
create table album
(
    alid int not null auto_increment,
    alartist varchar(200) not null,
    alalbum varchar(200) not null,
    totaltracks int not null,
    totalseconds int not null,
    lasttransform int not null default 0,
    altype enum('album', 'ep', 'live') not null default 'album',
    primary key (alid),
    unique index idx_total (alartist, alalbum)
) ENGINE=innodb;

drop table if exists transform;
create table transform
(
    tid int not null auto_increment,
    artistcond bool not null default 0,
    albumcond bool not null default 0,
    titlecond bool not null default 0,
    ensemblecond bool not null default 0,
    composercond bool not null default 0,
    conductorcond bool not null default 0,
    artistchange bool not null default 0,
    albumchange bool not null default 0,
    titlechange bool not null default 0,
    ensemblechange bool not null default 0,
    composerchange bool not null default 0,
    conductorchange bool not null default 0,
    artistpat varchar(200),
    albumpat varchar(200),
    titlepat varchar(255),
    ensemblepat varchar(255),
    composerpat varchar(255),
    conductorpat varchar(255),
    artistto varchar(200),
    albumto varchar(200),
    titleto varchar(255),
    ensembleto varchar(255), 
    composerto varchar(255), 
    conductorto varchar(255), 
    primary key (tid)
) ENGINE=innodb;

-- Updates 2016.11.19, our actual live DB didn't actually match our definitions.
/*
alter table album engine=innodb;
alter table track engine=innodb;
alter table transform engine=innodb;
alter table album modify alartist varchar(200) not null,
    modify alalbum varchar(200) not null,
    modify altype enum('album', 'ep', 'live') not null default 'album';
alter table track modify artist varchar(200) not null,
    modify album varchar(200) not null,
    modify source enum('xmms', 'car', 'stereo', 'cafe', 'vinyl') not null default 'xmms';
alter table transform modify artistpat varchar(200),
    modify albumpat varchar(200),
    modify artistto varchar(200),
    modify albumto varchar(200);
*/

-- Updates 2016.11.19, adding in classical music fields, finally
/*
alter table track
    add ensemble varchar(200) not null default '',
    add conductor varchar(200) not null default '',
    add composer varchar(200) not null default '',
    add index idx_ensemble (ensemble),
    add index idx_conductor (composer),
    add index idx_composer (conductor);
alter table transform
    add ensemblecond bool not null default 0,
    add composercond bool not null default 0,
    add conductorcond bool not null default 0,
    add ensemblechange bool not null default 0,
    add composerchange bool not null default 0,
    add conductorchange bool not null default 0,
    add ensemblepat varchar(255),
    add composerpat varchar(255),
    add conductorpat varchar(255),
    add ensembleto varchar(255), 
    add composerto varchar(255), 
    add conductorto varchar(255);
*/
