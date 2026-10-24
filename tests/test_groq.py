import asyncio
import json
import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app import main
import test_chat


class GroqTests(test_chat.ProviderTests):
    async def asyncSetUp(self):
        self.provider = patch.multiple(main, PROVIDER='groq', GROQ_API_KEY='test-secret', MODEL='openai/gpt-oss-20b')
        self.provider.start()
        self.addCleanup(self.provider.stop)

    async def test_provider_payload_and_reply(self):
        def handler(request):
            self.assertEqual(str(request.url), 'https://api.groq.com/openai/v1/chat/completions')
            self.assertEqual(request.headers['Authorization'], 'Bearer test-secret')
            data = json.loads(request.content)
            self.assertEqual(data['messages'][0]['role'], 'system')
            self.assertEqual(data['model'], 'openai/gpt-oss-20b')
            self.assertNotIn('think', data)
            self.assertNotIn('options', data)
            self.assertEqual(data['max_completion_tokens'], 1024)
            return httpx.Response(200, json={'choices': [{'message': {'content': ' Hello ', 'reasoning': 'private'}}]})
        self.assertEqual(await self.call_with_transport(handler), 'Hello')

    async def test_provider_failures(self):
        for code, body, expected in [(429, {}, 429), (401, {'error': 'SECRET'}, 503),
                                     (403, {}, 503), (404, {}, 503), (500, {}, 502),
                                     (200, {'choices': []}, 502),
                                     (200, {'choices': [{'message': {'content': None}}]}, 502)]:
            with self.subTest(code=code, body=body):
                with self.assertRaises(HTTPException) as ctx:
                    await self.call_with_transport(lambda req: httpx.Response(code, json=body))
                self.assertEqual(ctx.exception.status_code, expected)
                self.assertNotIn('SECRET', ctx.exception.detail)


class HostingTests(unittest.TestCase):
    def setUp(self):
        main.recent_requests.clear()
        self.client = TestClient(main.app)

    def test_global_quota(self):
        with patch.object(main, 'REQUESTS_PER_MINUTE', 1), patch.object(main, 'generate_reply', return_value='Hello'):
            body = {'messages': [{'role': 'user', 'content': 'Hi'}]}
            self.assertEqual(self.client.post('/api/chat', json=body).status_code, 200)
            blocked = self.client.post('/api/chat', json=body)
            self.assertEqual(blocked.status_code, 429)
            self.assertEqual(blocked.headers['retry-after'], '60')
            self.assertEqual(self.client.get('/health').status_code, 200)

    def test_cors(self):
        from fastapi.middleware.cors import CORSMiddleware
        wrapped = TestClient(CORSMiddleware(main.app, allow_origins=['https://example.github.io'],
                                           allow_methods=['POST'], allow_headers=['Content-Type']))
        for origin, expected in [('https://example.github.io', 200), ('https://other.example', 400)]:
            response = wrapped.options('/api/chat', headers={'Origin': origin,
                'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
            self.assertEqual(response.status_code, expected)

    def test_busy_limit(self):
        with patch.object(main, 'model_slots', asyncio.Semaphore(0)), patch.object(main, 'generate_reply') as model:
            response = self.client.post('/api/chat', json={'messages': [{'role': 'user', 'content': 'Hi'}]})
            self.assertEqual(response.status_code, 503)
            model.assert_not_called()

    def test_static_config(self):
        self.assertEqual(self.client.get('/static/config.js').status_code, 200)
