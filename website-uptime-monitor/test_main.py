import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# check_website and helpers live in main.py
import main


class TestValidateUrl(unittest.TestCase):

    def test_adds_https_when_missing(self):
        url, err = main.validate_url("example.com")
        self.assertIsNone(err)
        self.assertEqual(url, "https://example.com")

    def test_keeps_http_scheme(self):
        url, err = main.validate_url("http://example.com")
        self.assertIsNone(err)
        self.assertEqual(url, "http://example.com")

    def test_keeps_https_scheme(self):
        url, err = main.validate_url("https://example.com")
        self.assertIsNone(err)

    def test_blocks_localhost_by_name(self):
        _, err = main.validate_url("localhost")
        self.assertIsNotNone(err)
        self.assertIn("localhost", err.lower())

    def test_blocks_loopback_ip(self):
        _, err = main.validate_url("127.0.0.1")
        self.assertIsNotNone(err)

    def test_empty_hostname_is_invalid(self):
        _, err = main.validate_url("https://")
        self.assertIsNotNone(err)


class TestIsPrivateIp(unittest.TestCase):

    def test_private_192_range(self):
        with patch("socket.gethostbyname", return_value="192.168.1.1"):
            self.assertTrue(main.is_private_ip("somehost"))

    def test_private_10_range(self):
        with patch("socket.gethostbyname", return_value="10.0.0.5"):
            self.assertTrue(main.is_private_ip("somehost"))

    def test_public_ip_not_private(self):
        with patch("socket.gethostbyname", return_value="8.8.8.8"):
            self.assertFalse(main.is_private_ip("dns.google"))

    def test_dns_failure_returns_false(self):
        import socket
        with patch("socket.gethostbyname", side_effect=socket.gaierror):
            self.assertFalse(main.is_private_ip("unresolvable.invalid"))


class TestLoadHistory(unittest.TestCase):

    def test_returns_empty_list_when_file_missing(self):
        with patch("main.HISTORY_FILE", "/nonexistent/path/history.json"):
            result = main.load_history()
        self.assertEqual(result, [])

    def test_returns_empty_list_on_corrupt_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{")
            tmp_path = f.name
        try:
            with patch("main.HISTORY_FILE", tmp_path):
                result = main.load_history()
            self.assertEqual(result, [])
        finally:
            os.unlink(tmp_path)

    def test_loads_valid_history(self):
        records = [{"url": "https://example.com", "uptime_status": "UP"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(records, f)
            tmp_path = f.name
        try:
            with patch("main.HISTORY_FILE", tmp_path):
                result = main.load_history()
            self.assertEqual(result, records)
        finally:
            os.unlink(tmp_path)

    def test_returns_empty_list_when_json_is_not_a_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"unexpected": "object"}, f)
            tmp_path = f.name
        try:
            with patch("main.HISTORY_FILE", tmp_path):
                result = main.load_history()
            self.assertEqual(result, [])
        finally:
            os.unlink(tmp_path)


class TestCheckWebsite(unittest.TestCase):

    def _mock_response(self, status_code, history=None, url="https://example.com"):
        mock = MagicMock()
        mock.status_code = status_code
        mock.history = history or []
        mock.url = url
        return mock

    def test_200_returns_up(self):
        with patch("requests.get", return_value=self._mock_response(200)):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "UP")
        self.assertEqual(code, 200)
        self.assertIsNone(err)

    def test_404_returns_down(self):
        with patch("requests.get", return_value=self._mock_response(404)):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "DOWN")
        self.assertEqual(code, 404)

    def test_500_returns_down(self):
        with patch("requests.get", return_value=self._mock_response(500)):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "DOWN")

    def test_timeout_returns_down_with_message(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.Timeout):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "DOWN")
        self.assertIsNone(code)
        self.assertIn("timed out", err.lower())

    def test_ssl_error_returns_down_with_message(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.SSLError):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "DOWN")
        self.assertIn("ssl", err.lower())

    def test_connection_error_returns_down(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.ConnectionError):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "DOWN")
        self.assertIsNone(code)

    def test_too_many_redirects_returns_down(self):
        import requests as req
        with patch("requests.get", side_effect=req.exceptions.TooManyRedirects):
            code, status, elapsed, err = main.check_website("https://example.com")
        self.assertEqual(status, "DOWN")
        self.assertIn("redirect", err.lower())


if __name__ == "__main__":
    unittest.main()


class TestLogging(unittest.TestCase):
    """Verify that the right log levels fire for each check outcome."""

    def _check_with_log(self, side_effect=None, return_value=None):
        """Run check_website and capture log output."""
        mock = MagicMock()
        mock.status_code = 200
        mock.history = []
        mock.url = "https://example.com"

        # Logger name is "main" when the module is imported (not "__main__")
        with self.assertLogs("main", level="DEBUG") as log_ctx:
            if side_effect:
                with patch("requests.get", side_effect=side_effect):
                    result = main.check_website("https://example.com")
            else:
                with patch("requests.get", return_value=return_value or mock):
                    result = main.check_website("https://example.com")
        return result, log_ctx.output

    def test_successful_check_logs_info(self):
        mock = MagicMock()
        mock.status_code = 200
        mock.history = []
        mock.url = "https://example.com"
        _, logs = self._check_with_log(return_value=mock)
        info_logs = [l for l in logs if "INFO" in l]
        self.assertTrue(any("UP" in l for l in info_logs))

    def test_timeout_logs_warning(self):
        import requests as req
        _, logs = self._check_with_log(side_effect=req.exceptions.Timeout)
        warning_logs = [l for l in logs if "WARNING" in l]
        self.assertTrue(any("timeout" in l.lower() for l in warning_logs))

    def test_ssl_error_logs_error(self):
        import requests as req
        _, logs = self._check_with_log(side_effect=req.exceptions.SSLError)
        error_logs = [l for l in logs if "ERROR" in l]
        self.assertTrue(any("ssl" in l.lower() for l in error_logs))

    def test_connection_error_logs_warning(self):
        import requests as req
        _, logs = self._check_with_log(side_effect=req.exceptions.ConnectionError)
        warning_logs = [l for l in logs if "WARNING" in l]
        self.assertTrue(len(warning_logs) > 0)

    def test_logs_do_not_contain_passwords(self):
        """Confirm no accidental password or token leakage in log output."""
        mock = MagicMock()
        mock.status_code = 200
        mock.history = []
        mock.url = "https://example.com"
        _, logs = self._check_with_log(return_value=mock)
        combined = " ".join(logs).lower()
        for sensitive in ("password", "token", "secret", "api_key", "authorization"):
            self.assertNotIn(sensitive, combined)

    def test_validate_url_logs_warning_for_localhost(self):
        with self.assertLogs("main", level="WARNING") as log_ctx:
            main.validate_url("localhost")
        self.assertTrue(any("localhost" in l.lower() or "blocked" in l.lower() for l in log_ctx.output))

    def test_validate_url_logs_warning_for_private_ip(self):
        with patch("socket.gethostbyname", return_value="192.168.1.1"):
            with self.assertLogs("main", level="WARNING") as log_ctx:
                main.validate_url("someinternal.host")
        self.assertTrue(any("private" in l.lower() or "blocked" in l.lower() for l in log_ctx.output))
