#!/usr/bin/env python
# Copyright (c) 2006-2009 ActiveState Software Inc.

"""setup script for 'thirtyboxes'"""

from distutils.core import setup

import thirtyboxes


#---- setup mainline

setup(name="thirtyboxes",
      version=thirtyboxes.__version__,
      description="a Python binding to the 30boxes.com API",
      author="Trent Mick",
      author_email="trentm@gmail.com",
      url="http://code.google.com/p/python-thirtyboxes",
      license="MIT License",
      platforms=["Windows", "Linux", "Mac OS X", "Unix"],
      long_description="""\
`thirtyboxes.py` provides a Python module interface and a command-line
interface to the 30boxes.com API (http://www.30boxes.com/api/). 30boxes
is a web calendaring service.
""",
      keywords=["30boxes", "calendar", "api", "command-line", "web"],

      py_modules=['thirtyboxes'],
     )

