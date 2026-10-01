import time
import unittest
from unittest.mock import patch

from wrapper_server import CAIWrapper, flatten_messages, openai_response


class WrapperServerTests(unittest.TestCase):
    def test_flatten_messages_preserves_roles_and_text_parts(self):
        text = flatten_messages([
            {"role": "system", "content": "Keep JSON."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Run this."},
                    {"type": "text", "text": "Return OK."},
                ],
            },
        ])
        self.assertIn("SYSTEM:\nKeep JSON.", text)
        self.assertIn("USER:\nRun this.\nReturn OK.", text)

    def test_openai_response_matches_chat_completion_shape(self):
        response = openai_response("pentestgpt-qwen3", "OK", time.monotonic())
        self.assertEqual(response["object"], "chat.completion")
        self.assertEqual(response["model"], "pentestgpt-qwen3")
        self.assertEqual(response["choices"][0]["message"]["role"], "assistant")
        self.assertEqual(response["choices"][0]["message"]["content"], "OK")
        self.assertIn("usage", response)

    def test_cai_wrapper_normalizes_ollama_model_and_base_url(self):
        class FakeLiteLLM:
            def __init__(self):
                self.call = None

            def completion(self, **kwargs):
                self.call = kwargs

                class Message:
                    content = "OK"

                class Choice:
                    message = Message()

                class Response:
                    choices = [Choice()]

                return Response()

        fake = FakeLiteLLM()
        with patch.dict("sys.modules", {"litellm": fake}):
            wrapper = CAIWrapper(
                backend_model="qwen3:4b-instruct",
                backend_base_url="http://localhost:11434/v1",
            )
        self.assertEqual(wrapper.model_name, "ollama/qwen3:4b-instruct")
        self.assertEqual(wrapper.ollama_api_base, "http://localhost:11434")
        self.assertEqual(wrapper.complete([{"role": "user", "content": "Say OK"}]), "OK")
        self.assertEqual(fake.call["model"], "ollama/qwen3:4b-instruct")
        self.assertEqual(fake.call["api_base"], "http://localhost:11434")


if __name__ == "__main__":
    unittest.main()
