
CREATE TABLE schema_version (
  id integer primary key autoincrement
);

CREATE TRIGGER update_childrens_delta_on_update AFTER UPDATE OF sloc ON commits
WHEN new.sloc > 0
BEGIN
  UPDATE commits SET
    delta_sloc=sloc-new.sloc,
    delta_floc=floc-new.floc,
    delta_codefat=codefat-new.codefat
  WHERE parents = new.sha1 and sloc > 0;
END;

CREATE TRIGGER update_its_own_delta_on_update AFTER UPDATE OF sloc ON commits
WHEN new.sloc > 0
  AND 0 < (SELECT count() FROM commits WHERE sha1 = new.parents AND sloc > 0)
BEGIN
  UPDATE commits SET
    delta_sloc=sloc-(SELECT sloc FROM commits WHERE sha1 = new.parents),
    delta_floc=floc-(SELECT floc FROM commits WHERE sha1 = new.parents),
    delta_codefat=codefat-(SELECT codefat FROM commits WHERE sha1 = new.parents)
  WHERE sha1 = new.sha1;
END;

CREATE TRIGGER delete_project_transitively AFTER DELETE ON projects
BEGIN
  DELETE FROM commits WHERE project_id = old.id;
END;
