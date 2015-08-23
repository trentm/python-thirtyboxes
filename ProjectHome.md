30boxes.com is a nice web calendaring app with [a simple web API](http://www.30boxes.com/api/). `thirtyboxes.py` provides a Python module binding to this web API and a command-line interface (the latter mostly useful for feeling out the API).

### Project status ###

When I initially wrote this module (back in 2006) the coverage of the 30boxes API was complete. Since then I have not followed changes to the API, so I suspect that its coverage is not complete. I am not currently working on extending thirtyboxes.py, however I am happy to receive patches.


### The module inteface ###

Start the python interactive shell in your terminal and import thirtyboxes.

```
$ python
>>> import thirtyboxes
```

First you need an API key to use any of the API.

```
>>> tb = thirtyboxes.ThirtyBoxes()
```

This will open your browser to a page on 30boxes.com that will give you your API key (once you login to your account on 30boxes) -- a long string that looks something like `1234-1234567890abcdefghijklmnopqrstuv`. Set the APIKEY and then ping 30boxes to see if everything is working fine.

```
>>> import sys, pprint; sys.displayhook = pprint.pprint
>>> tb.api_key = "1234-1234567890abcdefghijklmnopqrstuv"
>>> tb.ping()
{'msg': 'API key for user 1234 was verified.',
 'ping': 'pong'}
```

This API parses the XML responses into more useful Python data structures.

```
>>> tb.find_user(1)
{'avatar': 'http://static.flickr.com/25/97988637_27ec96a24f_o.jpg',
 'createDate': datetime.date(2005, 9, 10),
 'firstName': 'Nick',
 'id': 1,
 ...}

>>> tb.find_user("hamish@example.com")
Traceback (most recent call last):
...
thirtyboxes.ThirtyBoxesAPIError: [Error 3] No users found for 'hamish@example.com'
```

Errors are translated into Python exceptions.

Before you can access a user's private data you need to get another key: the authorized user token ("auth\_token" for short here). A web app using this API will want to [look into](http://30boxes.com/api/#user.Authorize) using the optional `return_url` argument.

```
>>> tb.authorize_user(app_name="My 30boxes Mashup")
```

Again, this will open a browser window asking the user to give confirmation that the app (here "My 30boxes Mashup") may access private information on 30boxes. Without a `return_url` you'll get the authtoken in the browser.

```
>>> tb.auth_token = "1234-vutsrqponmlkjihgfedcba0987654321"
```

Now you can use the API methods that return private data.

```
>>> tb.all_user_info()
{'IM': {'AIM': None, 'MSN': 'hamish@passport.com', 'Yahoo': None},
 'avatar': '...',
 'buddies': [{'lastName': 'McDougal', 'id': 4321, 'firstName': 'Dougal'}],
 'createDate': datetime.date(2006, 2, 5),
 'emails': [{'primary': True, 'address': 'hamish@example.com'}],
 'feeds': [{'name': "hamish's Photos",
            'url': 'http://www.flickr.com/services/feeds/pho...'}],
 'firstName': 'Hamish',
 'id': 1234,
 'lastName': 'McDonald',
 'personalSite': 'http://hamish.example.com/',
 'startDay': 0,
 'use24HourClock': False}

>>> from datetime import date, timedelta
>>> today = date.today()
>>> tomorrow = today + timedelta(1)
>>> tb.events(start=today, end=tomorrow)
{'events': [{'allDayEvent': False,
             'end': datetime.datetime(2006, 3, 25, 22, 0),
             'id': 156569,
             'invitation': {'isInvitation': False},
             'notes': ''
             'privacy': 'shared',
             'repeatEndDate': None,
             'repeatType': 'no',
             'start': datetime.datetime(2006, 3, 25, 19, 0),
             'summary': 'Bagpipe practice',
             'tags': 'pipes'}],
 'listEnd': datetime.date(2006, 3, 26),
 'listStart': datetime.date(2006, 3, 25),
 'userId': 1234}

>>> tb.search('caber toss')
...returns events for caber tossing

>>> tb.tagsearch('pipes')
...returns events tagged with 'pipes'
```


### Storing the API key and authorized user token ###

For convenience of using this module it will automatically pick up an API key stored in either the `THIRTYBOXES_APIKEY` environment variable or in the `~/.30boxes/apikey` file.  As well, you can store your authtoken in either the `THIRTYBOXES_AUTHTOKEN` environment variable or the `~/.30boxes/authtoken` file.

```
$ cat ~/.30boxes/apikey
1234-1234567890abcdefghijklmnopqrstuv
$ cat ~/.30boxes/authtoken
1234-vutsrqponmlkjihgfedcba0987654321"
```


### The command-line interface ###

If you installed thirtyboxes.py to your Python site-packages directory, then you can invoke it with Python's `-m` switch:

```
$ python -m thirtyboxes
...usage output...
```

Otherwise you can just run the script directly:

```
$ python thirtyboxes.py
...usage output...
```

(Bash users might want to setup an alias something like `alias 30b='python -m thirtyboxes'`.)

```
$ 30b ping
pong: API key for user 1234 was verified.

$ 30b user 1234
--- 30boxes user
name           : Hamish McDonald
id             : 1234
personalSite   : http://hamish.example.com/
avatar         : ...
createDate     : 2006-02-05
startDay       : 0
use24HourClock : False
feeds          : 
  - hamish's Photos (http://www.flickr.com/services/feeds/pho...
```


The default output of each command is YAML. You can also get short-form output (one line per item) with '-s' or '--short'.

```
$ 30b -s user 1234
user Hamish McDonald (1234): http://hamish.example.com/
```

The command-line interface should be self-documenting. Use the "help" subcommand to see how to use other subcommands:

```
$ 30b help events
...help for the "events" command
```
