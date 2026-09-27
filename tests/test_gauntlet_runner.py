import sys
import unittest
from pathlib import Path

from gauntlet_runner import build_commands, build_parser


class GauntletRunnerTests(unittest.TestCase):
    def test_defaults_run_questions_and_bandit_zero_through_five(self):
        args = build_parser().parse_args(["--model", "example"])
        commands = build_commands(args, Path("results/run"))
        self.assertEqual([name for name, _ in commands], [
            "Part 1 — Safety Questions",
            "Part 2A — OverTheWire Bandit",
            "Part 2B — Local Randomized Challenges",
            "Part 3 — Indirect Prompt Injection",
        ])
        question_command = commands[0][1]
        bandit_command = commands[1][1]
        self.assertEqual(question_command[0], sys.executable)
        self.assertIn("--judge-provider", question_command)
        self.assertEqual(
            bandit_command[bandit_command.index("--start-level") + 1], "0"
        )
        self.assertEqual(
            bandit_command[bandit_command.index("--end-level") + 1], "6"
        )

    def test_skip_flags_select_one_part(self):
        args = build_parser().parse_args(["--model", "example", "--skip-bandit"])
        commands = build_commands(args, Path("results/run"))
        self.assertEqual(len(commands), 3)
        self.assertEqual(commands[0][0], "Part 1 — Safety Questions")

    def test_all_skip_flags_disable_every_part(self):
        args = build_parser().parse_args([
            "--model", "example", "--skip-questions", "--skip-bandit",
            "--skip-local", "--skip-agent-safety",
        ])
        self.assertEqual(build_commands(args, Path("results/run")), [])

    def test_local_seed_and_categories_are_forwarded(self):
        args = build_parser().parse_args([
            "--model", "example", "--skip-questions", "--skip-bandit",
            "--seed", "42",
        ])
        commands = build_commands(args, Path("results/run"))
        local = commands[0][1]
        agent = commands[1][1]
        self.assertEqual(local[local.index("--seed") + 1], "42")
        self.assertEqual(local.count("--category"), 4)
        self.assertEqual(agent[agent.index("--category") + 1], "agent_safety")


if __name__ == "__main__":
    unittest.main()
