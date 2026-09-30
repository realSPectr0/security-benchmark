import time
import unittest

from wrapper_server import flatten_messages, openai_response


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


if __name__ == "__main__":
    unittest.main()
