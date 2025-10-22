"""Network probe routines."""
from __future__ import annotations

import asyncio
import ssl
import contextlib
from datetime import datetime
from time import perf_counter
from typing import List, Optional

from .schemas import TargetSpec, TargetStatus


class ProbeRunner:
    def __init__(self, concurrency: int = 3) -> None:
        self._sem = asyncio.Semaphore(concurrency)

    async def probe_all(self, targets: List[TargetSpec]) -> List[TargetStatus]:
        results = await asyncio.gather(
            *[self._probe_with_sem(target) for target in targets], return_exceptions=False
        )
        return results

    async def _probe_with_sem(self, target: TargetSpec) -> TargetStatus:
        async with self._sem:
            return await probe_target(target)


async def probe_target(target: TargetSpec) -> TargetStatus:
    tcp_ms: Optional[float] = None
    tls_ms: Optional[float] = None
    http_ms: Optional[float] = None
    note: Optional[str] = None
    code = "unknown"
    up = False
    ssl_context = None
    if target.use_tls:
        ssl_context = ssl.create_default_context()
        if target.sni:
            ssl_context.check_hostname = True
    host = target.host
    port = target.port
    reader = writer = None
    start = perf_counter()
    try:
        connect_task = asyncio.open_connection(host, port, ssl=ssl_context, server_hostname=target.sni or host if ssl_context else None)
        reader, writer = await asyncio.wait_for(connect_task, timeout=target.timeout)
        tcp_ms = (perf_counter() - start) * 1000
        if target.use_tls:
            tls_ms = tcp_ms
            cert = writer.get_extra_info("peercert")
            if cert:
                cn = _extract_cn(cert)
                expiry = _extract_expiry(cert)
                details = []
                if cn:
                    details.append(f"CN={cn}")
                if expiry:
                    details.append(f"exp={expiry}")
                if details:
                    note = ", ".join(details)
        if target.http_path:
            http_start = perf_counter()
            request = _build_head_request(target)
            writer.write(request)
            await writer.drain()
            header_bytes = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=target.timeout)
            http_ms = (perf_counter() - http_start) * 1000
            status_line = header_bytes.split(b"\r\n", 1)[0].decode(errors="ignore")
            status_code = int(status_line.split()[1])
            if 400 <= status_code < 500:
                code = "http_4xx"
            elif 500 <= status_code < 600:
                code = "http_5xx"
            else:
                code = "success"
                up = True
        else:
            code = "success"
            up = True
    except asyncio.TimeoutError:
        code = "tcp_timeout"
    except ConnectionRefusedError:
        code = "tcp_refused"
    except ssl.SSLError:
        code = "tls_fail"
    except Exception as exc:  # pragma: no cover - defensive
        code = "unknown"
        note = str(exc)
    finally:
        if writer is not None:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
    if not up and code in {"tcp_timeout", "tcp_refused", "tls_fail"}:
        if await _has_arp_entry(host):
            code = "l2_present_l3_blocked"
    return TargetStatus(
        name=target.name,
        up=up,
        code=code,
        tcp_ms=tcp_ms,
        tls_ms=tls_ms,
        http_ms=http_ms,
        note=note,
    )


def _build_head_request(target: TargetSpec) -> bytes:
    host_header = target.sni or target.host
    path = target.http_path or "/"
    lines = [
        f"HEAD {path} HTTP/1.1",
        f"Host: {host_header}",
        "User-Agent: GPING-NEXT/1.0",
        "Connection: close",
        "",
        "",
    ]
    return "\r\n".join(lines).encode()


async def _has_arp_entry(host: str) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _check_arp_sync, host)


def _check_arp_sync(host: str) -> bool:
    import subprocess

    commands = [["arp", "-a"], ["ip", "neigh"]]
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and host in result.stdout:
                return True
        except Exception:
            continue
    return False


def _extract_cn(cert: dict) -> Optional[str]:
    subject = cert.get("subject", [])
    for attrs in subject:
        for key, value in attrs:
            if key == "commonName":
                return value
    return None


def _extract_expiry(cert: dict) -> Optional[str]:
    expiry = cert.get("notAfter")
    if not expiry:
        return None
    try:
        parsed = datetime.strptime(expiry, "%b %d %H:%M:%S %Y %Z")
        return parsed.date().isoformat()
    except Exception:
        return expiry


__all__ = ["ProbeRunner", "probe_target"]
