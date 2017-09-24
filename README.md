Jamaisvu
==========

A work-in-progress improvement on Will Drevo's [Dejavu](https://github.com/worldveil/dejavu) python library for use at WJRH at Lafayette College.
The goals of this improvement is to:
- Flesh out the programme's features
- Add a significant more amount of information about songs
- GPU acceleration via CUDA

## Installation and Dependencies:

Read [INSTALLATION.md](INSTALLATION.md)

## Setup

First, install the above dependencies.

Second, you'll need to create a MySQL database where Jamaisvu can store fingerprints. For example, on your local setup:

	$ mysql -u root -p
	Enter password: **********
	mysql> CREATE DATABASE IF NOT EXISTS jamaisvu;

Now you're ready to start fingerprinting your audio collection!

## Quickstart

```bash
$ git clone https://github.com/CwbhX/jamaisvu.git ./jamaisvu
$ cd jamaisvu
$ python example.py
```

## Fingerprinting

Let's say we want to fingerprint all of July 2013's VA US Top 40 hits.

Start by creating a Jamaisvu object with your configurations settings (Jamaisvu takes an ordinary Python dictionary for the settings).

```python
>>> from jamaisvu import Jamaisvu
>>> config = {
...     "database": {
...         "host": "127.0.0.1",
...         "user": "root",
...         "passwd": <password above>,
...         "db": <name of the database you created above>,
...     }
... }
>>> djv = Jamaisvu(config)
```

Next, give the `fingerprint_directory` method three arguments:
* input directory to look for audio files
* audio extensions to look for in the input directory
* number of processes (optional)

```python
>>> djv.fingerprint_directory("va_us_top_40/mp3", [".mp3"], 3)
```

For a large amount of files, this will take a while. However, Jamaisvu is robust enough you can kill and restart without affecting progress: Jamaisvu remembers which songs it fingerprinted and converted and which it didn't, and so won't repeat itself.

You'll have a lot of fingerprints once it completes a large folder of mp3s:
```python
>>> print djv.db.get_num_fingerprints()
5442376
```

Also, any subsequent calls to `fingerprint_file` or `fingerprint_directory` will fingerprint and add those songs to the database as well. It's meant to simulate a system where as new songs are released, they are fingerprinted and added to the database seemlessly without stopping the system.

## Configuration options

The configuration object to the Jamaisvu constructor must be a dictionary.

The following keys are mandatory:

* `database`, with a value as a dictionary with keys that the database you are using will accept. For example with MySQL, the keys must can be anything that the [`MySQLdb.connect()`](http://mysql-python.sourceforge.net/MySQLdb.html) function will accept.

The following keys are optional:

* `fingerprint_limit`: allows you to control how many seconds of each audio file to fingerprint. Leaving out this key, or alternatively using `-1` and `None` will cause Jamaisvu to fingerprint the entire audio file. Default value is `None`.
* `database_type`: as of now, only `mysql` (the default value) is supported. If you'd like to subclass `Database` and add another, please fork and send a pull request!

An example configuration is as follows:

```python
>>> from jamaisvu import Jamaisvu
>>> config = {
...     "database": {
...         "host": "127.0.0.1",
...         "user": "root",
...         "passwd": "Password123",
...         "db": "jamaisvu_db",
...     },
...     "database_type" : "mysql",
...     "fingerprint_limit" : 10
... }
>>> djv = Jamaisvu(config)
```
