"""Experience product version, independent of upstream patch and launcher versions."""
import re

VERSION = 'v0.18.1'


def validate_release_tag(tag):
    """Reject a release build whose tag disagrees with the displayed version."""
    if tag and tag.startswith('v') and tag != VERSION:
        raise ValueError('Release tag %s differs from Experience version %s' % (tag, VERSION))


def configure(scope):
    # Preserve upstream provenance. asm/build.py separately copies VERSION
    # into the native title authority and checks the reserved field length.
    scope['EX_VERSION'] = VERSION
    scope['TITLE'] = 'V-On Patcher EX ' + VERSION
    scope['EX_ATTRIBUTION'] = re.sub(r'^VO PATCH EX \S+', 'VO PATCH EX ' + VERSION,
                                     scope['EX_ATTRIBUTION'])


def build_identity(revision, kind='prerelease', rc=None):
    """Resolve immutable package identity without embedding a source hash in source."""
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('A complete release-source commit is required')
    labels = {'release': '', 'prerelease': 'Pre-Release', 'development': 'Dev'}
    if kind == 'rc':
        if not isinstance(rc, int) or rc < 1:
            raise ValueError('RC number must be positive')
        label = 'RC%d' % rc
    elif kind in labels:
        label = labels[kind]
    else:
        raise ValueError('Unknown build kind')
    subtitle = (label + ' · ' + revision[:7]) if label else ''
    return {'release': VERSION, 'revision': revision, 'kind': kind,
            'rc': rc if kind == 'rc' else None, 'title': 'VO PATCH EX ' + VERSION.removeprefix('v'),
            'subtitle': subtitle}
