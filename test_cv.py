"""Guards on the public CV.  python3 -m unittest test_cv -v

The denylist is the important one. The rule for this repository is that
employers are named and clients are described, because naming a client on a
public page is the client's decision and not mine. A rule nobody checks stops
holding the first time someone edits the YAML in a hurry, so it is checked here.
"""
import pathlib
import re
import unittest

import yaml

import build

ROOT = pathlib.Path(__file__).parent
CV = yaml.safe_load((ROOT / "cv.yaml").read_text(encoding="utf-8"))

# Clients and customers, never to appear in the rendered page.
# Employers (Creativate, Camsol, Karla, Bornhäußer & Friends) are deliberately absent here.
CLIENTS = ["Fresenius", "Aareal", "Börse Stuttgart", "Kassel", "ADAC",
           "Aramark", "Hugo Boss", "ING", "WDR", "Valisory", "KI-MAX",
           "Saxess", "DIHK", "Gasvisor", "CheckMe", "Skulup", "Ähdus"]

# Personal data that stays off a public page. Email and LinkedIn are published
# deliberately; a postal address and a phone number are not.
PRIVATE_HINTS = ["+49", "Straße", "Strasse", "str.", "@gmail"]


class PublicCV(unittest.TestCase):
    def setUp(self):
        self.page = build.render(CV)

    def test_no_client_is_named(self):
        # word boundaries, or a short acronym like ING matches "banking"
        hits = [c for c in CLIENTS
                if re.search(rf"\b{re.escape(c)}\b", self.page, re.I)]
        self.assertEqual(hits, [], f"client names leaked into the public CV: {hits}")

    def test_no_address_or_phone(self):
        hits = [h for h in PRIVATE_HINTS if h.lower() in self.page.lower()]
        self.assertEqual(hits, [], f"private contact details leaked: {hits}")

    def test_contact_is_email_and_links_only(self):
        p = CV["person"]
        self.assertIn("@", p["email"])
        self.assertNotIn("phone", p)
        self.assertNotIn("address", p)

    def test_every_role_has_company_and_period(self):
        for r in CV["experience"]:
            self.assertTrue(r.get("company"), r["title"])
            self.assertTrue(r.get("period"), r["title"])

    def test_all_prose_is_text_not_structure(self):
        # YAML reads an unquoted "Topic: detail" as a mapping, so the bullet
        # silently becomes a dict and renders as a Python literal on the page.
        for r in CV["experience"]:
            for b in r.get("bullets") or []:
                self.assertIsInstance(b, str, f"{r['title']}: {b!r}")
        for s in CV["skills"]:
            for i in s["items"]:
                self.assertIsInstance(i, str, f"{s['group']}: {i!r}")

    def test_no_python_literal_reaches_the_page(self):
        for marker in ("{'", "': '", "[{"):
            self.assertNotIn(marker, self.page,
                             f"structure leaked into rendered text: {marker}")

    def test_every_project_declares_its_stack(self):
        for p in CV["projects"]:
            self.assertTrue(p.get("tech"), p["title"])

    def test_page_renders_each_section(self):
        for heading in ("Experience", "Focus areas", "Selected projects",
                        "Education, languages"):
            self.assertIn(heading, self.page)

    def test_orcid_is_linked(self):
        self.assertIn("orcid.org", self.page)


if __name__ == "__main__":
    unittest.main()
