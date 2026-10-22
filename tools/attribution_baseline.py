"""Pinned G02/S04 title expectations for historical whole-image comparisons.

Keep every original equality assertion. Rebuild reference images with precisely
this independently executed title blob; all other reference code/data is untouched.
"""
import hashlib
OLD = '7ab9b719d3fc4c5416ad14a7bdc8975b455c733287b7a03fbdb6d0d59e0c9509'
PREVIOUS = '95e48921bcda166e52e833c4e1e92dd625bfb777faaf6074ad1944823e667dd0'
S04 = '78198b6b498046a03a468291f9aad5b6bc36ecde6a067ff9a34eb2b5794c5c06'
NEW = 'db8ef24f1dea966f4b99c2e390580bfa0398c3f698e96405f2cfb912e8f9a673'
def align(reference, current):
    old = hashlib.sha256(reference.BLOBS['TITLEVER'][0]).hexdigest()
    new = hashlib.sha256(current.BLOBS['TITLEVER'][0]).hexdigest()
    assert old in (OLD, PREVIOUS, S04, NEW) and new == NEW, 'unreviewed attribution change'
    reference.BLOBS = dict(reference.BLOBS, TITLEVER=current.BLOBS['TITLEVER'])
    reference.TITLEVER_CODE = reference.link('TITLEVER', reference.RETAIL)
    def stamp(buf, build=reference.RETAIL):
        at = reference.site('TITLEVER').for_build(build) + len(reference.TITLEVER_CODE) - current.TITLEVER_LEN
        buf[at:at + current.TITLEVER_LEN] = current.title_data()
    reference.stamp_version = stamp
    # Retail Sym/At values are materialized at import. Re-evaluate their
    # original recipes after the reviewed blob-size change (JPRE does this
    # naturally in features()). Do not copy any sites from the current module.
    def rebuild(value):
        if isinstance(value, (reference.Sym, reference.At)):
            return value.for_build(reference.RETAIL)
        return value
    reference.FEATURES = [(key, label, tip,
                           [tuple(rebuild(x) for x in row) for row in sites])
                          for key, label, tip, sites in reference.FEATURES]
    for key, label, tip, sites in reference.FEATURES:
        if key not in ('hires', 'dinput'):
            reference.BY_KEY[key] = (label, tip, sites)
