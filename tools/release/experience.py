"""Promote an approved CI artifact without rebuilding or changing its source tag."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

REPO = 'hyp36rmax/VO_PATCH_EX'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experience'))
from release_version import VERSION

VALIDATED_BASELINE = 'b6518d3f3c0777335fbb2100c1b99e8304797d2b'
# Frozen B02 implementation; only release maintenance and presentation may differ.
RELEASE_CHANGES = {
    '.github/workflows/build.yml', '.github/workflows/experience-version.yml',
    '.github/release-authorizations/v0.18.0.json',
    'tools/experience/release_version.py', 'tools/experience/package_normal.py',
    'README.md', 'docs/releases/v0.18.0.md', 'docs/releases/v0.18.1.md',
    'tools/release/README.md', 'tools/release/experience.py',
    'tools/release/test_experience.py',
}

RECORD = Path('.github/release-authorizations') / (VERSION + '.json')
WORKFLOW = '.github/workflows/publish-experience.yml'
ALLOWED_CHANGES = {
    str(RECORD), WORKFLOW, 'README.md', 'tools/release/experience.py',
    'tools/release/test_experience.py', 'tools/release/README.md',
    'docs/releases/' + VERSION + '.md',
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def authorize(record, context, run, jobs, artifact, payload, notes):
    """Fail closed before any mutation; inputs come from the trusted checkout/API."""
    require(context['repository'] == REPO, 'untrusted repository')
    require(context['event'] == 'workflow_dispatch', 'untrusted authorization event')
    require(context['ref'] == 'refs/heads/Experience', 'untrusted authorization ref')
    require(context['default_branch'] == 'Experience', 'unexpected default branch')
    require(context['sha'] == context['remote_sha'], 'authorization is not current Experience')
    require(context['workflow_ref'] == REPO + '/' + WORKFLOW + '@refs/heads/Experience',
            'untrusted publication workflow')
    require(record['schema'] == 2 and record['repository'] == REPO, 'invalid authorization')
    require(record['version'] == VERSION, 'unauthorized release version')
    require(context['version'] == record['version'], 'unauthorized tag')
    require(record['prerelease'] is True, 'only prereleases authorized')
    require(record['application_commit'] == context['application_commit'], 'wrong application commit')
    uat = record.get('windows_acceptance', {})
    require(uat.get('status') == 'PRESERVED_IMPLEMENTATION' and
            uat.get('confirmed_by') == 'hyp36rmax', 'missing baseline acceptance')
    require(uat.get('baseline_commit') == VALIDATED_BASELINE and
            uat.get('exact_artifact_physical_test') == 'NOT_RUN', 'acceptance scope mismatch')
    require(context.get('implementation_unchanged') is True, 'implementation differs from accepted baseline')
    require(run['id'] == record['ci_run_id'] and run['run_attempt'] == record['ci_run_attempt'],
            'wrong CI run or attempt')
    require(run['head_sha'] == record['application_commit'], 'CI source mismatch')
    require(run['head_branch'] == 'Experience' and run['event'] == 'push', 'untrusted CI source')
    require(run['repository']['full_name'] == REPO and
            run['head_repository']['full_name'] == REPO, 'untrusted CI repository')
    require(run['path'] == '.github/workflows/build.yml', 'wrong CI workflow')
    require(run['status'] == 'completed' and run['conclusion'] == 'success', 'hosted CI failed')
    by_name = {job['name']: job for job in jobs}
    for name in ('verify', 'experience-native', 'windows'):
        job = by_name.get(name, {})
        require(job.get('conclusion') == 'success' and job.get('head_sha') == record['application_commit'],
                'required CI job failed: ' + name)
    require(artifact is not None, 'missing release artifact')
    require(artifact['id'] == record['ci_artifact_id'] and
            artifact['name'] == record['ci_artifact_name'] and not artifact['expired'],
            'wrong or expired CI artifact')
    require(artifact['workflow_run']['id'] == record['ci_run_id'] and
            artifact['workflow_run']['head_sha'] == record['application_commit'],
            'artifact provenance mismatch')
    require(payload is not None, 'missing release ZIP')
    require(len(payload) == record['artifact_size'] and digest(payload) == record['artifact_sha256'],
            'wrong artifact checksum or size')
    require(digest(notes) == record['notes_sha256'], 'release notes changed')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(path, method='GET', data=None, binary=False):
    # Credentials are sent only to the fixed GitHub API hosts, never CDN redirects.
    url = 'https://api.github.com/repos/' + REPO + path
    if path.startswith('https://'):
        require(urllib.parse.urlparse(path).netloc == 'uploads.github.com', 'unexpected upload host')
        url = path
    headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
               'Accept': ('application/octet-stream' if binary and path.startswith('/releases/assets/')
                          else 'application/vnd.github+json'),
               'X-GitHub-Api-Version': '2022-11-28'}
    body = data if isinstance(data, bytes) else (json.dumps(data).encode() if data is not None else None)
    if body is not None:
        headers['Content-Type'] = 'application/zip' if isinstance(data, bytes) else 'application/json'
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        response = urllib.request.build_opener(NoRedirect).open(req, timeout=120)
    except urllib.error.HTTPError as error:
        if binary and method == 'GET' and error.code in (301, 302, 303, 307, 308):
            target = error.headers['Location']
            require(urllib.parse.urlparse(target).scheme == 'https', 'insecure artifact redirect')
            with urllib.request.urlopen(target, timeout=120) as response:
                return response.read()
        raise
    with response:
        raw = response.read()
    return raw if binary else json.loads(raw)


def absent(path):
    try:
        request(path)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return
        raise
    raise ValueError('publication target already exists: ' + path)


def verify_implementation(application_commit):
    """Keep the accepted implementation unchanged across the release-only update."""
    subprocess.run(['git', 'merge-base', '--is-ancestor', VALIDATED_BASELINE,
                    application_commit], check=True)
    changed = set(subprocess.check_output(
        ['git', 'diff', '--name-only', VALIDATED_BASELINE, application_commit],
        text=True).splitlines())
    require(changed <= RELEASE_CHANGES, 'implementation changed: ' + repr(changed - RELEASE_CHANGES))
    return True


def main():
    require(sys.argv[1:] in (['verify'], ['publish']), 'choose verify or publish')
    record = json.loads(RECORD.read_text())
    require(record['version'] == VERSION and record['repository'] == REPO, 'unauthorized record')
    # Check trusted dispatch before downloading artifacts or making any writes.
    require(os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
            os.environ.get('GITHUB_REF') == 'refs/heads/Experience' and
            os.environ.get('GITHUB_REPOSITORY') == REPO, 'untrusted authorization source')
    local = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    require(local == os.environ['GITHUB_SHA'], 'checkout does not match workflow')
    subprocess.run(['git', 'merge-base', '--is-ancestor', record['application_commit'], local], check=True)
    changed = set(subprocess.check_output(['git', 'diff', '--name-only', record['application_commit'], local],
                                          text=True).splitlines())
    require(changed <= ALLOWED_CHANGES, 'application changed since approval: ' + repr(changed - ALLOWED_CHANGES))
    repo = request('')
    remote = request('/git/ref/heads/Experience')['object']['sha']
    context = dict(repository=os.environ['GITHUB_REPOSITORY'], event=os.environ['GITHUB_EVENT_NAME'],
                   ref=os.environ['GITHUB_REF'], sha=local, remote_sha=remote,
                   workflow_ref=os.environ['GITHUB_WORKFLOW_REF'], default_branch=repo['default_branch'],
                   version=VERSION, application_commit=record['application_commit'],
                   implementation_unchanged=verify_implementation(record['application_commit']))
    run = request('/actions/runs/' + str(record['ci_run_id']))
    jobs = request('/actions/runs/' + str(record['ci_run_id']) + '/attempts/' +
                   str(record['ci_run_attempt']) + '/jobs?per_page=100')['jobs']
    artifact = request('/actions/artifacts/' + str(record['ci_artifact_id']))
    archive = request('/actions/artifacts/' + str(record['ci_artifact_id']) + '/zip', binary=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as outer:
        require(outer.namelist() == [record['artifact_name']], 'unexpected CI artifact contents')
        payload = outer.read(record['artifact_name'])
    notes = Path('docs/releases/' + VERSION + '.md').read_bytes()
    authorize(record, context, run, jobs, artifact, payload, notes)
    with zipfile.ZipFile(io.BytesIO(payload)) as package:
        require(package.testzip() is None, 'corrupt release ZIP')
    evidence = dict(application_commit=record['application_commit'], workflow_commit=local,
                    version=VERSION, artifact_sha256=digest(payload), ci_run_id=run['id'],
                    windows_acceptance=record['windows_acceptance'], status='VERIFIED')
    Path('publication-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))
    if sys.argv[1] == 'verify':
        return
    absent('/git/ref/tags/' + VERSION)
    absent('/releases/tags/' + VERSION)
    # Guard is rerun in the write-scoped job. Ref creation never updates an existing tag.
    require(request('/git/ref/heads/Experience')['object']['sha'] == local, 'Experience moved during validation')
    request('/git/refs', 'POST', {'ref': 'refs/tags/' + VERSION, 'sha': record['application_commit']})
    release = request('/releases', 'POST', dict(tag_name=VERSION,
                      target_commitish=record['application_commit'], name=record['title'],
                      body=notes.decode(), draft=True, prerelease=True, make_latest='false'))
    asset = request(release['upload_url'].split('{')[0] + '?name=' + record['artifact_name'], 'POST', payload)
    require(asset['size'] == len(payload), 'uploaded asset size mismatch')
    uploaded = request('/releases/assets/' + str(asset['id']), binary=True)
    require(digest(uploaded) == record['artifact_sha256'], 'uploaded asset checksum mismatch')
    require(request('/git/ref/tags/' + VERSION)['object']['sha'] == record['application_commit'], 'release tag changed')
    published = request('/releases/' + str(release['id']), 'PATCH',
                        dict(draft=False, prerelease=True, make_latest='false'))
    require(published['prerelease'] and not published['draft'], 'release publication mismatch')
    print('Published ' + published['html_url'])


if __name__ == '__main__':
    main()
