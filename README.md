# Jamaisvu

A work-in-progress improvement upon Will Drevo's [Dejavu](https://github.com/worldveil/dejavu) project for audio fingering printing in Python. The aim of Jamaisvu is to be optimised and effective enough to be used as a sound identifier for DJs at Lafayette College's [WJRH Radio](http://wjrh.org).

I occasionally write about the progress of Jamaisvu on my [website](http://clement.nyc), and features and bugs I am currently working on can be viewed on my [Trello board](https://trello.com/b/cGIQLRYg/jamaisvu)

The main goals for Jamaisvu over Dejavu is:

* Provide more features
	* Detailed Information about songs (e.g. Artist, Album, Explicit, etc...)
	* Support API calls to be able to run in the background
	* Provide support for user entry and modification for mislabelled data
* Provide much faster fingerprinting times via optimisations and GPU acceleration
* Be integrated with Renan Dincer's [Teal](https://github.com/wjrh/Teal), which is a nice package for organising and storing radio shows

Eventually this will be used as the backend for [WJRH Assistant](https://github.com/CwbhX/WJRH-Assistant)

## Getting Started

Tested only on MacOS and Ubuntu 16.04

### Prerequisites

What dependencies you will need to run Jamaisvu:

* Numpy
* Scipy
* Pycuda
* AcoustID
* Mysql
* Mysql-config
* Spotipy
* Pymsgbox
* Pydub
* Pyaudio (also portaudio19-dev)
* Reikna
* Scikit-cuda


### Installing

Ensure that you have a MySQL Database instance setup and running on your local machine and then setup a database for Jamaisvu with:

```
$ mysql -u root -p
Enter password: **********
mysql> CREATE DATABASE IF NOT EXISTS jamaisvu;
```


## Hello World

You can use the JMV_Test.py to test to make sure your installation is working correctly


```
$ python JMV_Test.py [path to config.yaml] [path to music file]
```

The programme should fingerprint your file, store it in the database, read the file again, and identify it using the database. It should return something like:

```
Result:
song_genre : canadian pop
confidence : 181436
offset_seconds : 0.0
match_time : 6.18130493164
offset : 0
song_artist : The Weeknd
song_id : 1
song_name : Often - Kygo Remix
file_sha1 : 4EC99324791D7AF5A497FB693FF1DD3DBD3420A1
song_album : Often (Kygo Remix)
song_length : 234400
song_explicit : 1
```


## Acknowledgments

* [Renan Dincer](https://github.com/renandincer) for being supportive of the idea from day 1

