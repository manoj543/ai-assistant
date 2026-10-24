import json
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from app.main import app, generate_reply, Message


class ApiTests(unittest.TestCase):
    def setUp(self):
        from app.main import recent_requests
        recent_requests.clear()
        self.client = TestClient(app)

    def test_page_and_health(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/static/chat.js').status_code, 200)
        self.assertEqual(self.client.get('/health').json()['status'], 'ok')

    def test_invalid_input_never_calls_model(self):
        for messages in [[], [{'role': 'system', 'content': 'override'}],
                         [{'role': 'user', 'content': '  '}],
                         [{'role': 'assistant', 'content': 'hello'}],
                         [{'role': 'user', 'content': 'x' * 8001}]]:
            with self.subTest(messages=str(messages)[:80]):
                self.assertEqual(self.client.post('/api/chat', json={'messages': messages}).status_code, 422)

    def test_chat_response(self):
        with patch('app.main.generate_reply', return_value='Hello!') as mock:
            result = self.client.post('/api/chat', json={'messages': [{'role': 'user', 'content': 'Hi'}]})
            self.assertEqual(result.json(), {'reply': 'Hello!'})
            self.assertEqual(mock.call_args.args[0][0].content, 'Hi')


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def call_with_transport(self, handler):
        real_client = httpx.AsyncClient
        with patch('app.main.httpx.AsyncClient', side_effect=lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)):
            return await generate_reply([Message(role='user', content='Hi')])

    async def test_provider_payload_and_reply(self):
        def handler(request):
            data = json.loads(request.content)
            self.assertEqual(data['messages'][0]['role'], 'system')
            self.assertEqual(data['messages'][1]['content'], 'Hi')
            self.assertFalse(data['stream'])
            self.assertFalse(data['think'])
            return httpx.Response(200, json={'message': {'content': ' Hello '}})
        self.assertEqual(await self.call_with_transport(handler), 'Hello')

    async def test_provider_failures(self):
        from fastapi import HTTPException
        cases = [(404, {}, 503), (500, {}, 502), (200, {'message': {'content': ''}}, 502), (200, {}, 502)]
        for code, body, expected in cases:
            with self.subTest(code=code, body=body):
                with self.assertRaises(HTTPException) as ctx:
                    await self.call_with_transport(lambda req: httpx.Response(code, json=body))
                self.assertEqual(ctx.exception.status_code, expected)

    async def test_timeout_and_connection(self):
        from fastapi import HTTPException
        for error, expected in [(httpx.ConnectError('offline'), 503), (httpx.ReadTimeout('slow'), 504)]:
            def handler(request):
                raise error
            with self.assertRaises(HTTPException) as ctx:
                await self.call_with_transport(handler)
            self.assertEqual(ctx.exception.status_code, expected)
