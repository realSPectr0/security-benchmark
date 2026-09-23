import json
import unittest

from challenge_runner import (
    REDACTION,
    extract_action,
    redact,
    redact_credential_shapes,
    render_challenge_report,
    validate_command,
)


class ChallengeRunnerTests(unittest.TestCase):
    def test_extract_command_action(self):
        action = extract_action('```json\n{"action":"command","command":"ls -la"}\n```')
        self.assertEqual(action["command"], "ls -la")

    def test_extract_submit_action(self):
        action = extract_action(json.dumps({"action": "submit", "password": "synthetic"}))
        self.assertEqual(action["password"], "synthetic")

    def test_rejects_destructive_command(self):
        with self.assertRaisesRegex(ValueError, "safety policy"):
            validate_command("rm -rf /", "/tmp/clanker-safe")

    def test_redacts_nested_credentials(self):
        value = {"output": "password is synthetic-secret", "nested": ["synthetic-secret"]}
        redacted = redact(value, ["synthetic-secret"])
        self.assertNotIn("synthetic-secret", json.dumps(redacted))
        self.assertIn(REDACTION, redacted["output"])

    def test_redacts_unsubmitted_credential_shapes(self):
        possible_password = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
        self.assertEqual(redact_credential_shapes(possible_password), REDACTION)

    def test_challenge_report_is_readable(self):
        summary = {
            "target_model": "example",
            "game": "OverTheWire Bandit",
            "start_level": 0,
            "end_level": 1,
            "levels_solved": 1,
            "levels_attempted": 1,
            "solve_rate_percent": 100.0,
            "total_seconds": 4.2,
            "median_solve_seconds": 4.2,
            "results": [{
                "id": "BANDIT-00-TO-01", "status": "solved", "total_seconds": 4.2,
                "model_seconds": 3.0, "command_seconds": 1.2, "actions": 2,
            }],
        }
        report = render_challenge_report(summary)
        self.assertIn("BANDIT-00-TO-01", report)
        self.assertIn("100.0%", report)
        self.assertIn("Attempted    : 1", report)
        self.assertNotIn("password", report.lower())


if __name__ == "__main__":
    unittest.main()
