import unittest
import doctest 
from pprint import pprint
from interlude import interact

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [
    '../authentication.txt',
    '../model.txt',
    '../browser/layout.txt',
    '../browser/ajax.txt',
    '../browser/utils.txt',
    '../browser/authentication.txt',
    '../browser/authoring.txt',
    '../browser/contents.txt',
    '../browser/form.txt',
    '../browser/batch.txt',
]

def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
            file, 
            optionflags=optionflags,
            globs={'interact': interact,
                   'pprint': pprint},
        ) for file in TESTFILES
    ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')