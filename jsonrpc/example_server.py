#
#  Copyright (c) 2011 Edward Langley
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#  Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
#
#  Redistributions in binary form must reproduce the above copyright
#  notice, this list of conditions and the following disclaimer in the
#  documentation and/or other materials provided with the distribution.
#
#  Neither the name of the project's author nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#  TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#

from socketserver import ThreadingMixIn
from http.server import HTTPServer

from jsonrpc.server import ServerEvents, JSON_RPC


class ExampleServer(ServerEvents):
    # inherited hooks
    def log(self, responses, request, error):
        if isinstance(responses, list):
            for response in responses:
                msg = self._get_msg(response)
                print(request, msg)
        else:
            msg = self._get_msg(responses)
            print(request, msg)

    def findmethod(self, method, args=None, kwargs=None):
        if method in self.methods:
            return getattr(self, method)
        else:
            return None

    # helper methods
    methods = set(['add', 'subtract', 'echo'])

    def _get_msg(self, response):
        return ' '.join(str(x) for x in
                            [response.id, response.result or response.error])

    def subtract(self, a, b):
        return a - b

    def add(self, a, b):
        return a + b

    def echo(self, v):
        return v


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


handler = JSON_RPC.customize(ExampleServer)

# 8007 is the port you want to run under. Choose something >1024
PORT = 8007
print('Listening on port %d...' % PORT)
httpd = ThreadedHTTPServer(('', PORT), handler)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    httpd.server_close()
