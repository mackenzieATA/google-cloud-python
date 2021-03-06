# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import mock


def _make_credentials():
    import google.auth.credentials
    return mock.Mock(spec=google.auth.credentials.Credentials)


class TestLogger(unittest.TestCase):

    PROJECT = 'test-project'
    LOGGER_NAME = 'logger-name'

    @staticmethod
    def _get_target_class():
        from google.cloud.logging.logger import Logger
        return Logger

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def test_ctor_defaults(self):
        conn = object()
        client = _Client(self.PROJECT, conn)
        logger = self._make_one(self.LOGGER_NAME, client=client)
        self.assertEqual(logger.name, self.LOGGER_NAME)
        self.assertIs(logger.client, client)
        self.assertEqual(logger.project, self.PROJECT)
        self.assertEqual(logger.full_name, 'projects/%s/logs/%s'
                         % (self.PROJECT, self.LOGGER_NAME))
        self.assertEqual(logger.path, '/projects/%s/logs/%s'
                         % (self.PROJECT, self.LOGGER_NAME))
        self.assertIsNone(logger.labels)

    def test_ctor_explicit(self):
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        conn = object()
        client = _Client(self.PROJECT, conn)
        logger = self._make_one(self.LOGGER_NAME, client=client, labels=LABELS)
        self.assertEqual(logger.name, self.LOGGER_NAME)
        self.assertIs(logger.client, client)
        self.assertEqual(logger.project, self.PROJECT)
        self.assertEqual(logger.full_name, 'projects/%s/logs/%s'
                         % (self.PROJECT, self.LOGGER_NAME))
        self.assertEqual(logger.path, '/projects/%s/logs/%s'
                         % (self.PROJECT, self.LOGGER_NAME))
        self.assertEqual(logger.labels, LABELS)

    def test_batch_w_bound_client(self):
        from google.cloud.logging.logger import Batch
        conn = object()
        client = _Client(self.PROJECT, conn)
        logger = self._make_one(self.LOGGER_NAME, client=client)
        batch = logger.batch()
        self.assertIsInstance(batch, Batch)
        self.assertIs(batch.logger, logger)
        self.assertIs(batch.client, client)

    def test_batch_w_alternate_client(self):
        from google.cloud.logging.logger import Batch
        conn1 = object()
        conn2 = object()
        client1 = _Client(self.PROJECT, conn1)
        client2 = _Client(self.PROJECT, conn2)
        logger = self._make_one(self.LOGGER_NAME, client=client1)
        batch = logger.batch(client2)
        self.assertIsInstance(batch, Batch)
        self.assertIs(batch.logger, logger)
        self.assertIs(batch.client, client2)

    def test_log_text_w_str_implicit_client(self):
        TEXT = 'TEXT'
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'textPayload': TEXT,
            'resource': {
                'type': 'global',
            },
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.log_text(TEXT)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_text_w_default_labels(self):
        TEXT = 'TEXT'
        DEFAULT_LABELS = {'foo': 'spam'}
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'textPayload': TEXT,
            'resource': {
                'type': 'global',
            },
            'labels': DEFAULT_LABELS,
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client,
                                labels=DEFAULT_LABELS)

        logger.log_text(TEXT)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_text_w_timestamp(self):
        import datetime

        TEXT = 'TEXT'
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'textPayload': TEXT,
            'timestamp': '2016-12-31T00:01:02.999999Z',
            'resource': {
                'type': 'global',
            },
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.log_text(TEXT, timestamp=TIMESTAMP)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_text_w_unicode_explicit_client_labels_severity_httpreq(self):
        TEXT = u'TEXT'
        DEFAULT_LABELS = {'foo': 'spam'}
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'textPayload': TEXT,
            'resource': {
                'type': 'global',
            },
            'labels': LABELS,
            'insertId': IID,
            'severity': SEVERITY,
            'httpRequest': REQUEST,
        }]
        client1 = _Client(self.PROJECT)
        client2 = _Client(self.PROJECT)
        api = client2.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client1,
                                labels=DEFAULT_LABELS)

        logger.log_text(TEXT, client=client2, labels=LABELS,
                        insert_id=IID, severity=SEVERITY, http_request=REQUEST)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_struct_w_implicit_client(self):
        STRUCT = {'message': 'MESSAGE', 'weather': 'cloudy'}
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'jsonPayload': STRUCT,
            'resource': {
                'type': 'global',
            },
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.log_struct(STRUCT)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_struct_w_default_labels(self):
        STRUCT = {'message': 'MESSAGE', 'weather': 'cloudy'}
        DEFAULT_LABELS = {'foo': 'spam'}
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'jsonPayload': STRUCT,
            'resource': {
                'type': 'global',
            },
            'labels': DEFAULT_LABELS,
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client,
                                labels=DEFAULT_LABELS)

        logger.log_struct(STRUCT)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_struct_w_explicit_client_labels_severity_httpreq(self):
        STRUCT = {'message': 'MESSAGE', 'weather': 'cloudy'}
        DEFAULT_LABELS = {'foo': 'spam'}
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'jsonPayload': STRUCT,
            'resource': {
                'type': 'global',
            },
            'labels': LABELS,
            'insertId': IID,
            'severity': SEVERITY,
            'httpRequest': REQUEST,
        }]
        client1 = _Client(self.PROJECT)
        client2 = _Client(self.PROJECT)
        api = client2.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client1,
                                labels=DEFAULT_LABELS)

        logger.log_struct(STRUCT, client=client2, labels=LABELS,
                          insert_id=IID, severity=SEVERITY,
                          http_request=REQUEST)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_struct_w_timestamp(self):
        import datetime
        STRUCT = {'message': 'MESSAGE', 'weather': 'cloudy'}
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'jsonPayload': STRUCT,
            'timestamp': '2016-12-31T00:01:02.999999Z',
            'resource': {
                'type': 'global',
            },
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.log_struct(STRUCT, timestamp=TIMESTAMP)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_proto_w_implicit_client(self):
        import json
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        message = Struct(fields={'foo': Value(bool_value=True)})
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'protoPayload': json.loads(MessageToJson(message)),
            'resource': {
                'type': 'global',
            },
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.log_proto(message)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_proto_w_default_labels(self):
        import json
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        message = Struct(fields={'foo': Value(bool_value=True)})
        DEFAULT_LABELS = {'foo': 'spam'}
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'protoPayload': json.loads(MessageToJson(message)),
            'resource': {
                'type': 'global',
            },
            'labels': DEFAULT_LABELS,
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client,
                                labels=DEFAULT_LABELS)

        logger.log_proto(message)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_proto_w_explicit_client_labels_severity_httpreq(self):
        import json
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        message = Struct(fields={'foo': Value(bool_value=True)})
        DEFAULT_LABELS = {'foo': 'spam'}
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'protoPayload': json.loads(MessageToJson(message)),
            'resource': {
                'type': 'global',
            },
            'labels': LABELS,
            'insertId': IID,
            'severity': SEVERITY,
            'httpRequest': REQUEST,
        }]
        client1 = _Client(self.PROJECT)
        client2 = _Client(self.PROJECT)
        api = client2.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client1,
                                labels=DEFAULT_LABELS)

        logger.log_proto(message, client=client2, labels=LABELS,
                         insert_id=IID, severity=SEVERITY,
                         http_request=REQUEST)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_log_proto_w_timestamp(self):
        import json
        import datetime
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        message = Struct(fields={'foo': Value(bool_value=True)})
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        ENTRIES = [{
            'logName': 'projects/%s/logs/%s' % (
                self.PROJECT, self.LOGGER_NAME),
            'protoPayload': json.loads(MessageToJson(message)),
            'timestamp': '2016-12-31T00:01:02.999999Z',
            'resource': {
                'type': 'global',
            },
        }]
        client = _Client(self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.log_proto(message, timestamp=TIMESTAMP)

        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, None, None, None))

    def test_delete_w_bound_client(self):
        client = _Client(project=self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client)

        logger.delete()

        self.assertEqual(api._logger_delete_called_with,
                         (self.PROJECT, self.LOGGER_NAME))

    def test_delete_w_alternate_client(self):
        client1 = _Client(project=self.PROJECT)
        client2 = _Client(project=self.PROJECT)
        api = client2.logging_api = _DummyLoggingAPI()
        logger = self._make_one(self.LOGGER_NAME, client=client1)

        logger.delete(client=client2)

        self.assertEqual(api._logger_delete_called_with,
                         (self.PROJECT, self.LOGGER_NAME))

    def test_list_entries_defaults(self):
        import six
        from google.cloud.logging.client import Client

        TOKEN = 'TOKEN'

        client = Client(project=self.PROJECT,
                        credentials=_make_credentials(),
                        use_gax=False)
        returned = {
            'nextPageToken': TOKEN,
        }
        client._connection = _Connection(returned)

        logger = self._make_one(self.LOGGER_NAME, client=client)

        iterator = logger.list_entries()
        page = six.next(iterator.pages)
        entries = list(page)
        token = iterator.next_page_token

        self.assertEqual(len(entries), 0)
        self.assertEqual(token, TOKEN)
        called_with = client._connection._called_with
        FILTER = 'logName=projects/%s/logs/%s' % (
            self.PROJECT, self.LOGGER_NAME)
        self.assertEqual(called_with, {
            'method': 'POST',
            'path': '/entries:list',
            'data': {
                'filter': FILTER,
                'projectIds': [self.PROJECT],
            },
        })

    def test_list_entries_explicit(self):
        from google.cloud.logging import DESCENDING
        from google.cloud.logging.client import Client

        PROJECT1 = 'PROJECT1'
        PROJECT2 = 'PROJECT2'
        FILTER = 'resource.type:global'
        TOKEN = 'TOKEN'
        PAGE_SIZE = 42
        client = Client(project=self.PROJECT,
                        credentials=_make_credentials(),
                        use_gax=False)
        client._connection = _Connection({})
        logger = self._make_one(self.LOGGER_NAME, client=client)
        iterator = logger.list_entries(
            projects=[PROJECT1, PROJECT2], filter_=FILTER, order_by=DESCENDING,
            page_size=PAGE_SIZE, page_token=TOKEN)
        entries = list(iterator)
        token = iterator.next_page_token

        self.assertEqual(len(entries), 0)
        self.assertIsNone(token)
        # self.assertEqual(client._listed, LISTED)
        called_with = client._connection._called_with
        combined_filter = '%s AND logName=projects/%s/logs/%s' % (
            FILTER, self.PROJECT, self.LOGGER_NAME)
        self.assertEqual(called_with, {
            'method': 'POST',
            'path': '/entries:list',
            'data': {
                'filter': combined_filter,
                'orderBy': DESCENDING,
                'pageSize': PAGE_SIZE,
                'pageToken': TOKEN,
                'projectIds': [PROJECT1, PROJECT2],
            },
        })


