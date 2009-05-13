#!/usr/bin/env python
# Copyright (c) 2006 ActiveState Software Inc.
# License: MIT License (http://www.opensource.org/licenses/mit-license.php)
# Contributors:
#   Trent Mick (TrentM@ActiveState.com)

r"""A Python interface to the 30boxes calender public API [1].

This file provides both module and command-line interfaces [2].
To use most of the 30boxes API you'll need to get an API key and a user
authorization token. See below in this docstring for more info.

First the module interface:

    >>> import sys, pprint
    >>> sys.displayhook = pprint.pprint  # make big dicts look nice
    >>> import thirtyboxes
    >>> tb = thirtyboxes.ThirtyBoxes()
    >>> tb.ping()
    {'msg': 'API key for user 1234 was verified.', 'ping': 'pong'}
    >>> t.find_user(1741)
    {'personalSite': 'http://trentm.com/',
     'firstName': 'Trent',
     ...}
    >>> t.search("bike")
    {'search': 'bike', 'userId': 1234, 'events': [
     {'summary': 'bike to work',
      'end': datetime.datetime(2006, 2, 6, 0, 0),
      ...},
     ...]}

The command-line interface should be self-documenting. Start with:

    $ python thirtyboxes.py -h
    30boxes.com calendar API

    usage:
        thirtyboxes SUBCOMMAND [ARGS...]
        thirtyboxes help SUBCOMMAND
    ...

    $ python thirtyboxes.py ping
    pong: API key for user 1234 was verified.

    $ python thirtyboxes.py user 1
    --- 30boxes user
    name           : Nick Wilder
    id             : 1
    personalSite   : ...
    ...

    $ python thirtyboxes.py tagsearch work
    --- 30boxes events for user 1234 with tag 'work'
    - summary : bike to work
      date    : 2006-02-06 (all day)
      tags    : personal work
      privacy : shared
      id      : 12345
    - summary : weekly meeting
    ...

By default `thirtyboxes.ThirtyBoxes' and the command line interface will
for your API key in `~/.30boxes/apikey' and a user authorization token
in `~/.30boxes/authtoken'. Alternatively they can be specified manually
(constructor args, command line options, environment vars). See the
relevant help for details.

[1] See http://30boxes.com/api/ for details on the API.
[2] The command-line interface requires the cmdln.py module from:
    http://trentm.com/projects/cmdln/
"""

__version_info__ = (0, 6, 0)
__version__ = '.'.join(map(str, __version_info__))

import os
from os.path import expanduser, exists, join
import sys
import getopt
import stat
import logging
from urllib2 import urlopen, URLError
import webbrowser
import datetime
import operator
from pprint import pprint
from cStringIO import StringIO
import re
import warnings

# Import ElementTree (needed for any by the "raw" interface).
try:
    import xml.etree.ElementTree as ET # in python >=2.5
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        try:
            import elementtree.ElementTree as ET
        except ImportError:
            try:
                import lxml.etree as ET
            except ImportError:
                warnings.warn("could not import ElementTree "
                              "(http://effbot.org/zone/element-index.htm) "
                              "required for anything but the 'raw' 30boxes "
                              "Python API")


#---- exceptions and globals

class ThirtyBoxesError(Exception):
    pass

class ThirtyBoxesAPIError(ThirtyBoxesError):
    def __init__(self, code, msg):
        """Create a 30boxes API Error from an error code and message."""
        self.code = code
        self.msg = msg
    def __str__(self):
        return "[Error %d] %s" % (self.code, self.msg)


log = logging.getLogger("30boxes")
API_URL = "http://30boxes.com/api/api.php"



#---- the top-level function-based 30boxes.com API
# This is what thirtyboxes.py 0.1.0 presented. These APIs are deprecated
# and will go away in a version or two.

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    # C.f. http://wiki.python.org/moin/PythonDecoratorLibrary
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s. Use the equivalent "
                      "functions on the ThirtyBoxes or RawThirtyBoxes "
                      "classes." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

@deprecated
def getKeyForUser():
    tb = RawThirtyBoxes()
    return tb.getKeyForUser()

