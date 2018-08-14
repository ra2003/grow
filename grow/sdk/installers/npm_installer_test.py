"""Tests for NPM Installer."""

import unittest
import mock
from grow.common import base_config
from grow.sdk.installers import base_installer
from grow.sdk.installers import npm_installer
from grow.testing import mocks


class NpmInstallerTestCase(unittest.TestCase):
    """Test the NPM Installer."""

    def _make_package(self):
        expected_files = ('/package.json',)
        self.pod.file_exists.side_effect = lambda name: name in expected_files

    def _make_nvm(self):
        expected_files = ('/.nvmrc',)
        self.pod.file_exists.side_effect = lambda name: name in expected_files

    def _make_yarn(self):
        expected_files = ('/yarn.lock',)
        self.pod.file_exists.side_effect = lambda name: name in expected_files

    def setUp(self):
        self.config = base_config.BaseConfig()
        env = mocks.mock_env(name="testing")
        self.pod = mocks.mock_pod(env=env, root='/testing/')
        self.pod.file_exists.return_value = False
        self.installer = npm_installer.NpmInstaller(self.pod, self.config)

    @mock.patch('subprocess.call')
    def test_check_prerequisites_npm(self, mock_call):
        """Check prerequisites for npm."""
        mock_call.return_value = 0
        self.installer.check_prerequisites()
        mock_call.assert_called_once_with(
            'npm --version > /dev/null 2>&1', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.call')
    def test_check_prerequisites_yarn(self, mock_call):
        """Check prerequisites for yarn."""
        mock_call.return_value = 0
        self._make_yarn()
        self.installer.check_prerequisites()
        mock_call.assert_called_once_with(
            'yarn --version > /dev/null 2>&1', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.call')
    def test_check_prerequisites_fail_npm(self, mock_call):
        """Fail check prerequisites for npm."""
        mock_call.return_value = 127
        with self.assertRaises(base_installer.MissingPrerequisiteError):
            self.installer.check_prerequisites()

    @mock.patch('subprocess.call')
    def test_check_prerequisites_fail_yarn(self, mock_call):
        """Fail check prerequisites for yarn."""
        mock_call.return_value = 127
        self._make_yarn()
        with self.assertRaises(base_installer.MissingPrerequisiteError):
            self.installer.check_prerequisites()

    @mock.patch('subprocess.Popen')
    def test_install_npm(self, mock_popen):
        """Install uses npm."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        self.installer.install()
        mock_popen.assert_called_once_with(
            'npm install', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.Popen')
    def test_install_npm_with_nvm(self, mock_popen):
        """Install uses npm."""
        self._make_nvm()
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        self.installer.install()
        mock_popen.assert_called_once_with(
            '. $NVM_DIR/nvm.sh && nvm exec npm install', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.Popen')
    def test_install_yarn(self, mock_popen):
        """Install uses yarn."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        self._make_yarn()
        self.installer.install()
        mock_popen.assert_called_once_with(
            'yarn install', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.Popen')
    def test_install_failed_npm(self, mock_popen):
        """Install fails using npm."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

    @mock.patch('subprocess.Popen')
    def test_install_failed_yarn(self, mock_popen):
        """Install fails using yarn."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        self._make_yarn()
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

    def test_post_install_messages_npm(self):
        """Post install messages for npm."""
        self.assertEqual(['Finished: npm'], self.installer.post_install_messages)

    def test_post_install_messages_yarn(self):
        """Post install messages for yarn."""
        self._make_yarn()
        self.assertEqual(['Finished: yarn'], self.installer.post_install_messages)

    def test_should_run(self):
        """Detect if should run when using npm."""
        self.assertFalse(self.installer.should_run)
        self._make_package()
        self.assertTrue(self.installer.should_run)

    def test_using_yarn_false(self):
        """Using yarn."""
        self.assertFalse(self.installer.using_yarn)

    def test_using_yarn_true(self):
        """Not using yarn."""
        self._make_yarn()
        self.assertTrue(self.installer.using_yarn)