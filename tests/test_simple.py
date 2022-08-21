# the inclusion of the tests module is not meant to offer best practices for
# testing in general, but rather to support the `find_packages` example in
# setup.py that excludes installing the "tests" package

import unittest

class TestTileMap(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
