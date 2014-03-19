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

# run Metr

You can run Metr using embedded web server.

    $ python runserver.py

Alternatively you can run Metr as WSGI application with Apache. Refer to apache-conf/* files.

# add git repository

For now, there is no web interface to add a git repository. Use plain sqlite3 CLI:

    $ sqlite3 metr.db
    > insert into projects (name, repository, branch) values ('MyProject', 'git://...', 'master');

# update metr

    $ python update_all.py

First time running update will take long (cloning repo, processing all commits/blobs).
