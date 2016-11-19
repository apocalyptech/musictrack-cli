drop table if exists track;
create table track
(
	id int not null auto_increment,
	timestamp datetime,
	artist varchar(200) not null,
	title varchar(255) not null,
	album varchar(200) not null,
	tracknum int,
	seconds int,
	source enum('xmms', 'car', 'stereo', 'cafe', 'vinyl') not null default 'xmms',
	album_id int default 0,
	lasttransform int not null default 0,
	primary key (id),
	index idx_artist (artist),
	index idx_title (title),
	index idx_album (album)
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
	artistchange bool not null default 0,
	albumchange bool not null default 0,
	titlechange bool not null default 0,
	artistpat varchar(200),
	albumpat varchar(200),
	titlepat varchar(255),
	artistto varchar(200),
	albumto varchar(200),
	titleto varchar(255),
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
