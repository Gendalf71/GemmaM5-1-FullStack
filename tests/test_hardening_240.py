from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from api_url_policy import require_api_token
from image_policy import image_data_url, read_validated_image


class Hardening240Tests(unittest.TestCase):
    def test_text_quality_gate_detects_trailing_whitespace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bad.md').write_text('bad  \n', encoding='utf-8')
            completed = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_text_quality.py'), '--root', str(root)], text=True, capture_output=True, check=False)
            self.assertNotEqual(0, completed.returncode)
            self.assertIn('trailing whitespace', completed.stderr)

    def test_token_policy_is_fail_closed(self):
        for value in (None, '', ' token', 'token ', 'to\nken'):
            with self.assertRaises(ValueError):
                require_api_token(value)
        self.assertEqual('token-123', require_api_token('token-123'))

    def test_image_policy_rejects_extension_spoofing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fake.png'
            path.write_bytes(b'not an image')
            with self.assertRaises(ValueError):
                read_validated_image(path)
        valid = ROOT / 'tests/fixtures/vision_test.png'
        self.assertTrue(image_data_url(valid).startswith('data:image/png;base64,'))

    def test_lm_studio_upgrade_is_explicit(self):
        source = (ROOT / 'scripts/install_lm_studio.sh').read_text(encoding='utf-8')
        self.assertIn('--upgrade', source)
        self.assertIn('No implicit upgrade was performed', source)
        self.assertIn('brew upgrade --cask lm-studio', source)

    def test_source_verifier_uses_current_version(self):
        source = (ROOT / 'scripts/verify_external_sources.py').read_text(encoding='utf-8')
        self.assertIn("f'GemmaM5-1-FullStack/{version} source-audit'", source)
        self.assertNotIn('GemmaM5-1-FullStack/1.1.150 source-audit', source)

    def test_agent_and_dependency_contracts_exist(self):
        agent = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn('Do not add model weights', agent)
        self.assertIn('make verify', agent)
        self.assertTrue((ROOT / 'docs/DEPENDENCY_POLICY.md').is_file())
        self.assertTrue((ROOT / 'docs/ru/DEPENDENCY_POLICY.md').is_file())

    def test_assurance_cross_links_are_closed(self):
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        assurance = json.loads((ROOT / f'docs/audit/release-assurance-{version}.json').read_text(encoding='utf-8'))
        self.assertEqual(194, assurance['revision_count'])
        self.assertEqual(91, assurance['unit_tests_expected'])
        self.assertEqual(2160, assurance['matrix']['total_control_passes'])

    def test_static_verification_does_not_use_compileall(self):
        source = (ROOT / 'scripts/verify_repo.sh').read_text(encoding='utf-8')
        self.assertNotIn('compileall', source)
        self.assertIn('verify_text_quality.py', source)
        self.assertFalse(any(ROOT.rglob('__pycache__')))


if __name__ == '__main__':
    unittest.main()
