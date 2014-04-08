Metr is a web app for monitoring codefat of git repositories.
Codefat is a experimental code metric which indicates how code looks bad. 

# virtualenv

* http://www.virtualenv.org/en/latest/virtualenv.html#installation
* create a virtual environment

    $ virtualenv metr
    $ . metr/bin/activiate

# clone metr2

    $ git clone git://github.com/agiledevteam/metr2.git
    $ cd metr2
    $ git submodule init
    $ git submodule update

# pip install

    $ pip install -r requirements.txt

If `pip install` fails, check the dependencies below

## dependencies

* On Mac OSX,  (March 20, 2014)
* use XCODE 5.0.2 command tool (clang)
* XCODE 5.1 has some bug on command tool (clang)

python-dev

    $ sudo apt-get install python-dev

libgit2

* On Ubuntu, 
* clone libgit2 and install it, then 
* check `LD_LIBRARY_PATH` 

plyj

* This is forked and modified version of origin [plyj](https://github.com/musiKk/plyj)

    $ cd libs/plyj
    $ python setup.py install

sqlite3

redis

* http://redis.io/topics/quickstart


# config.py

    $ cp config.py.sample config.py
    $ vi config.py

Configure DATABASE (sqlite3 database filepath), GITDIR (directory for git repositories)


## initialize database

After configuring you need to initialize database by executing following:

    $ python metrdb.py

# Front-end dependencies

    $ npm install
    $ bower install  # gets front-end dependencies
    $ grunt bower    # copies dependencies to 'static' folder

# run Metr

You can run Metr using embedded web server.

    $ python runserver.py

Alternatively you can run Metr as WSGI application with Apache. Refer to apache-conf/* files.

# add git repository

For now, there is no web interface to add a git repository. Use plain sqlite3 CLI:

    $ sqlite3 metr.db
    > insert into projects (name, repository, branch) values ('MyProject', 'git://...', 'master');

To add multiple repositories, use `python scan_repo.py` after cloning repositories in GIT_DIR. This command will add newly cloned repositories into database.

# update metr

    $ python update_all.py

First time running update will take long (cloning repo, processing all commits/blobs).
