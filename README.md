# fridgecheck

Is your refrigeration controller reachable from the internet?

In autumn 2026, attackers changed temperature setpoints on supermarket refrigeration systems across Europe. The affected controllers had their management interfaces exposed to the open internet. `fridgecheck` is a small self-audit tool that tells you whether yours is exposed too.

## What it checks

| Port | Service |
|------|---------|
| 80, 443, 8080, 8443 | Web admin panels |
| 502 | Modbus/TCP |
| 1911 | Niagara Fox |
| 21, 23, 5900 | FTP, Telnet, VNC |

For web ports it reads the landing page and flags pages that look like Danfoss, Copeland/Emerson or Dixell controllers.

## Usage

Python 3.8+, no dependencies.

```bash
python3 fridgecheck.py <your-public-ip-or-hostname>
```

Run it from **outside** the network you are testing (for example a phone hotspot), otherwise you are testing the LAN, not the internet exposure.

Example output:

```
Checking 203.0.113.10 (203.0.113.10) ...

[OPEN] 8080  HTTP panel (alt) | title: "ak-sm 850" | LOOKS LIKE: Danfoss controller

HIGH RISK: a control system interface is reachable from the internet.
Fix: remove the port forward, disable UPnP, put remote access behind a VPN with MFA.
```

Exit code is `0` when nothing is exposed and `1` otherwise, so it can run in a scheduled check.

## If it reports exposure

1. Remove the port forward on the router and disable UPnP.
2. Allow remote access only through a VPN with MFA.
3. Put refrigeration and other IoT devices on their own VLAN.
4. Change default passwords and update the controller firmware.
5. Add a temperature sensor with alerts that is independent of the controller.

## Limits

- Common TCP ports only. BACnet (UDP 47808) and vendor-specific ports are not tested.
- Vendor detection is keyword matching on the landing page. It can miss or mislabel devices.
- A clean result does not prove the system is secure. It only means these ports did not answer from where you ran it.

## Legal

Only scan systems you own or have written permission to test. Scanning third-party systems without authorisation can be a criminal offence (in Germany: §202a–c StGB).
