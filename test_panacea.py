"""Offline unit tests for Panacea (zero network or LLM quota used).
Run in PowerShell: py test_panacea.py"""
import unittest
from unittest.mock import patch
from adapters.base import Result
import planner
import core
import people


class TestPanaceaOffline(unittest.TestCase):
    def test_planner_parses_json_and_sources(self):
        fake_reply = '{"domain": "hardware", "wants": [], "queries": ["6dof robot arm", "stepper robot arm"]}'
        with patch("planner.ask", return_value=fake_reply):
            domain, queries, sources, wants = planner.plan(
                "build a 6-axis robot arm with 3D printed parts",
                ["github", "openalex", "cad", "guides", "huggingface"],
            )
            self.assertEqual(domain, "hardware")
            self.assertEqual(len(queries), 2)
            self.assertIn("cad", sources)

    def test_rank_parses_why_objects_and_plain_ints(self):
        items = [
            Result("Repo A", "https://a", "6dof arm", "github", "repo", "alice", "https://github.com/alice"),
            Result("Paper B", "https://b", "arm kinematics", "openalex", "paper", "Bob", "https://openalex.org/A123"),
        ]
        fake_rank = '[{"id": 1, "why": "Covers forward kinematics math"}, {"id": 0, "why": "Complete CAD and code"}]'
        with patch("core.ask", return_value=fake_rank):
            ranked, used_model = core.rank("6dof robot arm", items)
            self.assertTrue(used_model)
            self.assertEqual(ranked[0].title, "Paper B")
            self.assertEqual(ranked[0].why, "Covers forward kinematics math")

    def test_openalex_maker_info(self):
        r = Result("Paper", "https://doi.org/1", "summary", "openalex", "paper", "Jane Doe", "https://openalex.org/A12345")
        fake_author = {
            "display_name": "Jane Doe",
            "last_known_institutions": [{"display_name": "Lagos State University"}],
            "works_count": 42,
            "cited_by_count": 310,
            "orcid": "https://orcid.org/0000-0001-2345-6789",
        }
        with patch("net.get_json", return_value=fake_author):
            info = people.maker_info(r)
            self.assertEqual(info["institution"], "Lagos State University")
            self.assertIn("42", info["publications"])


if __name__ == "__main__":
    unittest.main()
