"""Inventory collection using CIM where available."""
from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

from .schemas import InventoryPayload


def gather_inventory(store: str) -> InventoryPayload:
    bios = _query_cim("Win32_BIOS")
    system = _query_cim("Win32_ComputerSystem")
    printers = _query_list("Win32_Printer", ["Name", "PortName"])
    monitor = _query_single("WmiMonitorID")
    nics = _query_list("Win32_NetworkAdapter", ["Name", "MACAddress"])
    if not bios:
        bios = {
            "serial": _safe(platform.node()),
            "version": _safe(platform.version()),
        }
    if not system:
        system = {
            "make": _safe(platform.system()),
            "model": _safe(platform.machine()),
        }
    return InventoryPayload(
        ts=datetime.utcnow(),
        store=store,
        bios=bios,
        system=system,
        printers=printers,
        monitor=monitor or {},
        nics=nics,
    )


def _query_cim(class_name: str) -> Optional[Dict[str, Optional[str]]]:
    data = _run_powershell(
        f"Get-CimInstance -ClassName {class_name} | Select-Object -First 1 | ConvertTo-Json"
    )
    if not data:
        return None
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return None
    result: Dict[str, Optional[str]] = {}
    for key in ("SerialNumber", "SMBIOSBIOSVersion", "Manufacturer", "Model"):
        if key in parsed:
            mapped = key.lower()
            result[mapped] = parsed.get(key)
    if result:
        rename = {
            "serialnumber": "serial",
            "smbiosbiosversion": "version",
        }
        output = {}
        for key, value in result.items():
            key = rename.get(key, key)
            output[key] = value
        return output
    return None


def _query_list(class_name: str, fields: List[str]) -> List[Dict[str, Optional[str]]]:
    select_fields = ",".join(fields)
    data = _run_powershell(
        f"Get-CimInstance -ClassName {class_name} | Select-Object {select_fields} | ConvertTo-Json"
    )
    if not data:
        return []
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, dict):
        parsed = [parsed]
    results = []
    for row in parsed:
        entry: Dict[str, Optional[str]] = {}
        for field in fields:
            entry[field.lower()] = row.get(field)
        results.append(entry)
    return results


def _query_single(class_name: str) -> Optional[Dict[str, Optional[str]]]:
    data = _run_powershell(
        f"Get-CimInstance -Namespace root/WMI -ClassName {class_name} | Select-Object -First 1 | ConvertTo-Json"
    )
    if not data:
        return None
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return None
    output: Dict[str, Optional[str]] = {}
    for field in ("ManufacturerName", "UserFriendlyName", "SerialNumber"):
        if field in parsed:
            output[field.replace("Name", "").lower() or field.lower()] = parsed.get(field)
    return output or None


def _run_powershell(script: str) -> Optional[str]:
    commands = [["pwsh", "-NoProfile", "-Command", script], ["powershell", "-NoProfile", "-Command", script]]
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except FileNotFoundError:
            continue
        except Exception:
            return None
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    return None


def _safe(value: str) -> str:
    return value or "unknown"


__all__ = ["gather_inventory"]
