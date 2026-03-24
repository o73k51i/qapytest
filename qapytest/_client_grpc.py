"""Module providing a gRPC client with comprehensive logging."""

import json
import logging
import os
import socket
import ssl
import time
from typing import Any

from qapytest._config import AnyType

os.environ.setdefault("GRPC_DNS_RESOLVER", "native")

try:
    import grpc
    from grpc_requests import Client as ReflectionClient
    from grpc_requests import StubClient
except ImportError as e:
    msg = "The 'grpc' package is required to use gRPC client. Install it with: pip install \"qapytest[grpc]\""
    raise ImportError(msg) from e


def _get_server_certificate(host: str, port: int) -> bytes:
    """Fetch the server certificate without verification."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    context.set_alpn_protocols(["h2"])
    with (
        socket.create_connection((host, port)) as sock,
        context.wrap_socket(sock, server_hostname=host) as ssock,
    ):
        cert = ssock.getpeercert(binary_form=True)
        if not cert:
            raise ValueError(f"Could not get certificate for {host}:{port}")
    return ssl.DER_cert_to_PEM_cert(cert).encode("utf-8")


class GrpcClient:
    """Client for convenient interaction with gRPC APIs.

    This client supports both reflection (automatic discovery of services/methods)
    and compiled stubs without reflection. It adds automatic and structured logging
    for each request and response, similar to `HttpClient`.

    Args:
        base_url: gRPC server address (e.g., 'localhost:50051').
        pb2_modules: List of compiled pb2 modules. If provided, the client will
                     work without reflection using these compiled definitions.
                     Otherwise, it will attempt to use ServerReflection.
        timeout: Default timeout in seconds for all requests. Default is 10.0.
        name_logger: Name of the logger to use. Default is "GrpcClient".
        enable_log: Whether to log requests and responses. Default is True.
        verify: Verify SSL certificates. If False, bypasses validation like
                `grpcurl -insecure`. Default is True.
        **kwargs: Additional arguments passed to the underlying `grpc_requests.Client`.

    ---
    ### Example usage:

    ```python
    # 1. With Reflection:
    client = GrpcClient("localhost:50051")
    response = client.request("helloworld.Greeter", "SayHello", {"name": "QA"})
    print(response)

    # 2. Without Reflection (with compiled python stubs):
    import helloworld_pb2
    client_stub = GrpcClient("localhost:50051", pb2_modules=[helloworld_pb2])
    response = client_stub.request("helloworld.Greeter", "SayHello", {"name": "QA"})
    print(response)
    ```
    """

    def __init__(
        self,
        base_url: str,
        pb2_modules: list[AnyType] | None = None,
        timeout: float = 10.0,
        name_logger: str = "GrpcClient",
        enable_log: bool = True,
        verify: bool = True,
        **kwargs,
    ) -> None:
        """Constructor for GrpcClient."""
        for name in ("grpc_requests", "grpc", "grpc_requests.client"):
            logging.getLogger(name).setLevel(logging.WARNING)

        self._logger = logging.getLogger(name_logger)
        self.base_url = base_url
        self.timeout = timeout
        self.enable_log = enable_log

        if not verify:
            parts = base_url.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 443
            try:
                pem = _get_server_certificate(host, port)
                kwargs["ssl"] = True
                if "credentials" not in kwargs:
                    kwargs["credentials"] = {}
                kwargs["credentials"]["root_certificates"] = pem
            except Exception as e:
                self._logger.warning(f"Failed to fetch certificate for verify=False: {e}")

        if pb2_modules:
            service_descriptors = []
            for item in pb2_modules:
                if hasattr(item, "DESCRIPTOR"):
                    service_descriptors.extend(item.DESCRIPTOR.services_by_name.values())
                else:
                    service_descriptors.append(item)
            self._client = StubClient(base_url, service_descriptors=service_descriptors, **kwargs)
            self._is_reflection = False
        else:
            self._client = ReflectionClient(base_url, **kwargs)
            self._is_reflection = True

    def _log_request(self, service: str, method: str, data: dict[str, Any] | None) -> None:
        """Log details of the gRPC request."""
        self._logger.info(f"Sending gRPC request to: {self.base_url} [{service}/{method}]")
        self._logger.debug(f"Request body (JSON): {json.dumps(data or {}, ensure_ascii=False)}")

    def _log_response(self, response: dict[str, Any] | AnyType, elapsed: float) -> None:
        """Log details of the successful gRPC response."""
        self._logger.info("Response status: OK")
        self._logger.info(f"Response time: {elapsed:.3f} s")
        try:
            body_to_log = response if isinstance(response, dict | list) else str(response)
            self._logger.debug(f"Response body (JSON): {json.dumps(body_to_log, ensure_ascii=False)}")
        except TypeError:
            self._logger.debug(f"Response body (raw): {response}")

    def _log_error(self, e: grpc.RpcError, elapsed: float) -> None:
        """Log details of the gRPC error."""
        code = e.code().name if hasattr(e.code(), "name") else e.code()
        details = e.details() if hasattr(e, "details") else str(e)
        self._logger.info(f"Response status: ERROR ({code})")
        self._logger.info(f"Response time: {elapsed:.3f} s")
        self._logger.error(f"Response error details: {details}")

    def request(
        self,
        service: str,
        method: str,
        data: dict[str, Any] | list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> dict[str, Any] | AnyType:
        """Perform a gRPC request with logging.

        Args:
            service: Name of the service.
            method: Name of the method to call.
            data: Dictionary representing the request body. Default is None.
            **kwargs: Additional metadata or options for the request.

        Returns:
            Dictionary representing the response body from unary response or iterable/generator for streams.

        Raises:
            grpc.RpcError: If the gRPC request fails with a non-OK status.
        """
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        if self.enable_log:
            self._log_request(service, method, data)

        start_time = time.monotonic()
        try:
            response = self._client.request(service, method, request=data, **kwargs)
            elapsed = time.monotonic() - start_time
            if self.enable_log:
                self._log_response(response, elapsed)
            return response
        except grpc.RpcError as e:
            elapsed = time.monotonic() - start_time
            if self.enable_log:
                self._log_error(e, elapsed)
            raise e.with_traceback(None) from None
        except Exception as e:
            elapsed = time.monotonic() - start_time
            if self.enable_log:
                self._logger.info("Response status: ERROR (INTERNAL)")
                self._logger.info(f"Response time: {elapsed:.3f} s")
                self._logger.error(f"Response error details: {e}")
            raise e.with_traceback(None) from None

    @property
    def channel(self) -> AnyType:
        """Get the underlying gRPC channel."""
        return self._client.channel

    def close(self) -> None:
        """Close the underlying gRPC channel."""
        if hasattr(self.channel, "close"):
            self.channel.close()

    def __enter__(self) -> "GrpcClient":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: AnyType | None,
    ) -> None:
        """Context manager exit."""
        self.close()
