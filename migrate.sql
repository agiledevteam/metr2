CREATE TABLE commits_new (
	  id integer primary key autoincrement,
	  project_id integer,
	  author text not null,
	  timestamp timestamp,
	  sha1 text not null,
	  message text,
	  parents text,
	  sloc integer,
	  floc double,
	  codefat double,
	  delta_sloc integer,
	  delta_floc double,
	  delta_codefat double,
	  foreign key(project_id) references projects(id)
);

INSERT INTO commits_new 
	SELECT id, project_id, author, timestamp, sha1, '', '', 
		sloc, (sloc-dloc) as floc, 100*(1-dloc/sloc),
		0, 0, 0 from commits;

DROP TABLE commits;

ALTER TABLE commits_new RENAME TO commits;

