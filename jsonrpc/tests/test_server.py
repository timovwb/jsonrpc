# -*- coding: utf-8 -*-


import urllib2
import unittest

import jsonrpc.jsonutil


PORT = 8007
URL = "http://localhost:%s/jsonrpc" % PORT


def send_json(url, data):
    respdata = urllib2.urlopen(url, data).read()
    result = jsonrpc.jsonutil.decode(respdata)
    return result


class TestJSONRPCServer(unittest.TestCase):
    def setUp(self):
        self.id_ = 'an_id'
        self.param = "some data"
        self.batchcall_data = (
            '[{"jsonrpc": "2.0", "params": [1, 2], "method": "add", "id": "1"},'
             '{"jsonrpc": "2.0", "params": {"a": 3, "b": 2}, "method": "add", "id": "2"}]'
        )
        self.batchcallerr_data = (
            '[{"jsonrpc": "2.0", "params": [1, 2], "method": "add", "id": "1"},'
             '{"jsonrpc": "2.0", "params": {"a": "3", "b": 2}, "method": "add", "id": "2"}]'
        )

    def test_requestid0(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": "echo", "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode([self.param]), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result["id"], self.id_)

    def test_requestid1(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": "echo", "id": 1}' % 
                            jsonrpc.jsonutil.encode([self.param]))
        result = send_json(URL, data)
        self.assertEqual(result["id"], 1)

    def test_requestid2(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": "echo", "id": []}' % 
                            jsonrpc.jsonutil.encode([self.param]))
        result = send_json(URL, data)
        self.assertNotEqual(result["id"], [])

    def test_requestid3(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": "echo", "id": {}}' % 
                            jsonrpc.jsonutil.encode([self.param]))
        result = send_json(URL, data)
        self.assertNotEqual(result["id"], {})

    def test_invalid_data(self):
        data = ' {"v": %s}, "method": "echo"}' % jsonrpc.jsonutil.encode(self.param)
        result = send_json(URL, data)
        self.assertEqual(result, {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error."}, "id": None})

    def test_wrongversion(self):
        data = ('{"jsonrpc": "2.1", "params": %s, "method": "echo", "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode([self.param]), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result, {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request."}, "id": self.id_})

    def test_invalidmethodname(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": 0, "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode([self.param]), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result, {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request."}, "id": self.id_})

    def test_missingmethod(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": "non_existent", "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode([self.param]), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result, {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Procedure not found."}, "id": self.id_})

    def test_simplecall(self):
        data = ('{"jsonrpc": "2.0", "params": %s, "method": "echo", "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode([self.param]), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result['id'], self.id_)
        self.assertEqual(result['result'], self.param)

    def test_notify(self):
        #XXX: Modified from original
        data = ('{"jsonrpc": "2.0", "params": {"v": %s}, "method": "echo", "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode(self.param), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result['result'], self.param)

    def test_kwcall(self):
        data = ('{"jsonrpc": "2.0", "params": {"v": %s}, "method": "echo", "id": "%s"}' % 
                            (jsonrpc.jsonutil.encode(self.param), self.id_))
        result = send_json(URL, data)
        self.assertEqual(result['id'], self.id_)
        self.assertEqual(result['result'], self.param)

    def test_err(self):
        data = ('{"jsonrpc": "2.0", "params": [1, "sss"], "method": "add", "id": "%s"}' % 
                            self.id_)
        result = send_json(URL, data)
        self.assertEqual(result['id'], self.id_)
        self.assertTrue(result.get('error', False))

    def test_batchcall1(self):
        #XXX: Modified from original
        result = send_json(URL, self.batchcall_data)
        self.assertTrue(isinstance(result, list))

    def test_batchcall2(self):
        result = send_json(URL, self.batchcall_data)
        self.assertEqual(len(result), 2)

    def test_batchcall3(self):
        result = send_json(URL, self.batchcall_data)
        self.assertEqual(set(x['result'] for x in result), set([3,5]))

    def test_batchcall4(self):
        result = send_json(URL, self.batchcall_data)
        self.assertEqual(set(x['id'] for x in result), set("12"))

    def test_batchcall5(self):
        result = send_json(URL, self.batchcall_data)
        self.assertFalse(any(x.get('error', False) for x in result))

    def test_batchcall_1err_1(self):
        #XXX: Modified from original
        result = send_json(URL, self.batchcallerr_data)
        self.assertTrue(isinstance(result, list))

    def test_batchcall_1err_2(self):
        result = send_json(URL, self.batchcallerr_data)
        self.assertEqual(len(result), 2)

    def test_batchcall_1err_3(self):
        result = send_json(URL, self.batchcallerr_data)
        self.assertEqual(set(x['id'] for x in result), set("12"))

    def test_batchcall_1err_4(self):
        result = send_json(URL, self.batchcallerr_data)
        self.assertEqual(set(x.get('result', False) for x in result), set([3,False]))

    def test_batchcall_1err_5(self):
        result = send_json(URL, self.batchcallerr_data)
        self.assertEqual(len(filter(None, [x.get('error') for x in result])), 1)

    def test_batchcall_emptylist(self):
        data = '[]'
        result = send_json(URL, data)
        self.assertEqual(result, {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request."}, "id": None})

