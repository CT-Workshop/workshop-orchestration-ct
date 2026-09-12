"""Guards the intent recorded in app/services/document_hash_policy.py.

This module isn't wired into the workflow yet (see its docstring), so there's
no behavior to unit test. What we can and must guard against is someone
quietly deleting the recorded decision while wiring the real check in later —
the next engineer should have to touch this test, not just the docstring.
"""

import unittest

from app.services import document_hash_policy


class DocumentHashPolicyIntentTest(unittest.TestCase):
    def test_docstring_states_orchestration_owns_the_check(self):
        doc = document_hash_policy.__doc__ or ""
        self.assertIn("SHA-256", doc)
        self.assertIn("orchestration", doc)
        self.assertIn("do not move this check into ingestion", doc.lower())

    def test_docstring_states_the_failure_mode_to_avoid(self):
        doc = (document_hash_policy.__doc__ or "").lower()
        self.assertIn("swapped file must not be able to reach", doc)


if __name__ == "__main__":
    unittest.main()
