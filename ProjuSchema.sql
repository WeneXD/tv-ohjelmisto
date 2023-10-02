create schema mydb;

create table käyttäjät(
	id int auto_increment not null,
    etunimi varchar(45) not null,
    sukunimi varchar(45) not null,
    salasana varchar(250) not null,
    rooli int not null,
    primary key (id)
);

drop table käyttäjät;

create table työvuoro(
	id int auto_increment not null,
    k_id int not null,
    tv_salku varchar(5) not null,
    tv_sloppu varchar(5) not null,
    tv_alku varchar(5),
    tv_loppu varchar(5),
    työtehtävä varchar(45) not null,
    pvmäärä date not null,
    ylityöt varchar(45),
    kommentti varchar(250),
    primary key (id)
);

drop table työvuoro;