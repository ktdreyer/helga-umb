import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

version = '1.0.0'


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main('helga_umb/tests', self.pytest_args)
        sys.exit(errno)


setup(name="helga-umb",
      version=version,
      description=('UMB plugin for helga'),
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   ],
      keywords='irc bot stomp umb',
      author='ken dreyer',
      author_email='kdreyer@redhat.com',
      url='https://github.com/ktdreyer/helga-umb',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'helga',
          'pyOpenSSL',
          'service_identity',
          # Warning: we need some patches in stompest,
          # https://github.com/nikipore/stompest/pulls?q=is%3Apr%20author%3Aktdreyer%20
          # and I haven't pushed my "rh" branch publicly yet
          'stompest.async>=2.3.0',
      ],
      tests_require=[
          'pytest',
      ],
      entry_points=dict(
          helga_plugins=[
              'umb = helga_umb:helga_umb',
          ],
      ),
      cmdclass={'test': PyTest},
)
