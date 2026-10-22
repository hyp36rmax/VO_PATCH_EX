"""Test promotion authorization without network, credentials or release writes."""
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import experience as guard


class AuthorizationTests(unittest.TestCase):
    def setUp(self):
        # A historical authorization supplies test structure, never live approval.
        fixture = Path('.github/release-authorizations/v0.18.0.json')
        self.record = json.loads(fixture.read_text())
        self.record['version'] = guard.VERSION
        self.record['windows_acceptance']['baseline_commit'] = guard.VALIDATED_BASELINE
        self.payload = b'test artifact'
        self.notes = b'test notes'
        self.record.update(artifact_sha256=guard.digest(self.payload), artifact_size=len(self.payload),
                           notes_sha256=guard.digest(self.notes))
        sha = self.record['application_commit']
        self.context = dict(repository=guard.REPO, event='workflow_dispatch', ref='refs/heads/Experience',
                            default_branch='Experience', sha='trusted-workflow', remote_sha='trusted-workflow',
                            workflow_ref=guard.REPO + '/' + guard.WORKFLOW + '@refs/heads/Experience',
                            version=guard.VERSION, application_commit=sha, implementation_unchanged=True)
        self.run = dict(id=self.record['ci_run_id'], run_attempt=self.record['ci_run_attempt'],
                        head_sha=sha, head_branch='Experience', event='push',
                        repository={'full_name': guard.REPO}, head_repository={'full_name': guard.REPO},
                        path='.github/workflows/build.yml', status='completed', conclusion='success')
        self.jobs = [dict(name=name, conclusion='success', head_sha=sha)
                     for name in ('verify', 'experience-native', 'windows')]
        self.artifact = dict(id=self.record['ci_artifact_id'], name=self.record['ci_artifact_name'],
                             expired=False, workflow_run=dict(id=self.record['ci_run_id'], head_sha=sha))

    def check(self):
        guard.authorize(self.record, self.context, self.run, self.jobs, self.artifact, self.payload, self.notes)

    def reject(self):
        with self.assertRaises(ValueError):
            self.check()

    def test_exact_authorization(self):
        self.check()

    def test_unauthorized_tag(self):
        self.context['version'] = 'v99.0.0'
        self.reject()

    def test_wrong_version(self):
        self.record['version'] = 'v99.0.0'
        self.reject()

    def test_wrong_application_commit(self):
        self.context['application_commit'] = '0' * 40
        self.reject()

    def test_wrong_ci_source(self):
        self.run['head_sha'] = '0' * 40
        self.reject()

    def test_wrong_checksum(self):
        self.payload = b'other artifact'
        self.reject()

    def test_missing_acceptance(self):
        self.record.pop('windows_acceptance')
        self.reject()

    def test_acceptance_identity(self):
        self.record['windows_acceptance']['baseline_commit'] = '0' * 40
        self.reject()

    def test_changed_implementation(self):
        self.context['implementation_unchanged'] = False
        self.reject()

    def test_no_new_physical_claim(self):
        self.record['windows_acceptance']['exact_artifact_physical_test'] = 'PASS'
        self.reject()

    def test_gameplay_diff_rejected(self):
        with patch.object(guard.subprocess, 'run'), patch.object(
                guard.subprocess, 'check_output', return_value='asm/bosses.asm\n'):
            with self.assertRaises(ValueError):
                guard.verify_implementation(self.record['application_commit'])

    def test_failed_ci(self):
        self.run['conclusion'] = 'failure'
        self.reject()

    def test_failed_windows_job(self):
        self.jobs[-1]['conclusion'] = 'failure'
        self.reject()

    def test_missing_job(self):
        self.jobs.pop()
        self.reject()

    def test_missing_artifact(self):
        self.artifact = None
        self.reject()

    def test_missing_zip(self):
        self.payload = None
        self.reject()

    def test_expired_artifact(self):
        self.artifact['expired'] = True
        self.reject()

    def test_wrong_provenance(self):
        self.artifact['workflow_run']['id'] += 1
        self.reject()

    def test_untrusted_event(self):
        for event in ('pull_request', 'pull_request_target', 'push'):
            with self.subTest(event=event):
                self.context['event'] = event
                self.reject()

    def test_untrusted_ref(self):
        self.context['ref'] = 'refs/heads/unreviewed'
        self.reject()

    def test_untrusted_repository(self):
        self.context['repository'] = 'attacker/fork'
        self.reject()

    def test_stale_authorization(self):
        self.context['remote_sha'] = 'changed'
        self.reject()

    def test_wrong_workflow(self):
        self.context['workflow_ref'] = 'another-workflow'
        self.reject()

    def test_changed_notes(self):
        self.notes = b'different notes'
        self.reject()

    def test_rerun_ci(self):
        self.run['run_attempt'] += 1
        self.reject()

    def test_stable_release_denied(self):
        self.record['prerelease'] = False
        self.reject()

    def test_committed_record(self):
        actual = json.loads(guard.RECORD.read_text())
        self.assertEqual(actual['windows_acceptance']['baseline_commit'], guard.VALIDATED_BASELINE)
        self.assertEqual(actual['windows_acceptance']['exact_artifact_physical_test'], 'NOT_RUN')
        self.assertTrue(guard.verify_implementation(actual['application_commit']))
        self.assertEqual(guard.digest(Path('docs/releases/' + guard.VERSION + '.md').read_bytes()), actual['notes_sha256'])

    def test_download_api_media_types(self):
        for path, expected in (('/actions/artifacts/1/zip', 'application/vnd.github+json'),
                               ('/releases/assets/1', 'application/octet-stream')):
            with self.subTest(path=path), patch.dict(guard.os.environ, {'GH_TOKEN': 'test-token'}):
                opener = MagicMock()
                opener.open.return_value.read.return_value = b'ZIP'
                with patch.object(guard.urllib.request, 'build_opener', return_value=opener):
                    self.assertEqual(guard.request(path, binary=True), b'ZIP')
                request = opener.open.call_args.args[0]
                self.assertEqual(request.get_header('Accept'), expected)

    def test_workflow_contract(self):
        workflow = Path(guard.WORKFLOW).read_text()
        self.assertIn('workflow_dispatch:', workflow)
        self.assertNotIn('pull_request:', workflow)
        self.assertNotIn('pull_request_target:', workflow)
        self.assertNotIn('package_normal.py', workflow)
        self.assertIn('needs: verify', workflow)
        self.assertEqual(workflow.count('contents: write'), 1)
        self.assertIn('persist-credentials: false', workflow)
        self.assertIn('Experience tags are not authorized for publication.', Path('.github/workflows/build.yml').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
