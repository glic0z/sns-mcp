# SPDX-License-Identifier: Apache-2.0
"""Thin async wrapper around the Stormshield SSLClient."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger("sns_mcp.client")


@dataclass
class SNSResponse:
    """Parsed response from an SNS CLI command.

    Attributes:
        ret: Return code from the appliance (e.g. '00a00100' for OK).
        code: Numeric return code.
        msg: Human-readable message from the appliance.
        format: Response format ('section' or 'section_line').
        data: Parsed response data as a dictionary.
        raw: Raw text output for debugging.
    """

    ret: str = ""
    code: str = ""
    msg: str = ""
    format: str = ""
    data: dict[str, list[dict[str, str]] | dict[str, str] | str] = field(default_factory=dict)
    raw: str = ""

    @property
    def is_ok(self) -> bool:
        """Check if the response indicates success."""
        return self.ret in {"00a00100", "00a01000"}

    @property
    def is_not_licensed(self) -> bool:
        """Check if the feature is not licensed."""
        return self.ret == "00b00013"

    @property
    def is_not_found(self) -> bool:
        """Check if the command/object was not found."""
        return self.ret in {"00b00001", "00b00014"}


class SNSClientProtocol(Protocol):
    """Protocol for SNS client implementations."""

    def connect(self) -> bool:
        """Connect to the SNS device."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the SNS device."""
        ...

    def send_command(self, command: str) -> SNSResponse:
        """Send a CLI command and return the parsed response."""
        ...


class CookieSSLClient:
    """This class is dynamically injected into the real SSLClient at runtime."""
    
    @staticmethod
    def _create_patched_client(
        host: str,
        port: int,
        cookie: str,
        sslverifypeer: bool,
        sslverifyhost: bool,
        timeout: int,
    ) -> Any:
        from stormshield.sns.sslclient import SSLClient, ServerError
        from xml.etree import ElementTree
        import requests

        class _PatchedSSLClient(SSLClient):
            def __init__(self, *args, **kwargs):
                self._cookie_val = kwargs.pop("cookie_val", "")
                kwargs["password"] = "DUMMY_PASSWORD"  # Bypass MissingAuth check
                kwargs["autoconnect"] = False
                super().__init__(*args, **kwargs)

            def connect(self):
                """Override connect to use the cookie instead of password."""
                self.logger.log(logging.INFO, 'Connecting to %s on port %d with cookie', self.host, self.port)

                # Inject the cookie into the session
                self.session.cookies.set("SNS_webadmin", self._cookie_val)

                # 2. Serverd session (Skip Step 1 Auth completely)
                data = {'app': self.app, 'id': 0}
                if self.credentials is not None:
                    data['reqlevel'] = self.credentials
                    
                request = self.session.post(
                    self.baseurl + '/api/auth/login',
                    data=data,
                    headers=self.headers,
                    **self.conn_options)

                self.logger.log(logging.DEBUG, request.text)

                if request.status_code == requests.codes.OK:
                    nws_node = ElementTree.fromstring(request.content)
                    ret = int(nws_node.attrib['code'])
                    msg = nws_node.attrib['msg']

                    if ret != self.SSL_SERVERD_OK:
                        # 02a00000 generally means Auth Failed/Expired in this context
                        if ret in [44040192, 205]: 
                            raise ValueError("AUTH_EXPIRED")
                        raise ServerError("ERROR: {} {}".format(ret, msg))

                    self.sessionid = nws_node.find('sessionid').text
                    self.protocol = nws_node.find('protocol').text
                    self.sessionlevel = nws_node.find('sessionlevel').text
                else:
                    raise ServerError("can't get serverd session")

        return _PatchedSSLClient(
            host=host,
            port=port,
            user="admin", # Default user, cookie dictates actual user
            cookie_val=cookie,
            sslverifypeer=sslverifypeer,
            sslverifyhost=sslverifyhost,
            timeout=timeout,
        )



