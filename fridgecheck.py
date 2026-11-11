#!/usr/bin/env python3
"""fridgecheck - is your refrigeration controller reachable from the internet?

Run it from OUTSIDE the network (e.g. phone hotspot) against your own public IP.
Only scan systems you own or have written permission to test.

Usage: python3 fridgecheck.py <public-ip-or-hostname>
"""
import re
import socket
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor

PORTS = {
    21: "FTP",
    23: "Telnet",
    80: "HTTP panel",
    443: "HTTPS panel",
    502: "Modbus/TCP (no authentication by design)",
    1911: "Niagara Fox (building automation)",
    5900: "VNC remote screen",
    8080: "HTTP panel (alt)",
    8443: "HTTPS panel (alt)",
}
WEB_PORTS = {80: False, 8080: False, 443: True, 8443: True}
VENDOR_HINTS = {
    "Danfoss": ["danfoss", "ak-sm", "ak-sc"],
    "Copeland / Emerson": ["copeland", "emerson", "e2 ", "e3 ", "site supervisor"],
    "Dixell": ["dixell", "xweb"],
}
TIMEOUT = 3


def is_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT):
            return True
    except OSError:
        return False


def fetch_page(host, port, tls):
    """Return the first bytes of the landing page, lowercased, or ''."""
    try:
        sock = socket.create_connection((host, port), timeout=TIMEOUT)
        if tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE  # controllers use self-signed certs
            sock = ctx.wrap_socket(sock, server_hostname=host)
        with sock:
            req = f"GET / HTTP/1.0\r\nHost: {host}\r\nUser-Agent: fridgecheck\r\n\r\n"
            sock.sendall(req.encode())
            data = b""
            while len(data) < 16384:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
        return data.decode("latin-1", "replace").lower()
    except OSError:
        return ""


def identify(page):
    for vendor, hints in VENDOR_HINTS.items():
        if any(h in page for h in hints):
            return vendor
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    host = sys.argv[1]
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        sys.exit(f"Cannot resolve {host}")

    print(f"Checking {host} ({ip}) ...\n")
    with ThreadPoolExecutor(max_workers=len(PORTS)) as pool:
        results = dict(zip(PORTS, pool.map(lambda p: is_open(ip, p), PORTS)))

    exposed = [p for p, ok in results.items() if ok]
    vendor_found = False
    for port in exposed:
        line = f"[OPEN] {port:<5} {PORTS[port]}"
        if port in WEB_PORTS:
            page = fetch_page(ip, port, WEB_PORTS[port])
            title = re.search(r"<title>(.*?)</title>", page, re.S)
            vendor = identify(page)
            if title:
                line += f' | title: "{title.group(1).strip()[:60]}"'
            if vendor:
                vendor_found = True
                line += f" | LOOKS LIKE: {vendor} controller"
        print(line)

    print()
    if not exposed:
        print("OK: none of the checked ports answer from here.")
        print("Note: this only covers common TCP ports. BACnet (UDP 47808) is not tested.")
        return
    if vendor_found or 502 in exposed or 1911 in exposed:
        print("HIGH RISK: a control system interface is reachable from the internet.")
    else:
        print("REVIEW: services are reachable from the internet. Confirm each one is intended.")
    print("Fix: remove the port forward, disable UPnP, put remote access behind a VPN with MFA.")
    sys.exit(1)


if __name__ == "__main__":
    main()
