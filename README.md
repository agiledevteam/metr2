metr web app

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


# config.py

    $ cp config.py.sample config.py
    $ vi config.py

# init db

    $ python
    >>> from metrapp import init_db
    >>> init_db()

# start redis-server

* http://redis.io/topics/quickstart

# run

    $ python runserver.py