class SNSClient:
    """Thin wrapper around the Stormshield SNS SSL client.

    Wraps the official stormshield.sns.sslclient.SSLClient to provide
    a consistent interface and async support via loop.run_in_executor.
    """

    def __init__(
        self,
        host: str,
        port: int = 443,
        user: str = "",
        password: str | None = None,
        cookie: str | None = None,
        sslverifyhost: bool = False,
        sslverifypeer: bool = False,
        cabundle: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize SNS client configuration.

        Args:
            host: SNS appliance hostname or IP address.
            port: HTTPS port (default 443).
            user: Authentication username.
            password: Authentication password (optional if cookie is used).
            cookie: Session cookie (optional if password is used).
            sslverifyhost: Whether to verify the SSL hostname.
            sslverifypeer: Whether to verify the SSL peer certificate.
            cabundle: Path to CA bundle PEM file.
            timeout: Command timeout in seconds.
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._cookie = cookie
        self._sslverifyhost = sslverifyhost
        self._sslverifypeer = sslverifypeer
        self._cabundle = cabundle
        self._timeout = timeout
        self._real_client: Any = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to the SNS device using the official SSL client.

        Returns:
            True if connection was successful.
        """
        try:
            from stormshield.sns.sslclient import SSLClient

            if self._cookie:
                self._real_client = CookieSSLClient._create_patched_client(
                    host=self._host,
                    port=self._port,
                    cookie=self._cookie,
                    sslverifypeer=self._sslverifypeer,
                    sslverifyhost=self._sslverifyhost,
                    timeout=self._timeout,
                )
            else:
                self._real_client = SSLClient(
                    host=self._host,
                    port=self._port,
                    user=self._user,
                    password=self._password,
                    sslverifypeer=self._sslverifypeer,
                    sslverifyhost=self._sslverifyhost,
                    timeout=self._timeout,
                    autoconnect=False,
                )
            
            self._real_client.connect()
            self._connected = True
            auth_method = "cookie" if self._cookie else "password"
            logger.info("Connected to SNS device at %s:%d using %s", self._host, self._port, auth_method)
            return True
        except ValueError as exc:
            if str(exc) == "AUTH_EXPIRED":
                logger.error("Authentication expired for %s:%d. User must re-authenticate.", self._host, self._port)
                # We raise this specific string so the executor can catch it and inform the AI
                raise ValueError("AUTH_EXPIRED") from exc
            return False
        except ImportError:
            logger.warning("stormshield.sns.sslclient not available — running in mock/test mode")
            self._connected = False
            return False
        except Exception as exc:
            logger.error("Failed to connect to %s:%d — %s", self._host, self._port, exc)
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the SNS device."""
        if self._real_client is not None:
            import contextlib

            with contextlib.suppress(Exception):
                self._real_client.disconnect()
            self._real_client = None
        self._connected = False

    def send_command(self, command: str) -> SNSResponse:
        """Send a CLI command to the SNS device.

        Args:
            command: SNS CLI command string.

        Returns:
            Parsed SNSResponse.

        Raises:
            ConnectionError: If not connected to the device.
        """
        if self._real_client is None:
            raise ConnectionError(f"Not connected to SNS device at {self._host}")

        try:
            response = self._real_client.send_command(command)
            return SNSResponse(
                ret=getattr(response, "ret", ""),
                code=getattr(response, "code", ""),
                msg=getattr(response, "msg", ""),
                format=getattr(response, "format", ""),
                data=getattr(response, "data", {}) or {},
                raw=getattr(response, "output", ""),
            )
        except Exception as exc:
            logger.error("Command '%s' failed on %s: %s", command, self._host, exc)
            raise

    async def async_send_command(self, command: str) -> SNSResponse:
        """Async wrapper for send_command using run_in_executor.

        Args:
            command: SNS CLI command string.

        Returns:
            Parsed SNSResponse.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_command, command)
