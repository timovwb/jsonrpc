# -*- coding: utf-8 -*-


import json
import unittest

from jsonrpc import jsonutil


class testobj:
    value = 'This is the json value'
    def json_equivalent(self):
        return self.value


class TestJSONUTIL(unittest.TestCase):
    def setUp(self):
        # simple tests
        self.lis = [1,2,3]
        self.jlis = json.dumps(self.lis)
        self.int = 1
        self.jint = json.dumps(self.int)
        self.str = 'asdasd'
        self.jstr = json.dumps(self.str)
        self.none = None
        self.jnone = json.dumps(self.none)

        # more complicated tests
        self.obj1 = dict(a=1,b=2,c=3)
        self.jobj1 = json.dumps(self.obj1)
        self.obj2 = dict(a=[1,2,3],b={2:2,3:3,4:4},c=(3,4,5))
        self.jobj2 = json.dumps(self.obj2)

        # extended functionality
        self.obj3 = dict(a=set([1]),b=frozenset([2]),c=[1,2,3])
        self.obj3_roundtrip = dict( (k,list(v)) for k,v in self.obj3.items())

        self.obj4 = testobj()
        self.jobj4 = json.dumps(testobj.value)

    def test_encode(self):
        self.assertEqual(jsonutil.encode(self.lis), self.jlis)
        self.assertEqual(jsonutil.encode(self.int), self.jint)
        self.assertEqual(jsonutil.encode(self.str), self.jstr)
        self.assertEqual(jsonutil.encode(self.none), self.jnone)

        self.assertEqual(jsonutil.encode(self.obj1), self.jobj1)
        self.assertEqual(jsonutil.encode(self.obj2), self.jobj2)
        self.assertEqual(jsonutil.encode(self.obj4), self.jobj4)

    def test_decode(self):
        self.assertEqual(jsonutil.decode(self.jlis), self.lis)
        self.assertEqual(jsonutil.decode(self.jint), self.int)
        self.assertEqual(jsonutil.decode(self.jstr), self.str)
        self.assertEqual(jsonutil.decode(self.jnone), self.none)

        self.assertEqual(jsonutil.decode(self.jobj1), self.obj1)
        self.assertEqual(jsonutil.decode(self.jobj2), json.loads(self.jobj2))
        self.assertEqual(jsonutil.decode(self.jobj4), testobj.value)

    def test_roundtrip(self):
        self.assertEqual(jsonutil.decode(jsonutil.encode(self.lis)), self.lis)
        self.assertEqual(jsonutil.decode(jsonutil.encode(self.int)), self.int)
        self.assertEqual(jsonutil.decode(jsonutil.encode(self.str)), self.str)
        self.assertEqual(jsonutil.decode(jsonutil.encode(self.none)), self.none)

        ##TODO Py3k: set/frozenset issue
        ##self.assertEqual(jsonutil.decode(jsonutil.encode(self.obj3)), self.obj3_roundtrip)

