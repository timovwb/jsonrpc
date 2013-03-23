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

import jsonrpc.jsonutil
from jsonrpc.utilities import public
import jsonrpc.common

from BaseHTTPServer import BaseHTTPRequestHandler

import copy
import UserDict, collections
collections.Mapping.register(UserDict.DictMixin)


@public
class ServerEvents(object):
    '''Subclass this and pass to :py:meth:`JSON_RPC.customize` to customize
    the JSON-RPC server.
    '''

    DEBUG = False

    #: an object defining a 'get' method which contains the methods
    methods = None

    def __init__(self, server):
        #: A link to the JSON-RPC server instance
        self.server = server

    def callmethod(self, rpcrequest, **extra):
        '''Find the method and call it with the specified args

        :returns: the result of the method
        '''

        extra.update(rpcrequest.kwargs)

        method = self.findmethod(rpcrequest.method, rpcrequest.args, extra)
        postprocess_result = False
        if hasattr('method', '__iter__'):
            method, postprocess_result = method

        if self.DEBUG:
            # Debugging: raise AssertionError if type of method is invalid
            assert method is None or callable(method),\
                            'the returned method is not callable'

        if not callable(method):
            raise jsonrpc.common.MethodNotFound

        result = method(*rpcrequest.args, **extra)

        #if the result needs to be adjusted/validated, do it
        if postprocess_result:
            result = self.methods.postprocess(rpcrequest.method, result,
                                              rpcrequest.args, extra)

        return result

    def findmethod(self, method_name, args=None, kwargs=None):
        '''Return the callable associated with the method name

        :returns: a callable or None if the method is not found
        '''

        if self.methods is not None:
            return self.methods.get(method_name)
        else:
            raise NotImplementedError

    def processrequest(self, result, **kw):
        '''Override to implement custom handling of the method result and request'''

        return result

    def log(self, response, txrequest, error=False):
        '''Override to implement custom logging'''

        pass

    def processcontent(self, content):
        '''Given the freshly decoded content of the request, return the content
        that should be used.

        :returns: an object which implements the
                  :py:class:`collections.MutableMapping` interface
        '''

        return content

    def getresponsecode(self, result):
        '''Take the result, and return an appropriate HTTP response code,
        returns 200 by default.

        NOTE: if an error code is returned, the client error messages will be
              much less helpful!

        for example

            def getresponsecode(self, result):
                code = 200
                if not isinstance(result, list):
                    if result is not None and result.error is not None:
                        code = result.error.code or 500
                return code


        :returns: :py:class:`int`
        '''

        # returns 200 so that the python client can see something useful
        return 200


## Base class providing a JSON-RPC 2.0 implementation with 2 customizable hooks
@public
class JSON_RPC(BaseHTTPRequestHandler):
    '''This class implements a JSON-RPC 2.0 server'''

    ### NOTE: these comments are used by Sphinx as documentation.
    #: An instance of :py:class:`ServerEvents` which supplies callbacks to
    #: customize the operation of the server.  The proper way to initialize this
    #: is either to subclass and set it manually, or, preferably, to call
    #: :py:meth:`customize`.
    eventhandler = ServerEvents

    @classmethod
    def customize(cls, eventhandler):
        '''customize the behavior of the server'''

        cls.eventhandler = eventhandler(cls)
        return cls

    def log_request(self, code, size=None):
        '''Overriden method from BaseHTTPRequestHandler to reduce logmessages'''

    def do_POST(self):
        self.request = "<{0} {1} {2}>".format(self.command, self.path,
                                                    self.request_version)
        result = []
        errors = False
        contents = None
        try:
            length = int(self.headers.getheader('content-length'))
            try:
                contents = jsonrpc.jsonutil.decode(self.rfile.read(length))
            except ValueError:
                raise jsonrpc.common.ParseError

            islist = (True if isinstance(contents, list) else False)
            if not islist:
                contents = [contents]

            if contents == []:
                raise jsonrpc.common.InvalidRequest

            contents = self.eventhandler.processcontent(contents)
            contents = jsonrpc.common.Request.from_json(contents)
            for item in contents:
                try:
                    item.check()
                except BaseException, exc:
                    # Save error and process other items when doing a batchcall
                    if islist:
                        exc = self.render_error(exc, item.id)
                        result.append(exc)
                        errors = True
                        continue
                    # Let the top handler catch this on a single call
                    raise

            def callmethod(rpcrequest, add, **kwargs):
                add.update(kwargs)
                result = self.eventhandler.callmethod(rpcrequest, **add)
                return result

            for rpcrequest in contents:
                try:
                    add = copy.deepcopy(rpcrequest.extra)
                    methodresult = callmethod(rpcrequest, add)
                    res = jsonrpc.common.Response(id=rpcrequest.id,
                                                  result=methodresult)
                    res = self.eventhandler.processrequest(res)
                    if res.id is not None:
                        result.append(res)
                except BaseException, exc:
                    err = self.render_error(exc, rpcrequest.id)
                    result.append(err)
                    errors = True
                    continue

            if result != []:
                if not islist:
                    result = result[0]
            else:
                result = None
        except (BaseException, jsonrpc.common.RPCError), exc:
            if contents is None or contents == []:
                errid = None
            elif hasattr(contents, 'id'):
                errid = contents.id
            elif hasattr(contents[0], 'id'):
                errid = contents[0].id

            err = self.render_error(exc, errid)
            self.response(err, True)
        else:
            self.response(result, errors)

    def response(self, resp, error):
        code = self.eventhandler.getresponsecode(resp)
        self.send_response(code)
        self.eventhandler.log(resp, self.request, error=error)

        result = jsonrpc.jsonutil.encode(resp).encode('utf-8')
        self.send_header("content-type", 'application/json')
        self.send_header("content-length", len(result))
        self.end_headers()
        self.wfile.write(result)

    def render_error(self, e, id):
        err = (e if isinstance(e, jsonrpc.common.RPCError) else
                        dict(code=0, message=str(e), data=e.args))
        return jsonrpc.common.Response(id=id, error=err)
