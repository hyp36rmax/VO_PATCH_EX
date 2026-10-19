"""Experience product version, independent of upstream patch and launcher versions."""
import re

VERSION = 'v0.18.0'


def validate_release_tag(tag):
    """Reject a release build whose tag disagrees with the displayed version."""
    if tag and tag.startswith('v') and tag != VERSION:
        raise ValueError('Release tag %s differs from Experience version %s' % (tag, VERSION))


def configure(scope):
    # VERSION also feeds upstream binary patch stamps. Keep it unchanged so
    # presentation-only updates cannot invalidate the frozen patch recipes.
    scope['EX_VERSION'] = VERSION
    scope['TITLE'] = 'V-On Patcher EX ' + VERSION
    scope['EX_ATTRIBUTION'] = re.sub(r'^VO PATCH EX \S+', 'VO PATCH EX ' + VERSION,
                                     scope['EX_ATTRIBUTION'])
