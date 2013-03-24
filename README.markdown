A JSON-RPC 2.0 implementation for Python 3


## Getting Started
### Installing the librarary:

    % python setup.py install

  Alternatively, one can use the following commands from the directory which contains the 'setup.py' file.

### Start the Server:

    % python -m jsonrpc.example_server
    Listening on port 8007...

### Start the Client:
  
  `python -i -m jsonrpc <host name>`

  Example: `python -i -m jsonrpc http://localhost:8007`


    >>> server.add(1, 2)
    3

    >>> server.subtract(3,2)
    1

    # Exceptions
    >>> server.add(1, '2')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "jsonrpc/proxy.py", line 197, in __call__
        return resp.get_result()
      File "jsonrpc/common.py", line 190, in get_result
        raise codemap.get(code, RPCError).from_dict(self.error)
    jsonrpc.common.RPCError: {"message": "unsupported operand type(s) for +: 'int' and 'unicode'", "code": 0}


    >>> server.batch_call( dict(add=( (1,2), {} ), subtract=( (3,2), {} )) )
    [(3, None), (1, None)] # the pattern is (result, error)

    # batch calls can also be done with an iterable, if you want
    # to have more than one call to the same method
    >>> server.batch_call( [('add', ((1, 2), {})), ('subtract', ((3, 2), {}))] )
    [(3, None), (1, None)]

    # Exceptions in batch calls
    >>> server.batch_call( dict(add=( (1,2), {} ), subtract=( (3,'2'), {} )) )
    [(3, None), (None, {u'message': u"unsupported operand type(s) for -: 'int' 
      and 'unicode'", u'code': 0, u'data': [u"unsupported operand type(s) for -: 
      'int' and 'unicode'"]})]



Made for:
    http://ncmi.bcm.edu