@deprecated
def test_Ping(apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    tb = RawThirtyBoxes(apiKey)
    return tb.test_Ping()

@deprecated
def user_FindByEmail(email, apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    tb = RawThirtyBoxes(apiKey)
    return tb.user_FindByEmail(email)

@deprecated
def user_FindById(id, apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    tb = RawThirtyBoxes(apiKey)
    return tb.user_FindById(id)

@deprecated
def user_Authorize(applicationName, applicationLogoUrl=None,
                   returnUrl=None, apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    tb = RawThirtyBoxes(apiKey)
    return tb.user_Authorize(applicationName, applicationLogoUrl,
                             returnUrl)

@deprecated
def user_GetAllInfo(authorizedUserToken=None, apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    if authorizedUserToken is None:
        authorizedUserToken = _get_authorized_user_token()
    tb = RawThirtyBoxes(apiKey, authorizedUserToken)
    return tb.user_GetAllInfo()

@deprecated
def events_Get(start=None, end=None, authorizedUserToken=None,
               apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    if authorizedUserToken is None:
        authorizedUserToken = _get_authorized_user_token()
    tb = RawThirtyBoxes(apiKey, authorizedUserToken)
    return tb.events_Get(start, end)

@deprecated
def events_Search(query, authorizedUserToken=None, apiKey=None):
    if apiKey is None:
        apiKey = _get_api_key()
    if authorizedUserToken is None:
        authorizedUserToken = _get_authorized_user_token()
    tb = RawThirtyBoxes(apiKey, authorizedUserToken)
    return tb.events_Search(query)

@deprecated
def events_TagSearch(tag, authorizedUserToken=None, apiKey=None):
    """Return all events tagged with the given tag.

    See user_Authorize for getting an 'authorizedUserToken'. 
    """
    if apiKey is None:
        apiKey = _get_api_key()
    if authorizedUserToken is None:
        authorizedUserToken = _get_authorized_user_token()
    tb = RawThirtyBoxes(apiKey, authorizedUserToken)
    return tb.events_TagSearch(tag)



#---- the raw 30boxes.com API

class RawThirtyBoxes(object):
    def __init__(self, apiKey=None, authorizedUserToken=None):
        self.apiKey = apiKey
        self.authorizedUserToken = authorizedUserToken

    def getKeyForUser(self):
        url = self._url_from_method_and_args("getKeyForUser")
        webbrowser.open(url)

    def test_Ping(self):
        return self._api_call("test.Ping", apiKey=self.apiKey)

    def user_FindByEmail(self, email):
        return self._api_call("user.FindByEmail", email=email,
                              apiKey=self.apiKey)

    def user_FindById(self, id):
        return self._api_call("user.FindById", id=id, apiKey=self.apiKey)

    def user_Authorize(self, applicationName, applicationLogoUrl=None,
                       returnUrl=None):
        url = self._url_from_method_and_args("user.Authorize",
                applicationName=applicationName,
                applicationLogoUrl=applicationLogoUrl,
                returnUrl=returnUrl,
                apiKey=self.apiKey)
        webbrowser.open(url)

    def user_GetAllInfo(self):
        """Get all info on the authorized user.
        
        See user_Authorize for getting an 'authorizedUserToken'. 
        """
        return self._api_call("user.GetAllInfo",
                              authorizedUserToken=self.authorizedUserToken,
                              apiKey=self.apiKey)

    def events_Get(self, start=None, end=None):
        """Get all events in the given date range.

        See user_Authorize for getting an 'authorizedUserToken'. 
        """
        return self._api_call("events.Get",
                              start=start,
                              end=end,
                              authorizedUserToken=self.authorizedUserToken,
                              apiKey=self.apiKey)

    def events_Search(self, query):
        """Return all events matching the given query.

        See user_Authorize for getting an 'authorizedUserToken'. 
        """
        return self._api_call("events.Search",
                              query=query,
                              authorizedUserToken=self.authorizedUserToken,
                              apiKey=self.apiKey)

    def events_TagSearch(self, tag):
        """Return all events tagged with the given tag.

        See user_Authorize for getting an 'authorizedUserToken'. 
        """
        return self._api_call("events.TagSearch",
                              tag=tag,
                              authorizedUserToken=self.authorizedUserToken,
                              apiKey=self.apiKey)

    def _api_call(self, method, **args):
        url = self._url_from_method_and_args(method, **args)
        log.debug("call `%s'", url)
        f = urlopen(url)
        xml_response = f.read()
        return xml_response

    def _url_from_method_and_args(self, method, **args):
        from urllib import quote
        url = API_URL + "?method=%s" % method
        for name, value in args.items():
            if value is not None:
                url += "&%s=%s" % (quote(str(name)), quote(str(value)))
        return url



#---- the richer, more-Pythonic 30boxes.com module API

class ThirtyBoxes(object):
    def __init__(self, api_key=None, auth_token=None):
        if api_key is None:
            api_key = ThirtyBoxes._api_key_from_env()
        if auth_token is None:
            auth_token = ThirtyBoxes._auth_token_from_env()
        self._api = RawThirtyBoxes(api_key, auth_token)

    def _get_api_key_prop(self):
        return self._api.api_key
    def _set_api_key_prop(self, api_key):
        self._api.apiKey = api_key
    api_key = property(_get_api_key_prop, _set_api_key_prop, None,
                       "30boxes API key")

    def _get_auth_token_prop(self):
        return self._api.auth_token
    def _set_auth_token_prop(self, auth_token):
        self._api.authorizedUserToken = auth_token
    auth_token = property(_get_auth_token_prop, _set_auth_token_prop, None,
                          "30boxes authorized user token")

    @staticmethod
    def _api_key_from_env():
        """Look for a 30boxes API key.

        First look for the THIRTYBOXES_APIKEY environment variable, then for
        `~/.30boxes/apikey'.
        """
        apikey = None
        if "THIRTYBOXES_APIKEY" in os.environ:
            log.debug("using API key from THIRTYBOXES_APIKEY env var")
            apikey = os.environ["THIRTYBOXES_APIKEY"]
        else:
            apikey_path = expanduser(join("~", ".30boxes", "apikey"))
            if exists(apikey_path):
                log.debug("using API key from `%s'", apikey_path)
                apikey = open(apikey_path, 'r').read().strip()
        return apikey

    @staticmethod
    def _auth_token_from_env():
        """Look for a 30boxes authenticated user token (auth token).

        First look for the THIRTYBOXES_AUTHTOKEN environment variable, then for
        `~/.30boxes/authtoken'.
        """
        authtoken = None
        if "THIRTYBOXES_AUTHTOKEN" in os.environ:
            log.debug("using auth token from THIRTYBOXES_AUTHTOKEN env var")
            authtoken = os.environ["THIRTYBOXES_AUTHTOKEN"]
        else:
            authtoken_path = expanduser(join("~", ".30boxes", "authtoken"))
            if exists(authtoken_path):
                log.debug("using auth token from `%s'", authtoken_path)
                authtoken = open(authtoken_path, 'r').read().strip()
        return authtoken

    #XXX Need to walk through a web app example that uses these
    #    and document how to use that.
    def get_api_key(self):
        self._api.getKeyForUser()
    def authorize_user(self, app_name, app_logo_url=None, return_url=None):
        self._api.user_Authorize(app_name, app_logo_url, return_url)

    def ping(self):
        response = self._api.test_Ping()
        return _parse_response("ping", response, _ping_unmarshallers)

    def find_user(self, id):
        try:
            int(id)
        except ValueError:
            response = self._api.user_FindByEmail(id)
        else:
            response = self._api.user_FindById(id)
        return _parse_response("user", response, _user_unmarshallers)

    def all_user_info(self):
        response = self._api.user_GetAllInfo()
        return _parse_response("user", response, _user_unmarshallers)

    def events(self, start=None, end=None):
        """Return events that start on or after "start" to on or before
        "end".

            "start" (optional) is a Python datetime or date instance
                It defaults to today.
            "end" (optional" is a Python datetime or date instance.
                It defaults to "start" + 90 days and cannot be more than
                180 days after "start".
        """
        if start:
            if isinstance(start, datetime.datetime):
                start_str = start.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(start, datetime.date):
                start_str = start.strftime("%Y-%m-%d")
            else:
                raise ThirtyBoxesError("invalid 'start' argument: must be "
                                       "datetime.datetime or datetime.date: "
                                       "%r" % start)
        else:
            start_str = None
        if end:
            if isinstance(end, datetime.datetime):
                end_str = end.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(end, datetime.date):
                end_str = end.strftime("%Y-%m-%d")
            else:
                raise ThirtyBoxesError("invalid 'end' argument: must be "
                                       "datetime.datetime or datetime.date: "
                                       "%r" % end)
        else:
            end_str = None

        response = self._api.events_Get(start_str, end_str)
        return _parse_response("events", response, _events_unmarshallers)

    def search(self, query):
        response = self._api.events_Search(query)
        return _parse_response("events", response, _events_unmarshallers)

    def tag_search(self, tag):
        response = self._api.events_TagSearch(tag)
        return _parse_response("events", response, _events_unmarshallers)




#---- internal support stuff

def _datetime_from_datetime_str(datetime_str, purpose=None):
    """Return a datetime.datetime or datetime.date object representing
    the given date(time) string.

    For now just support:
        YYYY-MM-DD              datetime.date()
        YYYY-MM-DD HH:MM:SS     datetime.datetime()
        0000-00-00              None (i.e. not applicable)
    """
    try:
        if datetime_str == "0000-00-00":
            return None
        if ' ' in datetime_str:
            return datetime.datetime(*
                map(int, re.split('[- :]', datetime_str))
            )
        else:
            return datetime.date(*
                map(int, datetime_str.split('-'))
            )
    except (TypeError, ValueError), ex:
        if purpose:
            purpose_str = " for "+purpose
        else:
            purpose_str = ""
        raise ThirtyBoxesError("'%s': could not parse datetime string%s: %s "
                               "(must match 'YYYY-MM-DD' or "
                               "'YYYY-MM-DD HH:MM:SS')"
                               % (datetime_str, purpose_str, ex))

def _unmarshal_rsp(elem):
    if elem.get("stat") == "fail":
        raise ThirtyBoxesAPIError(**elem[0].text)
    assert elem.get("stat") == "ok"
    if len(elem) == 1:
        return elem[0].text # e.g. the <user> subelement
    else:
        return dict([(elem[i].tag, elem[i].text) for i in range(len(elem))])

def _unmarshal_err(elem):
    return {
        "code": int(elem.get("code")),
        "msg":  elem.get("msg"),
    }

def _unmarshal_user_elem(elem):
    user = {}
    for child in elem:
        if child.tag == "feed":
            if "feeds" not in user:
                user["feeds"] = []
            user["feeds"].append(child.text)
        elif child.tag == "email":
            if "emails" not in user:
                user["emails"] = []
            user["emails"].append(child.text)
        elif child.tag == "IM":
            if "IM" not in user:
                user["IM"] = {}
            user["IM"][child.text["type"]] = child.text["username"]
        elif child.tag == "buddy":
            if "buddies" not in user:
                user["buddies"] = []
            user["buddies"].append(child.text)
        else:
            user[child.tag] = child.text
    return user

def _unmarshal_eventList(elem):
    event_list = {
        "events": [],
    }
    for child in elem:
        if child.tag == "event":
            event_list["events"].append(child.text)
        else:
            event_list[child.tag] = child.text
    return event_list

def _unmarshal_notes(elem):
    notes = elem.text
    for child in elem:
        assert child.tag == "br"
        if child.tag == "br":
            notes += child.text or ''
    return notes

_events_unmarshallers = {
    "rsp": _unmarshal_rsp,
    "err": _unmarshal_err,

    "lastUpdate": lambda x: x.text, 
    "repeatSkipDates": lambda x: x.text,
    "reminder": lambda x: x.text, 
    "externalUID": lambda x: x.text,
    "repeatICal": lambda x: x.text, 
    "eventList": _unmarshal_eventList,
    "event": lambda x: dict([(x[i].tag, x[i].text) for i in range(len(x))]),
    #XXX Not sure about bounds of <invitation> yet. Ask on forum.
    "invitation": lambda x: dict([(x[i].tag, x[i].text) for i in range(len(x))]),

    "userId": lambda x: int(x.text),
    "search": lambda x: x.text,
    "tagSearch": lambda x: x.text,
    "listStart": lambda x: _datetime_from_datetime_str(x.text, "'listStart' tag"),
    "listEnd": lambda x: _datetime_from_datetime_str(x.text, "'listEnd' tag"),
    "id": lambda x: int(x.text),
    "summary": lambda x: x.text,
    "notes": _unmarshal_notes,
    "br": lambda x: '\n' + (x.tail or ''), # <br/> in <notes> content -> '\n'
    "start": lambda x: _datetime_from_datetime_str(x.text, "event 'start' tag"),
    "end": lambda x: _datetime_from_datetime_str(x.text, "event 'end' tag"),
    "allDayEvent": lambda x: operator.truth(int(x.text)),
    "repeatType": lambda x: x.text,
    "repeatEndDate": lambda x: _datetime_from_datetime_str(x.text, "event 'repeatEndDate' tag"),
    "tags": lambda x: x.text,
    "privacy": lambda x: x.text,
    "isInvitation": lambda x: operator.truth(int(x.text)),
}

_user_unmarshallers = {
    "rsp": _unmarshal_rsp,
    "err": _unmarshal_err,

    "user": _unmarshal_user_elem,
    "feed": lambda x: dict([(x[i].tag, x[i].text) for i in range(len(x))]),
    "email": lambda x: dict([(x[i].tag, x[i].text) for i in range(len(x))]),
    "IM": lambda x: dict([(x[i].tag, x[i].text) for i in range(len(x))]),
    "buddy": _unmarshal_user_elem,

    "id": lambda x: int(x.text),
    "facebookId": lambda x: int(x.text), 
    "status": lambda x: x.text, 
    "dateFormat": lambda x: x.text,
    "bio": lambda x: x.text,    
    "timeZone": lambda x: x.text, 
    "firstName": lambda x: x.text,
    "lastName": lambda x: x.text,
    "avatar": lambda x: x.text,
    "createDate": lambda x: datetime.date(*map(int, x.text.split('-'))),
    "startDay": lambda x: int(x.text),
    "use24HourClock": lambda x: operator.truth(int(x.text)),
    "personalSite": lambda x: x.text,
    "name": lambda x: x.text,
    "url": lambda x: x.text,
    "type": lambda x: x.text,
    "username": lambda x: x.text,
    "address": lambda x: x.text,
    "primary": lambda x: operator.truth(int(x.text)),
}

_ping_unmarshallers = {
    "rsp": _unmarshal_rsp,
    "err": _unmarshal_err,
    "ping": lambda x: x.text,
    "msg": lambda x: x.text,
}

def _parse_response(what, response, unmarshallers):
    if log.isEnabledFor(logging.DEBUG):
        log.debug("response:\n%s", _indent(response))
    file = StringIO(response)
    parser = ET.iterparse(file)
    for action, elem in parser:
        unmarshaller = unmarshallers.get(elem.tag)
        if unmarshaller:
            data = unmarshaller(elem)
            elem.clear()
            elem.text = data
        else:
            raise ThirtyBoxesError("unknown %s tag: %r" % (what, elem.tag))
    return parser.root.text


# Recipe: indent (0.2.1) in /Users/trentm/tm/recipes/cookbook
def _indent(s, width=4, skip_first_line=False):
    """_indent(s, [width=4]) -> 's' indented by 'width' spaces

    The optional "skip_first_line" argument is a boolean (default False)
    indicating if the first line should NOT be indented.
    """
    lines = s.splitlines(1)
    indentstr = ' '*width
    if skip_first_line:
        return indentstr.join(lines)
    else:
        return indentstr + indentstr.join(lines)


def _get_api_key():
    apikey = ThirtyBoxes._api_key_from_env()
    if apikey is None:
        if __name__ == "__main__":
            first_opt = "1. use the -k|--api-key option,"
        else:
            first_opt = "1. use the apiKey argument,"
        raise ThirtyBoxesError("""could not determine API key:
    %s
    2. set the THIRTYBOXES_APIKEY environment variable, or
    3. create `%s'.
See `http://30boxes.com/api/' for information on getting an API key."""
% (first_opt, apikey_path))
    return apikey

def _get_authorized_user_token():
    authtoken = ThirtyBoxes._auth_token_from_env()
    if authtoken is None:
        if __name__ == "__main__":
            first_opt = "1. use the -a|--auth-token option,"
        else:
            first_opt = "1. use the authorizedUserToken argument,"
        raise ThirtyBoxesError("""could not determine auth token:
    %s
    2. set the THIRTYBOXES_AUTHTOKEN environment variable, or
    3. create `%s'.
See `http://30boxes.com/api/#user.Authorize' for information on getting
an authorization token.""" % (first_opt, authtoken_path))
    return authtoken



#---- the command-line interface

if __name__ == "__main__":
    import cmdln # for cmdln iface you need cmdln.py from http://trentm.com/projects/cmdln/

    class Shell(cmdln.Cmdln):
        """30boxes.com calendar API

        usage:
            ${name} SUBCOMMAND [ARGS...]
            ${name} help SUBCOMMAND

        ${option_list}
        ${command_list}
        ${help_list}
        """
        name = "thirtyboxes"
        _api = None # lazily assigned ThirtyBoxes() instance

        def _get_api(self):
            if self._api is None:
                self._api = ThirtyBoxes(self.options.api_key,
                                        self.options.auth_token)
            return self._api

        def do_getapikey(self, subcmd, opts):
            """get a 30boxes API key necessary for using the rest of the API

            ${cmd_usage}
            ${cmd_option_list}
            This will open a browser to show you your API key (once you have
            logged into your 30boxes.com account).
            
            The API key may then be specified for subsequent calls by any
            of the following: 
                1. manually via the -k/--api-key option,
                2. set to the THIRTYBOXES_APIKEY environment variable, or
                3. saved in `~/.30boxes/apikey'.
            """
            self._get_api().get_api_key()

        def do_ping(self, subcmd, opts):
            """ping the 30boxes API

            ${cmd_usage}
            ${cmd_option_list}
            """
            api = self._get_api()
            response = api.ping()
            if self.options.output_format == "raw":
                print response
            else:
                print "%(ping)s: %(msg)s" % response

        def do_user(self, subcmd, opts, email_or_id):
            """get public info for the given user

            ${cmd_usage}
            ${cmd_option_list}

            This is a mingling of user.FindByEmail and user.FindById
            from the 30boxes.com API.
            """
            api = self._get_api()
            response = api.find_user(email_or_id)
            if self.options.output_format == "raw":
                pprint(response)
            elif self.options.output_format == "short":
                # user Joe Blow (1234): site
                s = "user %(firstName)s %(lastName)s (%(id)s)" % response
                extras = []
                if "personalSite" in response:
                    extras.append(response["personalSite"])
                #for feed in response["feeds"]:
                #    extras.append("%(name)s (%(url)s)" % feed)
                if extras:
                    s += ": " + ', '.join(extras)
                print s
            else:
                longest_key = max([len(k) for k in response
                                   if response[k] is not None])
                template = "%%-%ds : %%s" % longest_key
                lines = [
                    "--- 30boxes user",
                    template % ("name", "%(firstName)s %(lastName)s" % response),
                ]
                extras = ["id", "avatar", "createDate", "startDay", "use24HourClock"]
                if "personalSite" in response:
                    extras.append("personalSite")
                for key in extras:
                    lines.append(template % (key, response[key]))
                if response["feeds"]:
                    lines.append(template % ("feeds", ""))
                    for feed in response["feeds"]:
                        lines.append("  - %(name)s (%(url)s)" % feed)
                print '\n'.join(lines)

        @cmdln.option("-r", "--return-url",
                      help="return URL to which authorization will redirect")
        @cmdln.option("-l", "--app-logo-url",
                      help="application logo URL (max 150 chars)")
        def do_authorize_user(self, subcmd, opts, app_name):
            """authorize a user

            ${cmd_usage}
            ${cmd_option_list}
            This will open a browser to authorize the user with 30boxes.
            This authorization process will provide an
            'authorizedUserToken', or auth token for short, that must then
            be used for many of the other API functions.
            
            The auth token may then be specified for subsequent calls by any
            of the following: 
                1. manually via the -a/--auth-token option,
                2. set to the THIRTYBOXES_AUTHTOKEN environment variable, or
                3. saved in `~/.30boxes/authtoken'.
            """
            api = self._get_api()
            api.authorize_user(app_name, opts.app_logo_url, opts.return_url)

        def do_alluserinfo(self, subcmd, opts):
            """get all info on the authorized user

            ${cmd_usage}
            ${cmd_option_list}
            See "${name} help authorize" for information on authorizing a user.
            """
            api = self._get_api()
            response = api.all_user_info()
            if self.options.output_format == "raw":
                pprint(response)
            elif self.options.output_format == "short":
                # Short output for "user" is:
                #   user Joe Blow (1234): <site>
                # user Joe Blow (1234): joe@aol.com, <site>, <IMs>
                s = "user %(firstName)s %(lastName)s (%(id)s)" % response
                extras = []
                tail_extras = []
                for email in response["emails"]:
                    if email["primary"]:
                        extras.append(email["address"])
                    else:
                        tail_extras.append(email["address"])
                if "personalSite" in response:
                    extras.append(response["personalSite"])
                for im_name, im_addr in response["IM"].items():
                    if im_addr:
                        extras.append("%s:%s" % (im_name.lower(), im_addr))
                #for feed in response["feeds"]:
                #    extras.append("%(name)s (%(url)s)" % feed)
                extras += tail_extras
                if extras:
                    s += ": " + ', '.join(extras)
                print s
            else:
                longest_key = max([len(k) for k in response
                                   if response[k] is not None])
                template = "%%-%ds : %%s" % longest_key
                lines = [
                    "--- 30boxes user",
                    template % ("name", "%(firstName)s %(lastName)s" % response),
                ] 
                for key in ("id", "personalSite", "avatar",
                            "createDate", "startDay", "use24HourClock"):
                    lines.append(template % (key, response[key]))
                if response["emails"]:
                    lines.append(template % ("emails", ""))
                    for email in response["emails"]:
                        if email["primary"]:
                            lines.append("  - %s (primary)" % email["address"])
                        else:
                            lines.append("  - %s" % email["address"])
                ims = dict((k, v) for k, v in response["IM"].items()
                           if v is not None)
                if ims:
                    lines.append(template % ("IM", ""))
                    for im_name, im_addr in ims.items():
                        lines.append("  - %s (%s)" % (im_addr, im_name))
                if response["feeds"]:
                    lines.append(template % ("feeds", ""))
                    for feed in response["feeds"]:
                        lines.append("  - %(name)s (%(url)s)" % feed)
                print '\n'.join(lines)

        def do_events(self, subcmd, opts, start=None, end=None):
            """list all events for the given date range

            ${cmd_usage}
            ${cmd_option_list}
            Returns events starting on or after START (defaults to
            today) and starting before END (defaults to START + 90
            days). END cannot be more than 120 days after START.

            Start and end dates must be formatted as 'YYYY-MM-DD' and
            time/dates as 'YYYY-MM-DD HH:MM:SS' (the same as mysql).
            
            See "${name} help authorize" for information on authorizing
            a user.
            """
            api = self._get_api()
            if start:
                start_dt = _datetime_from_datetime_str(start)
            else:
                start_dt = None
            if end:
                end_dt = _datetime_from_datetime_str(end)
            else:
                end_dt = None
            response = api.events(start_dt, end_dt)
            if self.options.output_format == "raw":
                pprint(response)
            elif self.options.output_format == "short":
                for event in response["events"]:
                    print self._summary_line_from_event(event)
            else:
                lines = [
                    "--- 30boxes events for user %(userId)s "
                        "(%(listStart)s to %(listEnd)s)" % response,
                ] 
                events = response["events"]
                if events:
                    lines += self._yaml_lines_from_events(events)
                print '\n'.join(lines)  


        def do_search(self, subcmd, opts, query):
            """list all events matching QUERY

            ${cmd_usage}
            ${cmd_option_list}
            See "${name} help authorize" for information on authorizing a user.
            """
            api = self._get_api()
            response = api.search(query)
            if self.options.output_format == "raw":
                pprint(response)
            elif self.options.output_format == "short":
                for event in response["events"]:
                    print self._summary_line_from_event(event)
            else:
                lines = [
                    "--- 30boxes events for user %(userId)s matching "
                        "'%(search)s'" % response,
                ] 
                events = response["events"]
                if events:
                    lines += self._yaml_lines_from_events(events)
                print '\n'.join(lines).encode("UTF-8") 

        def do_tagsearch(self, subcmd, opts, tag):
            """list all events tagged with TAG

            ${cmd_usage}
            ${cmd_option_list}
            See "${name} help authorize" for information on authorizing a user.
            """
            api = self._get_api()
            response = api.tag_search(tag)
            if self.options.output_format == "raw":
                pprint(response)
            elif self.options.output_format == "short":
                for event in response["events"]:
                    print self._summary_line_from_event(event)
            else:
                lines = [
                    "--- 30boxes events for user %(userId)s with tag "
                        "'%(tagSearch)s'" % response,
                ] 
                events = response["events"]
                if events:
                    lines += self._yaml_lines_from_events(events)
                print '\n'.join(lines).encode("UTF-8")

        def _date_summary_from_range(self, start, end, allDayEvent):
            date_summary = ""
            if allDayEvent:
                date_summary += str(start.date())
            else:
                if start.second == 0:
                    date_summary += start.strftime("%Y-%m-%d %H:%M")
                else:
                    date_summary += start.strftime("%Y-%m-%d %H:%M:%S")
            if start == end:
                pass
            elif start.date() == end.date():
                if end.second == 0:
                    date_summary += "-%s" % end.strftime("%H:%M")
                else:
                    date_summary += "-%s" % end.strftime("%H:%M:%S")
            else:
                if end.second == 0:
                    date_summary += " - %s" % end.strftime("%Y-%m-%d %H:%M")
                else:
                    date_summary += " - %s" % end.strftime("%Y-%m-%d %H:%M:%S")
            return date_summary
            
        def _summary_line_from_event(self, event):
            # event '<summary>' at <date> <repeat-info>
            s = "event '%s' at " % event["summary"]
            s += self._date_summary_from_range(event["start"],
                                               event["end"],
                                               event["allDayEvent"])
            if event["repeatType"] != "no":
                s += " repeat " + event["repeatType"]
                if event["repeatEndDate"]:
                    s += " until %(repeatEndDate)s" % event
            return s

        def _yaml_lines_from_events(self, events):
            # - summary: <summary>
            #   date: <start>[ - <end>]     # if different
            #   # iff repeatType != "no"
            #   [repeat: <repeatType>[ until <repeatEndDate>]]
            #   [tags: <tags>]
            #   privacy: <privacy>
            #   id: <id>
            #   invitation: ???             # iff isInvitation
            #   notes:
            #     <notes>
            lines = []
            for event in events:
                lines.append("- summary : %(summary)s" % event)
                date_summary = self._date_summary_from_range(
                    event["start"], event["end"], event["allDayEvent"])
                lines.append("  date    : %s" % date_summary)
                if event["allDayEvent"]:
                    lines[-1] += " (all day)"
                if event["repeatType"] != "no":
                    lines.append("  repeat  : %(repeatType)s" % event)
                    if event["repeatEndDate"]:
                        lines[-1] += " until %(repeatEndDate)s" % event
                if event["tags"]:
                    lines.append("  tags    : %(tags)s" % event)
                lines.append("  privacy : %(privacy)s" % event)
                lines.append("  id      : %(id)s" % event)
                if event["invitation"]["isInvitation"]:
                    lines.append("  invitation: ??? %(invitation)r"
                                 % event)
                if event["notes"]:
                    lines.append("  notes   :")
                    lines.append(_indent(event["notes"], 4))
            return lines


    # Recipe: pretty_logging (0.1) in C:\trentm\tm\recipes\cookbook
    class _PerLevelFormatter(logging.Formatter):
        """Allow multiple format string -- depending on the log level.
        
        A "fmtFromLevel" optional arg is added to the constructor. It can be
        a dictionary mapping a log record level to a format string. The
        usual "fmt" argument acts as the default.
        """
        def __init__(self, fmt=None, datefmt=None, fmtFromLevel=None):
            logging.Formatter.__init__(self, fmt, datefmt)
            if fmtFromLevel is None:
                self.fmtFromLevel = {}
            else:
                self.fmtFromLevel = fmtFromLevel
        def format(self, record):
            record.levelname = record.levelname.lower()
            if record.levelno in self.fmtFromLevel:
                #XXX This is a non-threadsafe HACK. Really the base Formatter
                #    class should provide a hook accessor for the _fmt
                #    attribute. *Could* add a lock guard here (overkill?).
                _saved_fmt = self._fmt
                self._fmt = self.fmtFromLevel[record.levelno]
                try:
                    return logging.Formatter.format(self, record)
                finally:
                    self._fmt = _saved_fmt
            else:
                return logging.Formatter.format(self, record)

    def _setup_logging():
        hdlr = logging.StreamHandler()
        defaultFmt = "%(name)s: %(levelname)s: %(message)s"
        infoFmt = "%(name)s: %(message)s"
        fmtr = _PerLevelFormatter(fmt=defaultFmt,
                                  fmtFromLevel={logging.INFO: infoFmt})
        hdlr.setFormatter(fmtr)
        logging.root.addHandler(hdlr)
        log.setLevel(logging.INFO)



    _setup_logging() # defined in recipe:pretty_logging

    try:
        shell = Shell()
        optparser = cmdln.CmdlnOptionParser(shell,
            version=Shell.name+" "+__version__)
        optparser.add_option("-v", "--verbose", action="callback",
            callback=lambda opt, o, v, p: log.setLevel(logging.DEBUG),
            help="more verbose output")
        optparser.add_option("-q", "--quiet", action="callback",
            callback=lambda opt, o, v, p: log.setLevel(logging.WARNING),
            help="quieter output")
        optparser.add_option("-R", "--raw", action="store_const",
            dest="output_format", const="raw",
            help="print the raw (Python dict) response as from `ThirtyBoxes`")
        optparser.add_option("-s", "--short", action="store_const",
            dest="output_format", const="short",
            help="print the short response (single line per item)")
        optparser.add_option("-k", "--api-key", 
            help="specify your API key")
        optparser.add_option("-a", "--auth-token", 
            help="specify your authorized user token")
        optparser.set_defaults(api_key=None, auth_token=None,
                               output_format="long")
        retval = shell.main(sys.argv, optparser=optparser)
    except KeyboardInterrupt:
        sys.exit(1)
    except:
        exc_info = sys.exc_info()
        if hasattr(exc_info[0], "__name__"):
            log.error("%s", exc_info[1])
        else:  # string exception
            log.error(exc_info[0])
        if log.isEnabledFor(logging.DEBUG):
            import traceback
            print
            traceback.print_exception(*exc_info)
        sys.exit(1)
    else:
        sys.exit(retval)


# if __name__ == "__main__":
#     import sys, pprint
#     import thirtyboxes
#     sys.displayhook = pprint.pprint  # make big dicts look nice
#     tb = thirtyboxes.ThirtyBoxes()
#     tb.ping()
#     tb.find_user(34663)
