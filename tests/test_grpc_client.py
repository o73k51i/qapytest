import logging
from collections.abc import Generator
from typing import ClassVar
from unittest.mock import MagicMock, patch

import grpc
import pytest

from qapytest._client_grpc import GrpcClient


@pytest.fixture
def mock_reflection_client() -> Generator[MagicMock, None, None]:
    with patch("qapytest._client_grpc.ReflectionClient") as mock:
        yield mock


@pytest.fixture
def mock_stub_client() -> Generator[MagicMock, None, None]:
    with patch("qapytest._client_grpc.StubClient") as mock:
        yield mock


class DummyDescriptor:
    services_by_name: ClassVar[dict[str, str]] = {"DummyService": "dummy_descriptor"}


class DummyPb2Module:
    DESCRIPTOR = DummyDescriptor()


def test_grpc_client_init_reflection(mock_reflection_client: MagicMock) -> None:
    client = GrpcClient(base_url="localhost:50051")

    assert client.base_url == "localhost:50051"
    assert client.timeout == 10.0
    assert client.enable_log is True
    assert client._is_reflection is True  # noqa: SLF001
    mock_reflection_client.assert_called_once_with("localhost:50051")


def test_grpc_client_init_stub(mock_stub_client: MagicMock) -> None:
    pb2_module = DummyPb2Module()
    client = GrpcClient(base_url="localhost:50051", pb2_modules=[pb2_module])

    assert client._is_reflection is False  # noqa: SLF001
    mock_stub_client.assert_called_once_with(
        "localhost:50051",
        service_descriptors=["dummy_descriptor"],
    )


def test_grpc_client_request_success(mock_reflection_client: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    instance_mock = mock_reflection_client.return_value
    instance_mock.request.return_value = {"message": "Hello QA"}

    client = GrpcClient(base_url="localhost:50051", name_logger="TestGrpcClient")

    with caplog.at_level(logging.DEBUG, logger="TestGrpcClient"):
        response = client.request("helloworld.Greeter", "SayHello", {"name": "QA"})

    assert response == {"message": "Hello QA"}
    instance_mock.request.assert_called_once_with(
        "helloworld.Greeter",
        "SayHello",
        request={"name": "QA"},
        timeout=10.0,
    )

    # Assert logs
    assert "Sending gRPC request to: localhost:50051 [helloworld.Greeter/SayHello]" in caplog.text
    assert "Response status: OK" in caplog.text
    assert "Response time:" in caplog.text


def test_grpc_client_request_grpc_error(mock_reflection_client: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    instance_mock = mock_reflection_client.return_value

    # Mock RpcError
    rpc_error = grpc.RpcError()
    rpc_error.code = MagicMock(return_value=grpc.StatusCode.NOT_FOUND)
    rpc_error.details = MagicMock(return_value="Service not found")
    instance_mock.request.side_effect = rpc_error

    client = GrpcClient(base_url="localhost:50051", name_logger="TestGrpcClient")

    with caplog.at_level(logging.INFO, logger="TestGrpcClient"), pytest.raises(grpc.RpcError):
        client.request("helloworld.Greeter", "SayHello", {})

    assert "Response status: ERROR (NOT_FOUND)" in caplog.text
    assert "Response error details: Service not found" in caplog.text


def test_grpc_client_request_generic_error(mock_reflection_client: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    instance_mock = mock_reflection_client.return_value
    instance_mock.request.side_effect = ValueError("Some internal error")

    client = GrpcClient(base_url="localhost:50051", name_logger="TestGrpcClient")

    with caplog.at_level(logging.INFO, logger="TestGrpcClient"), pytest.raises(ValueError, match="Some internal error"):
        client.request("helloworld.Greeter", "SayHello", {})

    assert "Response status: ERROR (INTERNAL)" in caplog.text
    assert "Response error details: Some internal error" in caplog.text


def test_grpc_client_logging_disabled(mock_reflection_client: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    instance_mock = mock_reflection_client.return_value
    instance_mock.request.return_value = {"message": "Hello QA"}

    client = GrpcClient(base_url="localhost:50051", enable_log=False, name_logger="TestGrpcClient")

    with caplog.at_level(logging.DEBUG, logger="TestGrpcClient"):
        client.request("helloworld.Greeter", "SayHello", {"name": "QA"})

    assert caplog.text == ""  # No logs should be produced


def test_grpc_channel_property(mock_reflection_client: MagicMock) -> None:
    instance_mock = mock_reflection_client.return_value
    instance_mock.channel = "mock_channel"

    client = GrpcClient(base_url="localhost:50051")
    assert client.channel == "mock_channel"
