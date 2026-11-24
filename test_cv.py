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

# The portrait and the logos are embedded as base64, and base64 is an alphabet
# of letters, digits, "+" and "/" — so a long enough blob contains "+49", and
# "ING" too, purely by chance. It did: the logo strip broke this file's own
# phone-number check on its first push. The denylists are about prose, so they
# read the page with the embedded bytes taken out.
DATA_URI = re.compile(r"data:[a-z/+-]+;base64,[A-Za-z0-9+/=]+")


def prose(page: str) -> str:
    return DATA_URI.sub("", page)


class PublicCV(unittest.TestCase):
    def setUp(self):
        self.page = prose(build.render(CV))

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
        for heading in ("Experience", "Skills", "Selected projects",
                        "Education", "Languages", "Research"):
            self.assertIn(heading, self.page)

    def test_bar_labels_survived_the_yaml(self):
        """An unquoted comma inside { } ends the value: "Applied AI, agents &
        LLM orchestration" parsed as the name "Applied AI" plus a stray key,
        and the page rendered the short half without complaining."""
        for b in CV.get("strengths", []):
            self.assertEqual(set(b), {"name", "level"}, f"stray keys: {b}")
            self.assertIsInstance(b["level"], int, b)

    def test_every_pin_is_on_the_map(self):
        for pin in CV.get("map", {}).get("pins", []):
            self.assertTrue(-180 <= pin["lon"] <= 180, pin)
            self.assertTrue(-58 <= pin["lat"] <= 84, f"outside the drawn band: {pin}")

    def test_orcid_is_linked(self):
        self.assertIn("orcid.org", self.page)


class TestTheQRCode(unittest.TestCase):
    """A QR code that does not scan is worse than no QR code: it is printed on
    the page claiming to work. The matrix comes from a real encoder, so the
    only thing that can break it here is the drawing — rects are merged across
    horizontal runs, and an off-by-one in that merge is invisible to the eye.
    So read the drawing back and compare it with the matrix."""

    def setUp(self):
        self.rows = [l for l in (ROOT / "assets" / "qr-cv.txt").read_text().splitlines()
                     if l and not l.startswith("#")]

    def test_the_drawing_matches_the_matrix(self):
        n = len(self.rows)
        grid = [["0"] * n for _ in range(n)]
        for x, y, w in re.findall(
                r'<rect x="(\d+)" y="(\d+)" width="(\d+)" height="1"/>', build.qr()):
            for i in range(int(w)):
                grid[int(y)][int(x) + i] = "1"
        self.assertEqual(["".join(r) for r in grid], self.rows)

    def test_it_points_at_the_live_cv(self):
        head = (ROOT / "assets" / "qr-cv.txt").read_text().splitlines()[0]
        self.assertEqual(head, "# https://adminleo.github.io/cv")


class TestThePortrait(unittest.TestCase):
    """The page is one file. The photo has to travel inside it."""

    def setUp(self):
        # The one class that wants the embedded bytes left in.
        self.page = build.render(CV)

    def test_the_photo_is_embedded_not_linked(self):
        self.assertIn("data:image/png;base64,", self.page)

    def test_no_image_is_fetched_from_elsewhere(self):
        """A CV that loads its portrait from a server is one deploy away from
        showing a recruiter a broken image. It has happened to the email
        signature three times."""
        for tag in re.findall(r"<img[^>]*>", self.page):
            self.assertIn("data:image/", tag, f"image fetched remotely: {tag[:80]}")

    def test_the_page_still_builds_without_a_photo(self):
        self.assertIsInstance(build.photo(), str)



if __name__ == "__main__":
    unittest.main()
