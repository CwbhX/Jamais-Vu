Jamaisvu
==========

A work-in-progress improvement on Will Drevo's [Dejavu](https://github.com/worldveil/dejavu) python library for use at [WJRH](http://wjrh.org) at Lafayette College.
The goals of this improvement is to:
- Flesh out the programme's features
- Add a significant more amount of information about songs
- GPU acceleration via CUDA

## Installation and Dependencies:

- numpy
- scipy
- pycuda
- pyfft
- mysql
- pymsgbox
- pyyaml
- pydub
- pyaudio
- matplotlib

## Setup

First, install the above dependencies.

Second, you'll need to create a MySQL database where Jamaisvu can store fingerprints. For example, on your local setup:

	$ mysql -u root -p
	Enter password: **********
	mysql> CREATE DATABASE IF NOT EXISTS jamaisvu;
