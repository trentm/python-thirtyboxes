This project installs one Python module: `thirtyboxes.py`. It depends on some form of the `ElementTree` python API: any of `xml.etree`, `ElementTree`, `cElementTree` or `lxml`. The command-line interface depends on [cmdln.py](http://code.google.com/p/cmdln). The module should work with Python 2.4, 2.5, 2.6, 2.7. I haven't yet put together a version for Python 3.


# Do I have it installed? #

If you have thirtyboxes.py installed you should be able to do this:

```
$ python -c "import thirtyboxes; print('yes')"
yes
```


# What version do I have installed? #

```
$ python -c "import thirtyboxes; print(thirtyboxes.__version__)"
...your installed version...
```


# How do I install of upgrade? #

Install with **one** of the following methods.

  * Install **with pip** (if you have it):

> `pip install thirtyboxes`

> More on `pip` [here](http://pip.openplans.org/).

  * Install **with easy\_install** (if you have it):

> `easy_install thirtyboxes`

> See good instructions here for installing easy\_install (part of setuptools) [here](http://turbogears.org/2.0/docs/main/DownloadInstall.html#setting-up-setuptools).

  * **Basic** (aka old school) installation:
    1. download the latest `thirtyboxes-$version.zip`
    1. unzip it
    1. run `python setup.py install` in the extracted directory

> For example, for version 0.6.0:
```
wget -q http://python-thirtyboxes.googlecode.com/files/thirtyboxes-0.6.0.zip
unzip thirtyboxes-0.6.0.zip
cd thirtyboxes-0.6.0
python setup.py install
```