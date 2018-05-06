from periodDetection import echo
import unittest


def setUpModule():
    print("setUpModule")


def tearDownModule():
    print("tearUpModule")


class TestAdd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("setUpClass")

    @classmethod
    def tearDownClass(cls):
        print("tearDownClass")

    def setUp(self):
        print("instance setUp")

    def tearDown(self):
        print("instance tearDown")

    def test_echo(self):
        self.assertEqual(echo('hello'), 'hello')


def add_suite():
    suite = unittest.TestSuite()
    suite.addTest(TestAdd("test_echo"))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    test_suite = add_suite()
    runner.run(test_suite)
