metr web app

# clone

    $ git clone git://github.com/agiledevteam/metr2.git
    $ cd metr2
    $ git submodule init
    $ git submodule update

# pip install

    $ pip install -r requirements.txt

# setup plyj

    $ cd libs/plyj
    $ python setup.py install

# config.py

    $ cp config.py.sample config.py
    $ vi config.py

# init db

    $ python
    >>> from metrapp import init_db
    >>> init_db()

# run

    $ python runserver.py

