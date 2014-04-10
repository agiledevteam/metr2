
drop table if exists projects;
create table projects (
  id integer primary key autoincrement,
  name text not null,
  repository text not null,
  branch text not null
);

drop table if exists commits;
create table commits (
  id integer primary key autoincrement,
  project_id integer,
  author text not null,
  timestamp timestamp,
  sha1 text not null,
  sloc integer,
  dloc double,
  cc integer,
  added integer,
  changed integer,
  deleted integer,
  foreign key(project_id) references projects(id)
);

