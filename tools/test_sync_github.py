"""Offline tests for catalogue comparison and API pagination."""
import unittest
from unittest.mock import patch
from sync_github import compare, public_repositories


def repository(name, *, private=False, owner="RufusTheDwarf"):
    return {
        "name": name,
        "owner": {"login": owner},
        "private": private,
        "visibility": "private" if private else "public",
        "html_url": f"https://github.com/{owner}/{name}",
    }


class CatalogueTests(unittest.TestCase):
    def test_comparison_preserves_editorial_entries(self):
        projects = [{"repo": "Old", "summary": "Custom"}, {"repo": "GONE"}]
        report = compare(projects, [repository("old"), repository("New")])
        self.assertEqual(report["new_public_repositories"][0]["repo"], "New")
        self.assertEqual(report["catalogue_entries_not_in_public_listing"], ["GONE"])
        self.assertEqual(projects[0]["summary"], "Custom")

    def test_only_public_owned_repos_and_pagination(self):
        first = [repository(f"repo-{i}") for i in range(97)] + [
            repository("RufusTheDwarf"), repository("secret", private=True),
            repository("other", owner="Different"),
        ]
        with patch("sync_github.fetch_json", side_effect=[first, [repository("last")]]) as fetch:
            result = public_repositories("RufusTheDwarf")
        self.assertEqual(len(result), 98)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(result[-1]["name"], "last")

    def test_empty_catalogue(self):
        report = compare([], [])
        self.assertEqual(report["public_count_excluding_profile"], 0)
        self.assertEqual(report["new_public_repositories"], [])


if __name__ == "__main__":
    unittest.main()
