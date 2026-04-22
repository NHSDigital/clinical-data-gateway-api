from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
import requests.adapters

from gateway_api.apim_app_auth.http import SessionManager
from gateway_api.apim_app_auth.request_context import set_correlation_id


class TestSessionManager:
    @patch("tempfile.NamedTemporaryFile")
    @patch("requests.Session")
    def test_with_session(
        self, mock_session: MagicMock, mock_tempfile: MagicMock
    ) -> None:
        expected_timeout = timedelta(seconds=30)
        session_manager = SessionManager(
            client_timeout=expected_timeout,
            client_certificate=None,
        )

        @session_manager.with_session
        def mock_function(_: requests.Session) -> None:
            mock_session.return_value.mount.assert_called_once()
            args, _ = mock_session.return_value.mount.call_args

            assert args[0] == "https://"

            adapter = args[1]
            assert adapter is not None
            assert isinstance(adapter, SessionManager._Adapter)  # noqa: SLF001 - Private access for testing

            assert adapter._timeout == expected_timeout.total_seconds()  # noqa: SLF001 - Private access for testing

            mock_tempfile.assert_not_called()

        mock_function()
        mock_session.return_value.__exit__.assert_called_once()

    @patch("tempfile.NamedTemporaryFile")
    @patch("requests.Session")
    def test_with_session_with_client_cert(
        self, mock_session: MagicMock, mock_tempfile: MagicMock
    ) -> None:
        expected_timeout = timedelta(seconds=30)
        expected_cert = "cert_content"
        expected_key = "key_content"

        session_manager = SessionManager(
            client_timeout=expected_timeout,
            client_certificate={
                "certificate": expected_cert,
                "key": expected_key,
            },
        )

        mock_cert_file = MagicMock()
        mock_cert_file.name = "cert_file_name"

        mock_key_file = MagicMock()
        mock_key_file.name = "key_file_name"

        mock_tempfile.side_effect = [mock_cert_file, mock_key_file]

        @session_manager.with_session
        def mock_function(_: requests.Session) -> None:
            mock_session.return_value.mount.assert_called_once()
            args, _ = mock_session.return_value.mount.call_args

            assert args[0] == "https://"

            adapter = args[1]
            assert adapter is not None
            assert isinstance(adapter, SessionManager._Adapter)  # noqa: SLF001 - Private access for testing

            assert adapter._timeout == expected_timeout.total_seconds()  # noqa: SLF001 - Private access for testing

            assert mock_tempfile.call_count == 2

            assert mock_session.return_value.cert == (
                mock_cert_file.name,
                mock_key_file.name,
            )

            mock_cert_file.write.assert_called_once_with(expected_cert.encode())
            mock_cert_file.flush.assert_called_once()

            mock_key_file.write.assert_called_once_with(expected_key.encode())
            mock_key_file.flush.assert_called_once()

        mock_function()
        mock_session.return_value.__exit__.assert_called_once()
        mock_cert_file.__exit__.assert_called_once()
        mock_key_file.__exit__.assert_called_once()

    @patch("tempfile.NamedTemporaryFile")
    @patch("requests.Session")
    def test_with_session_raises_when_tempfile_creation_fails(
        self, mock_session: MagicMock, mock_tempfile: MagicMock
    ) -> None:
        expected_timeout = timedelta(seconds=30)

        session_manager = SessionManager(
            client_timeout=expected_timeout,
            client_certificate={
                "certificate": "cert_content",
                "key": "key_content",
            },
        )

        mock_tempfile.side_effect = OSError("unable to create temporary file")

        @session_manager.with_session
        def mock_function(_: requests.Session) -> None:
            msg = "Wrapped function should not be called when tempfile creation fails"
            raise AssertionError(msg)

        with pytest.raises(OSError, match="unable to create temporary file"):
            mock_function()

        mock_session.return_value.mount.assert_called_once()
        mock_session.return_value.__exit__.assert_called_once()
        assert mock_tempfile.call_count == 1

    @patch("requests.Session")
    def test_with_session_raises_when_wrapped_function_fails(
        self, mock_session: MagicMock
    ) -> None:
        expected_timeout = timedelta(seconds=30)
        session_manager = SessionManager(
            client_timeout=expected_timeout,
            client_certificate=None,
        )

        @session_manager.with_session
        def mock_function(_: requests.Session) -> None:
            raise RuntimeError("request handling failed")

        with pytest.raises(RuntimeError, match="request handling failed"):
            mock_function()

        mock_session.return_value.mount.assert_called_once()
        mock_session.return_value.__exit__.assert_called_once()

    def test_adapter_applies_defaults(self) -> None:
        with patch.object(
            requests.adapters.HTTPAdapter, "send", autospec=True
        ) as mock_send:
            set_correlation_id(
                full_id="test-correlation-id-long", short_id="test-correlation-id"
            )

            expected_timeout = timedelta(seconds=30)
            adapter = SessionManager._Adapter(timeout=expected_timeout.total_seconds())  # noqa: SLF001 - Private access for testing

            mock_request = Mock()
            mock_request.headers = {}

            expected_response = Mock()
            mock_send.return_value = expected_response

            response = adapter.send(mock_request, verify=True)
            assert response == expected_response

            mock_send.assert_called_once_with(
                adapter,
                mock_request,
                verify=True,
                timeout=expected_timeout.total_seconds(),
            )

            assert mock_request.headers["X-Correlation-ID"] == "test-correlation-id"

    def test_adapter_overrides_defaults(self) -> None:
        with patch.object(
            requests.adapters.HTTPAdapter, "send", autospec=True
        ) as mock_send:
            expected_timeout = timedelta(seconds=30)
            adapter = SessionManager._Adapter(timeout=expected_timeout.total_seconds())  # noqa: SLF001 - Private access for testing

            mock_request = Mock()
            expected_correlation_id = "correaltion-id"
            mock_request.headers = {"X-Correlation-ID": expected_correlation_id}

            expected_response = Mock()
            mock_send.return_value = expected_response

            response = adapter.send(mock_request, verify=True)
            assert response == expected_response

            mock_send.assert_called_once_with(
                adapter,
                mock_request,
                verify=True,
                timeout=expected_timeout.total_seconds(),
            )

            assert mock_request.headers["X-Correlation-ID"] == expected_correlation_id

    def test_adapter_request_error(self) -> None:
        with patch.object(
            requests.adapters.HTTPAdapter, "send", autospec=True
        ) as mock_send:
            mock_send.side_effect = requests.RequestException("request failed")
            expected_timeout = timedelta(seconds=30)
            adapter = SessionManager._Adapter(timeout=expected_timeout.total_seconds())  # noqa: SLF001 - Private access for testing

            mock_request = Mock()
            mock_request.headers = {}

            set_correlation_id(
                full_id="test-correlation-id-long", short_id="test-correlation-id"
            )

            with pytest.raises(requests.RequestException, match="request failed"):
                adapter.send(mock_request)
