"""Regression tests for synthetic evidence and bounded, independent support."""
import ast
import copy
import io
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from kalshi_public_buy.planner import plan
ROOT = Path(__file__).resolve().parents[1]
ENTRY = 'run_buy_planner.py'
SAMPLE = json.loads((ROOT / 'examples' / 'eligible_snapshot.json').read_text())


class RefreshPackageTests(unittest.TestCase):
    def clone(self):
        # Tests own their temporary roots under project outputs; nothing private copied.
        folder = ROOT / 'outputs' / 'tests'
        folder.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=folder)
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / 'project & spaces'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', 'outputs', '__pycache__'))
        return root

    def invoke(self, root, entry, *args):
        return subprocess.run([sys.executable, '-I', '-S', '-B', str(root / entry), *args],
                              capture_output=True, text=True, timeout=10, cwd=root.parent)

    def test_export_when_main_disabled(self):
        root = self.clone()
        (root / ENTRY).unlink()
        (root / 'MANIFEST.json').unlink()
        (root / 'PACKAGE_METADATA.json').unlink()
        shutil.rmtree(root / 'kalshi_public_buy')
        result = self.invoke(root, 'public_support.py', '--export')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['file_count'], 4)
        with zipfile.ZipFile(root / payload['path']) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(json.loads(archive.read('diagnostics.json'))['application_health'], 'NOT_CHECKED')

    def test_tampered_exporter_never_runs(self):
        root = self.clone()
        (root / 'public_support.py').write_text('raise RuntimeError("UNTRUSTED_SENTINEL")')
        result = self.invoke(root, ENTRY, '--export')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('UNTRUSTED_SENTINEL', result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['code'], 'SUPPORT_UNAVAILABLE')

    def test_critical_capsule_precedes_zip(self):
        root = self.clone()
        (root / 'VERSION.txt').write_text('changed')
        result = self.invoke(root, ENTRY, '--demo')
        self.assertEqual(result.returncode, 2)
        folder = root / 'outputs' / 'support'
        self.assertEqual(len(list(folder.glob('Critical_*.json'))), 1)
        self.assertEqual(len(list(folder.glob('Export20_*.zip'))), 1)
        self.assertEqual(list(folder.glob('.stage-*')), [])

    def test_invalid_input_is_not_critical(self):
        root = self.clone()
        result = self.invoke(root, ENTRY, 'missing.json')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((root / 'outputs' / 'support').exists())

    def test_export_lock_preserved_on_contention(self):
        root = self.clone()
        folder = root / 'outputs' / 'support'
        folder.mkdir(parents=True)
        lock = folder / '.export.lock'
        lock.write_text('sentinel')
        result = self.invoke(root, 'public_support.py', '--export')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(lock.read_text(), 'sentinel')

    def test_budget_does_not_prune_evidence(self):
        root = self.clone()
        folder = root / 'outputs' / 'support'
        folder.mkdir(parents=True)
        (folder / '.export_count').write_text('64')
        (folder / 'protected.txt').write_text('protected')
        result = self.invoke(root, 'public_support.py', '--export')
        self.assertEqual(result.returncode, 2)
        self.assertEqual((folder / 'protected.txt').read_text(), 'protected')
        self.assertEqual(list(folder.glob('*.zip')), [])

    def test_symlink_input_rejected(self):
        root = self.clone()
        folder = root / 'outputs'
        folder.mkdir()
        target = folder / 'target.json'
        target.write_text(json.dumps(SAMPLE))
        link = folder / 'link.json'
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest('Host does not permit symlink creation: ' + type(exc).__name__)
        result = self.invoke(root, ENTRY, str(link))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['reason'], 'INPUT_REJECTED')

    def test_output_symlink_rejected_without_external_writes(self):
        root = self.clone()
        external = root.parent / 'outside'
        external.mkdir()
        try:
            (root / 'outputs').symlink_to(external, target_is_directory=True)
        except OSError as exc:
            self.skipTest('Host does not permit symlink creation: ' + type(exc).__name__)
        result = self.invoke(root, 'public_support.py', '--export')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(external.iterdir()), [])

    def test_atomic_archive_not_visible_during_compression(self):
        root = self.clone()
        module = runpy.run_path(str(root / 'public_support.py'))
        observed = []
        original = zipfile.ZipFile.writestr
        def wrapped(archive, *args, **kwargs):
            observed.append(list((root / 'outputs' / 'support').glob('*.zip')))
            return original(archive, *args, **kwargs)
        with patch('zipfile.ZipFile.writestr', wrapped):
            result = module['export_support']()
        self.assertEqual(result['status'], 'EXPORTED')
        self.assertEqual(observed, [[], [], [], []])

    def test_same_run_critical_deduplicated(self):
        root = self.clone()
        export = runpy.run_path(str(root / 'public_support.py'))['export_support']
        first = export('FAIL')
        second = export('FAIL')
        self.assertEqual(first['status'], 'EXPORTED')
        self.assertEqual(second['status'], 'SUPPRESSED')
        self.assertEqual(len(list((root / 'outputs/support').glob('*.zip'))), 1)

    def test_low_disk_has_no_fallback(self):
        root = self.clone()
        export = runpy.run_path(str(root / 'public_support.py'))['export_support']
        usage = type('Usage', (), {'free': 0})()
        with patch('shutil.disk_usage', return_value=usage):
            result = export()
        self.assertEqual(result['status'], 'ERROR')
        self.assertFalse(list(root.rglob('*.zip')))

    def test_partial_capture_has_distinct_status(self):
        root = self.clone()
        export = runpy.run_path(str(root / 'public_support.py'))['export_support']
        with patch('zipfile.ZipFile', side_effect=OSError('DO_NOT_ECHO')):
            result = export('FAIL')
        self.assertEqual(result['status'], 'CAPSULE_ONLY')
        self.assertTrue((root / result['path']).is_file())
        self.assertNotIn('DO_NOT_ECHO', json.dumps(result))

    def test_support_runtime_imports_allowlist(self):
        allowed = {'sys', 'hashlib', 'io', 'json', 'os', 'pathlib', 'shutil', 'stat', 'time', 'uuid', 'zipfile'}
        tree = ast.parse((ROOT / 'public_support.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split('.')[0], allowed)
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module.split('.')[0], allowed)

    def test_export_uses_no_input_values(self):
        root = self.clone()
        (root / 'private.txt').write_text('DO_NOT_EXPORT_PRIVATE_SENTINEL')
        result = self.invoke(root, 'public_support.py', '--export')
        with zipfile.ZipFile(root / json.loads(result.stdout)['path']) as archive:
            self.assertNotIn(b'DO_NOT_EXPORT_PRIVATE_SENTINEL', b''.join(archive.read(n) for n in archive.namelist()))


class EvidenceReviewTests(unittest.TestCase):
    def sample(self):
        return copy.deepcopy(SAMPLE)

    def test_complete_review(self):
        result = plan(self.sample())
        self.assertEqual(result['status'], 'PLAN')
        self.assertEqual(result['analysis_review']['status'], 'READY_FOR_REVIEW')

    def test_neutral_under_six_does_not_block_plan(self):
        sample = self.sample()
        sample['analysis_evidence']['independent_response_count'] = 5
        result = plan(sample)
        self.assertEqual(result['status'], 'PLAN')
        self.assertEqual(result['analysis_review']['status'], 'NEUTRAL')

    def test_incomplete_history_blocks_only_analysis(self):
        sample = self.sample()
        sample['analysis_evidence']['history_complete'] = False
        result = plan(sample)
        self.assertEqual(result['status'], 'PLAN')
        self.assertEqual(result['analysis_review']['reason'], 'INCOMPLETE_HISTORY')

    def test_stale_analysis_never_graduates(self):
        sample = self.sample()
        sample['analysis_evidence']['age_seconds'] = 31
        self.assertEqual(plan(sample)['analysis_review']['reason'], 'STALE_ANALYSIS_EVIDENCE')

    def test_fee_lifecycle_before_holdout(self):
        sample = self.sample()
        sample['analysis_evidence'].update(lifecycle_fee_complete=False, chronological_holdout_complete=False)
        self.assertEqual(plan(sample)['analysis_review']['reason'], 'INCOMPLETE_LIFECYCLE_FEES')

    def test_holdout_required(self):
        sample = self.sample()
        sample['analysis_evidence']['chronological_holdout_complete'] = False
        self.assertEqual(plan(sample)['analysis_review']['reason'], 'HOLDOUT_NOT_COMPLETE')

    def test_optional_review_does_not_change_intent(self):
        sample = self.sample()
        first = plan(sample)['intent_id']
        del sample['analysis_evidence']
        self.assertEqual(plan(sample)['intent_id'], first)

    def test_bad_analysis_is_invalid_without_echo(self):
        for value in [-1, True, '6', 1.5, None]:
            with self.subTest(value=value):
                sample = self.sample()
                sample['analysis_evidence']['independent_response_count'] = value
                self.assertEqual(plan(sample)['status'], 'INVALID')

    def test_no_analysis_extra_field(self):
        sample = self.sample()
        sample['analysis_evidence']['hidden'] = 'SENTINEL'
        self.assertEqual(plan(sample)['status'], 'INVALID')

    def test_public_contract_remains_ten_times_one_cent(self):
        result = plan(self.sample())
        self.assertEqual((result['quantity'], result['price_cents'], result['principal_cents']), (10, 1, 10))


if __name__ == '__main__':
    unittest.main()