class TestBatch(unittest.TestCase):

    PROJECT = 'test-project'

    @staticmethod
    def _get_target_class():
        from google.cloud.logging.logger import Batch
        return Batch

    def _make_one(self, *args, **kwargs):
        return self._get_target_class()(*args, **kwargs)

    def test_ctor_defaults(self):
        logger = _Logger()
        client = _Client(project=self.PROJECT)
        batch = self._make_one(logger, client)
        self.assertIs(batch.logger, logger)
        self.assertIs(batch.client, client)
        self.assertEqual(len(batch.entries), 0)

    def test_log_text_defaults(self):
        TEXT = 'This is the entry text'
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        logger = _Logger()
        batch = self._make_one(logger, client=client)
        batch.log_text(TEXT)
        self.assertEqual(batch.entries,
                         [('text', TEXT, None, None, None, None, None)])

    def test_log_text_explicit(self):
        import datetime
        TEXT = 'This is the entry text'
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        logger = _Logger()
        batch = self._make_one(logger, client=client)
        batch.log_text(TEXT, labels=LABELS, insert_id=IID, severity=SEVERITY,
                       http_request=REQUEST, timestamp=TIMESTAMP)
        self.assertEqual(
            batch.entries,
            [('text', TEXT, LABELS, IID, SEVERITY, REQUEST, TIMESTAMP)])

    def test_log_struct_defaults(self):
        STRUCT = {'message': 'Message text', 'weather': 'partly cloudy'}
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        logger = _Logger()
        batch = self._make_one(logger, client=client)
        batch.log_struct(STRUCT)
        self.assertEqual(
            batch.entries,
            [('struct', STRUCT, None, None, None, None, None)])

    def test_log_struct_explicit(self):
        import datetime
        STRUCT = {'message': 'Message text', 'weather': 'partly cloudy'}
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        logger = _Logger()
        batch = self._make_one(logger, client=client)
        batch.log_struct(STRUCT, labels=LABELS, insert_id=IID,
                         severity=SEVERITY, http_request=REQUEST,
                         timestamp=TIMESTAMP)
        self.assertEqual(
            batch.entries,
            [('struct', STRUCT, LABELS, IID, SEVERITY, REQUEST, TIMESTAMP)])

    def test_log_proto_defaults(self):
        from google.protobuf.struct_pb2 import Struct, Value
        message = Struct(fields={'foo': Value(bool_value=True)})
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        logger = _Logger()
        batch = self._make_one(logger, client=client)
        batch.log_proto(message)
        self.assertEqual(batch.entries,
                         [('proto', message, None, None, None, None, None)])

    def test_log_proto_explicit(self):
        import datetime
        from google.protobuf.struct_pb2 import Struct, Value
        message = Struct(fields={'foo': Value(bool_value=True)})
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        logger = _Logger()
        batch = self._make_one(logger, client=client)
        batch.log_proto(message, labels=LABELS, insert_id=IID,
                        severity=SEVERITY, http_request=REQUEST,
                        timestamp=TIMESTAMP)
        self.assertEqual(
            batch.entries,
            [('proto', message, LABELS, IID, SEVERITY, REQUEST, TIMESTAMP)])

    def test_commit_w_invalid_entry_type(self):
        logger = _Logger()
        client = _Client(project=self.PROJECT, connection=_make_credentials())
        batch = self._make_one(logger, client)
        batch.entries.append(('bogus', 'BOGUS', None, None, None, None, None))
        with self.assertRaises(ValueError):
            batch.commit()

    def test_commit_w_bound_client(self):
        import json
        import datetime
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        TEXT = 'This is the entry text'
        STRUCT = {'message': TEXT, 'weather': 'partly cloudy'}
        message = Struct(fields={'foo': Value(bool_value=True)})
        IID1 = 'IID1'
        IID2 = 'IID2'
        IID3 = 'IID3'
        TIMESTAMP1 = datetime.datetime(2016, 12, 31, 0, 0, 1, 999999)
        TIMESTAMP2 = datetime.datetime(2016, 12, 31, 0, 0, 2, 999999)
        TIMESTAMP3 = datetime.datetime(2016, 12, 31, 0, 0, 3, 999999)
        RESOURCE = {
            'type': 'global',
        }
        ENTRIES = [
            {'textPayload': TEXT, 'insertId': IID1, 'timestamp': TIMESTAMP1},
            {'jsonPayload': STRUCT, 'insertId': IID2, 'timestamp': TIMESTAMP2},
            {'protoPayload': json.loads(MessageToJson(message)),
             'insertId': IID3, 'timestamp': TIMESTAMP3},
        ]
        client = _Client(project=self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = _Logger()
        batch = self._make_one(logger, client=client)

        batch.log_text(TEXT, insert_id=IID1, timestamp=TIMESTAMP1)
        batch.log_struct(STRUCT, insert_id=IID2, timestamp=TIMESTAMP2)
        batch.log_proto(message, insert_id=IID3, timestamp=TIMESTAMP3)
        batch.commit()

        self.assertEqual(list(batch.entries), [])
        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, logger.full_name, RESOURCE, None))

    def test_commit_w_alternate_client(self):
        import json
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        from google.cloud.logging.logger import Logger
        TEXT = 'This is the entry text'
        STRUCT = {'message': TEXT, 'weather': 'partly cloudy'}
        message = Struct(fields={'foo': Value(bool_value=True)})
        DEFAULT_LABELS = {'foo': 'spam'}
        LABELS = {
            'foo': 'bar',
            'baz': 'qux',
        }
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        client1 = _Client(project=self.PROJECT)
        client2 = _Client(project=self.PROJECT)
        api = client2.logging_api = _DummyLoggingAPI()
        logger = Logger('logger_name', client1, labels=DEFAULT_LABELS)
        RESOURCE = {'type': 'global'}
        ENTRIES = [
            {'textPayload': TEXT, 'labels': LABELS},
            {'jsonPayload': STRUCT, 'severity': SEVERITY},
            {'protoPayload': json.loads(MessageToJson(message)),
             'httpRequest': REQUEST},
        ]
        batch = self._make_one(logger, client=client1)

        batch.log_text(TEXT, labels=LABELS)
        batch.log_struct(STRUCT, severity=SEVERITY)
        batch.log_proto(message, http_request=REQUEST)
        batch.commit(client=client2)

        self.assertEqual(list(batch.entries), [])
        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, logger.full_name, RESOURCE, DEFAULT_LABELS))

    def test_context_mgr_success(self):
        import json
        from google.protobuf.json_format import MessageToJson
        from google.protobuf.struct_pb2 import Struct, Value
        from google.cloud.logging.logger import Logger
        TEXT = 'This is the entry text'
        STRUCT = {'message': TEXT, 'weather': 'partly cloudy'}
        message = Struct(fields={'foo': Value(bool_value=True)})
        DEFAULT_LABELS = {'foo': 'spam'}
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        client = _Client(project=self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = Logger('logger_name', client, labels=DEFAULT_LABELS)
        RESOURCE = {
            'type': 'global',
        }
        ENTRIES = [
            {'textPayload': TEXT, 'httpRequest': REQUEST},
            {'jsonPayload': STRUCT, 'labels': LABELS},
            {'protoPayload': json.loads(MessageToJson(message)),
             'severity': SEVERITY},
        ]
        batch = self._make_one(logger, client=client)

        with batch as other:
            other.log_text(TEXT, http_request=REQUEST)
            other.log_struct(STRUCT, labels=LABELS)
            other.log_proto(message, severity=SEVERITY)

        self.assertEqual(list(batch.entries), [])
        self.assertEqual(api._write_entries_called_with,
                         (ENTRIES, logger.full_name, RESOURCE, DEFAULT_LABELS))

    def test_context_mgr_failure(self):
        import datetime
        from google.protobuf.struct_pb2 import Struct, Value
        TEXT = 'This is the entry text'
        STRUCT = {'message': TEXT, 'weather': 'partly cloudy'}
        LABELS = {'foo': 'bar', 'baz': 'qux'}
        IID = 'IID'
        SEVERITY = 'CRITICAL'
        METHOD = 'POST'
        URI = 'https://api.example.com/endpoint'
        STATUS = '500'
        REQUEST = {
            'requestMethod': METHOD,
            'requestUrl': URI,
            'status': STATUS,
        }
        TIMESTAMP = datetime.datetime(2016, 12, 31, 0, 1, 2, 999999)
        message = Struct(fields={'foo': Value(bool_value=True)})
        client = _Client(project=self.PROJECT)
        api = client.logging_api = _DummyLoggingAPI()
        logger = _Logger()
        UNSENT = [
            ('text', TEXT, None, IID, None, None, TIMESTAMP),
            ('struct', STRUCT, None, None, SEVERITY, None, None),
            ('proto', message, LABELS, None, None, REQUEST, None),
        ]
        batch = self._make_one(logger, client=client)

        try:
            with batch as other:
                other.log_text(TEXT, insert_id=IID, timestamp=TIMESTAMP)
                other.log_struct(STRUCT, severity=SEVERITY)
                other.log_proto(message, labels=LABELS, http_request=REQUEST)
                raise _Bugout()
        except _Bugout:
            pass

        self.assertEqual(list(batch.entries), UNSENT)
        self.assertIsNone(api._write_entries_called_with)


class _Logger(object):

    labels = None

    def __init__(self, name='NAME', project='PROJECT'):
        self.full_name = 'projects/%s/logs/%s' % (project, name)


class _DummyLoggingAPI(object):

    _write_entries_called_with = None

    def write_entries(self, entries, logger_name=None, resource=None,
                      labels=None):
        self._write_entries_called_with = (
            entries, logger_name, resource, labels)

    def logger_delete(self, project, logger_name):
        self._logger_delete_called_with = (project, logger_name)


class _Client(object):

    def __init__(self, project, connection=None):
        self.project = project
        self._connection = connection


class _Bugout(Exception):
    pass


class _Connection(object):

    _called_with = None

    def __init__(self, *responses):
        self._responses = responses

    def api_request(self, **kw):
        self._called_with = kw
        response, self._responses = self._responses[0], self._responses[1:]
        return response
