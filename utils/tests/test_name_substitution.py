# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.

import os
import unittest
import xml.etree.ElementTree as xml
from pathlib import Path

from .. import i18n_apply
from .. import name_substitution
from .. import name_substitution_utils as util


class NameSubstitutionTest(unittest.TestCase):
    def test_visible_product_copy(self):
        cases = {
            "Open chrome://settings": "Open jobrowsa://settings",
            "Meet Helium": "Meet Jobrowsa",
            "Helium flag.": "Jobrowsa flag.",
            "Helium's services": "Jobrowsa's services",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                replaced, had_match = util.replace_text(source)
                self.assertTrue(had_match)
                self.assertEqual(expected, replaced)

    def test_internal_names_are_preserved(self):
        for value in (
            "IDS_HELIUM_SERVICES_SCHEMA_MENU_ITEM",
            "kHeliumUIScheme",
            "HeliumNoise",
            "helium.services.origin_override",
            "HELIUM_VERSION",
        ):
            with self.subTest(value=value):
                replaced, had_match = util.replace_text(value)
                self.assertFalse(had_match)
                self.assertEqual(value, replaced)

    def test_grit_attributes_are_preserved(self):
        message = xml.fromstring(
            '<message name="IDS_HELIUM_SETUP" '
            'desc="Helium setup title">Helium Setup</message>'
        )
        self.assertTrue(util.replace_grit_message(message))
        self.assertEqual("Jobrowsa Setup", message.text)
        self.assertEqual("IDS_HELIUM_SETUP", message.get("name"))
        self.assertEqual("Helium setup title", message.get("desc"))

    def test_translated_product_copy(self):
        cases = {
            "Möt Helium": "Möt Jobrowsa",
            "Tutustu Heliumiin": "Tutustu Jobrowsaiin",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(expected, i18n_apply.to_xtb_message(source))

    def test_translation_fingerprint_input_tracks_substitution(self):
        # i18n_apply computes translation ids from replace_text() output,
        # while GRIT compares them against substituted GRD message values;
        # both sides must assemble identical fingerprint inputs.
        source = (
            'Helium will fetch <ph name="BANGS_LIST_URL">$1'
            "<ex>https://example.com</ex></ph> so you can browse faster."
        )
        element = xml.fromstring(f"<message>{source}</message>")
        util.replace_grit_message(element)

        def fingerprint_input(node):
            text = node.text or ""
            for ph in node.findall("ph"):
                text = text + ph.get("name").upper() + (ph.tail or "")
            return text

        branded, _ = util.replace_text(source)
        aligned = fingerprint_input(xml.fromstring(f"<message>{branded}</message>"))
        self.assertEqual(fingerprint_input(element), aligned)

    def test_executable_sanity_examples(self):
        name_substitution.replacement_sanity()

    def _require_grit(self):
        """compute_fp() lazily imports grit from the Chromium source tree."""
        try:
            import grit.extern.tclib  # noqa: F401
        except ImportError:
            tree = Path(
                os.environ.get(
                    "CHROMIUM_SRC",
                    Path(__file__).resolve().parents[3] / "build" / "src",
                )
            )
            if not (tree / "tools" / "grit").is_dir():
                self.skipTest("Chromium tree required for grit imports")
            util.add_grit_to_path(tree)

    def test_grit_tree_preserves_xml_prolog(self):
        # helium_onboarding_strings.grdp ships without an XML declaration;
        # its generator rejects files that gain one during substitution.
        self._require_grit()
        body = (
            "<grit-part>\n"
            '  <message name="IDS_X" desc="d">Helium Setup</message>\n'
            "</grit-part>\n"
        )

        replaced, fp_map = util.replace_grit_tree(body)
        self.assertFalse(replaced.lstrip().startswith("<?xml"))
        self.assertIn("Jobrowsa Setup", replaced)
        self.assertTrue(fp_map)

        declared = '<?xml version="1.0" encoding="utf-8"?>\n' + body
        replaced, _ = util.replace_grit_tree(declared)
        self.assertTrue(replaced.startswith("<?xml"))


if __name__ == "__main__":
    unittest.main()
