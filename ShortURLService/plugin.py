###
# Copyright (c) 2011, Florian Besser
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import os
import string
import supybot.utils as utils
import supybot.conf as conf
from supybot.commands import *
import supybot.plugins as plugins
import supybot.conf as conf
import supybot.world as world
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.httpserver as httpserver
from supybot.i18n import PluginInternationalization, internationalizeDocstring

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3 # for python2.4


_ = PluginInternationalization('ShortURLService')


# those to function I got from urlserver.py (weechat script) by FlashCode
def base62_encode(number):
    """Encode a number in base62 (all digits + a-z + A-Z)."""
    base62chars = string.digits + string.letters
    l = []
    while number > 0:
        remainder = number % 62
        number = number // 62
        l.insert(0, base62chars[remainder])
    return ''.join(l) or '0'

def base62_decode(str_value):
    """Decode a base62 string (all digits + a-z + A-Z) to a number."""
    base62chars = string.digits + string.letters
    return sum([base62chars.index(char) * (62 ** (len(str_value) - index - 1)) for index, char in enumerate(str_value)])

class ShortURLServiceCallback(httpserver.SupyHTTPServerCallback):
    name = 'ShortURLService'
    defaultResponse = """
    This plugin handles only GET request, please don't use other requests."""

    def doGet(self, handler, path):

        try:
            if path == "/":
                response = 200
                content_type = 'text/html'
                output = '<p> This is the ShortURLService Plugin for Supybot/Limnoira </p>'
            
            elif len(path) < 13:
                response = 200
                content_type = 'text/html'
                number = int(base62_decode(path.lstrip('/')))
                #output = "HAAALOOOOOOOOOO"
                url = self.db.getURLbyID(number)
                #output = '<p> %s' % url
                output = '<meta http-equiv="refresh" content="0; url=%s">' % url
           
           else:
                response = 404
                content_type ='text/html'
                output = '<h2> Error:404 </h2><p>No such Page</p>'
        
        except FooException, e:
            response = 500
            content_type = 'text/html'
            if output == '':
                output = '<h1>Internal server error</h1>'
        
        finally:
            self.send_response(response)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(output)
        

class ShortURLServiceDB:
    def __init__(self):
        filename = conf.supybot.directories.data.dirize('ShortURLService.db')
        alreadyExists = os.path.exists(filename)
        #if alreadyExists and testing:
        #    os.remove(filename)
        #    alreadyExists = False
        self._conn = sqlite3.connect(filename, check_same_thread = False)
        self._conn.text_factory = str
        if not alreadyExists:
            self.makeDb()

    def makeDb(self):
        """Create the tables in the database"""
        cursor = self._conn.cursor()
        cursor.execute("""CREATE TABLE shorturl(
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          chan TEXT,
                          url TEXT
                          )""")
        self._conn.commit()
        cursor.close()
    def getURLbyID(self, number):
        cursor = self._conn.cursor()
        cursor.execute("SELECT url FROM shorturl WHERE id=?", (number,))
        url = cursor.fetchone()
        cursor.close()
        return url

    def getURLsChan(self, channel):
        pass

    def writeURL(self, channel, url):
        cursor = self._conn.cursor()
        cursor.execute("INSERT INTO shorturl VALUES(NULL,?,?)", (channel,url))
        cursor.execute("select last_insert_rowid()")
        number = cursor.fetchone()
        cursor.close()
        self._conn.commit()
        return int(number[0])

    def delURL(self, number):
        pass



@internationalizeDocstring
class ShortURLService(callbacks.Plugin):
    """Add the help for "@plugin help ShortURLService" here
    This should describe *how* to use this plugin."""
    def __init__(self, irc):
        self.__parent = super(ShortURLService, self)
        callbacks.Plugin.__init__(self, irc)
        self.db = ShortURLServiceDB()

        callback = ShortURLServiceCallback()
        callback.plugin = self
        callback.db = self.db
        httpserver.hook('S', callback)
    def short(self, irc, msg, args , url):
        """ <URL>
        Makes a short URL from the given <URL>
        """

        number = self.db.writeURL('mirja', url)
        shorturl = "http://%s/%s" % (conf.supybot.plugins.ShortURLService.baseurl, base62_encode(number))
        irc.reply(shorturl)
    short = wrap(short, ['httpUrl'])


Class = ShortURLService


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
