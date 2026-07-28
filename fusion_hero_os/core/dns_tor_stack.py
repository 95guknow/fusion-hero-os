"""
Fusion dual-stack DNS: Clearnet + Tailscale + Tor (.onion).

Listens on 127.0.0.1:5353 (configurable). Routes:
  - *.onion  → Tor DNSPort (default 127.0.0.1:5354)
  - else     → clearnet upstreams (Quad9 / Cloudflare)

Requires Tor running with DNSPort (see ~/.fusion/tor/torrc).

Geltung: Spezifikation · Tor optional · not a crime toolkit
Policy: pseudo_inhouse_only · freemium=false
"""
from __future__ import annotations

import json
import os
import socket
import struct
import sys
import threading
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

__all__ = ["load_config", "status", "serve", "resolve_once", "start_tor_if_possible"]


def load_config() -> dict[str, Any]:
    path = ROOT / "dns_tor_stack.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _cfg() -> dict[str, Any]:
    return load_config()


def _tor_data() -> Path:
    p = Path.home() / ".fusion" / "tor"
    p.mkdir(parents=True, exist_ok=True)
    (p / "data").mkdir(exist_ok=True)
    return p


def find_tor_exe() -> str | None:
    env = os.getenv("FUSION_TOR_EXE", "").strip()
    if env and Path(env).is_file():
        return env
    candidates = [
        Path.home() / "Desktop" / "Tor Browser" / "Browser" / "TorBrowser" / "Tor" / "tor.exe",
        Path.home() / "OneDrive" / "Desktop" / "Tor Browser" / "Browser" / "TorBrowser" / "Tor" / "tor.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Tor Browser"
        / "Browser"
        / "TorBrowser"
        / "Tor"
        / "tor.exe",
        Path(r"C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe"),
        Path(r"C:\Program Files (x86)\Tor Browser\Browser\TorBrowser\Tor\tor.exe"),
        Path(r"C:\Users\Admin\OneDrive\Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def start_tor_if_possible() -> dict[str, Any]:
    """Start system Tor with Fusion torrc if not already listening on DNSPort."""
    cfg = _cfg()
    tor_c = cfg.get("tor") or {}
    dns_port = int(tor_c.get("dns_port") or 5354)
    socks_port = int(tor_c.get("socks_port") or 9050)
    if _port_open("127.0.0.1", dns_port, udp=True) or _port_open("127.0.0.1", socks_port):
        return {
            "ok": True,
            "already_running": True,
            "dns_port": dns_port,
            "socks_port": socks_port,
            "dns_udp": _port_open("127.0.0.1", dns_port, udp=True),
            "socks": _port_open("127.0.0.1", socks_port),
        }

    exe = find_tor_exe()
    if not exe:
        return {
            "ok": False,
            "error": "tor.exe not found — install Tor Browser (winget TorProject.TorBrowser)",
        }

    data = _tor_data()
    torrc = data / "torrc"
    if not torrc.is_file():
        # copy from repo template if present, else write built-in default
        repo_rc = ROOT / "configs" / "torrc"
        template = Path.home() / ".fusion" / "tor" / "torrc"
        if not template.is_file():
            if repo_rc.is_file():
                template.write_text(repo_rc.read_text(encoding="utf-8"), encoding="utf-8")
            else:
                template.write_text(
                    f"""SocksPort 127.0.0.1:{socks_port}
DNSPort 127.0.0.1:{dns_port}
ControlPort 127.0.0.1:{int(tor_c.get('control_port') or 9051)}
CookieAuthentication 1
AutomapHostsOnResolve 1
AutomapHostsSuffixes .onion,.exit
ClientOnly 1
AvoidDiskWrites 1
""",
                    encoding="utf-8",
                )
        torrc = template

    log = data / "tor.log"
    try:
        import subprocess

        creation = 0
        if sys.platform.startswith("win"):
            creation = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        proc = subprocess.Popen(
            [
                exe,
                "-f",
                str(torrc),
                "DataDirectory",
                str(data / "data"),
                "SocksPort",
                f"127.0.0.1:{socks_port}",
                "DNSPort",
                f"127.0.0.1:{dns_port}",
            ],
            stdout=open(log, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            creationflags=creation,
        )
        # wait bootstrap briefly
        for _ in range(45):
            time.sleep(1)
            if _port_open("127.0.0.1", dns_port, udp=True) or _port_open(
                "127.0.0.1", socks_port
            ):
                return {
                    "ok": True,
                    "started": True,
                    "pid": proc.pid,
                    "exe": exe,
                    "dns_port": dns_port,
                    "socks_port": socks_port,
                    "dns_udp": _port_open("127.0.0.1", dns_port, udp=True),
                    "socks": _port_open("127.0.0.1", socks_port),
                    "log": str(log),
                }
        return {
            "ok": _port_open("127.0.0.1", socks_port),
            "started": True,
            "pid": proc.pid,
            "exe": exe,
            "dns_port": dns_port,
            "socks_port": socks_port,
            "warn": "DNSPort not open yet — still bootstrapping (check tor.log)",
            "log": str(log),
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200], "exe": exe}


def _port_open(host: str, port: int, *, udp: bool = False) -> bool:
    """TCP connect check, or UDP probe for DNS ports."""
    if not udp:
        try:
            with socket.create_connection((host, port), timeout=0.4):
                return True
        except OSError:
            return False
    # UDP: send minimal DNS query and expect any response/error that is not timeout
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.6)
    try:
        # empty-ish A query for "."
        q = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01"
        sock.sendto(q, (host, port))
        sock.recvfrom(512)
        return True
    except TimeoutError:
        return False
    except OSError:
        return False
    finally:
        sock.close()


def _parse_qname(data: bytes, offset: int) -> tuple[str, int]:
    labels = []
    jumped = False
    origin = offset
    seen = 0
    while True:
        if offset >= len(data) or seen > 50:
            break
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if (length & 0xC0) == 0xC0:
            if offset + 1 >= len(data):
                break
            ptr = struct.unpack("!H", data[offset : offset + 2])[0] & 0x3FFF
            if not jumped:
                origin = offset + 2
            offset = ptr
            jumped = True
            seen += 1
            continue
        offset += 1
        raw = data[offset : offset + length]
        try:
            labels.append(raw.decode("idna"))
        except Exception:
            labels.append(raw.decode("ascii", errors="ignore") or "x")
        offset += length
        seen += 1
    name = ".".join(labels).lower()
    return name, (origin if jumped else offset)


def _encode_name(name: str) -> bytes:
    out = bytearray()
    for label in name.rstrip(".").split("."):
        if not label:
            continue
        try:
            b = label.encode("idna")
        except Exception:
            b = label.encode("ascii", errors="ignore")
        out.append(len(b))
        out.extend(b)
    out.append(0)
    return bytes(out)


def _build_query(name: str, qtype: int = 1) -> bytes:
    # standard A/AAAA query — DNS header is 12 bytes total
    tid = os.urandom(2)
    # flags RD=1, qdcount=1, ancount=0, nscount=0, arcount=0
    header = tid + struct.pack("!HHHHH", 0x0100, 1, 0, 0, 0)
    return header + _encode_name(name) + struct.pack("!HH", qtype, 1)


def _forward_udp(query: bytes, host: str, port: int, timeout: float = 3.0) -> bytes | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(query, (host, port))
        data, _ = sock.recvfrom(4096)
        return data
    except OSError:
        return None
    finally:
        sock.close()


def resolve_once(name: str, qtype: int = 1) -> dict[str, Any]:
    """Resolve one name; route .onion to Tor DNSPort."""
    cfg = _cfg()
    name = name.strip(".").lower()
    tor_c = cfg.get("tor") or {}
    ups = list(cfg.get("clearnet_upstream") or ["9.9.9.9", "1.1.1.1"])
    query = _build_query(name, qtype)

    if name.endswith(".onion"):
        th = tor_c.get("dns_host") or "127.0.0.1"
        tp = int(tor_c.get("dns_port") or 5354)
        if not _port_open(th, tp):
            return {"ok": False, "name": name, "via": "tor_dnsport", "error": "tor_dns_down"}
        resp = _forward_udp(query, th, tp, timeout=8.0)
        return {
            "ok": bool(resp),
            "name": name,
            "via": "tor_dnsport",
            "bytes": len(resp) if resp else 0,
            "upstream": f"{th}:{tp}",
        }

    for u in ups:
        if not isinstance(u, str) or u.startswith("http"):
            continue
        resp = _forward_udp(query, u, 53, timeout=2.5)
        if resp:
            return {"ok": True, "name": name, "via": "clearnet", "upstream": u, "bytes": len(resp)}
    return {"ok": False, "name": name, "via": "clearnet", "error": "all_upstream_failed"}


def _handle_query(data: bytes, addr, sock: socket.socket) -> None:
    if len(data) < 12:
        return
    try:
        qname, off = _parse_qname(data, 12)
        if off + 4 > len(data):
            return
        qtype, _qclass = struct.unpack("!HH", data[off : off + 4])
    except Exception:
        return

    cfg = _cfg()
    tor_c = cfg.get("tor") or {}
    ups = [u for u in (cfg.get("clearnet_upstream") or ["9.9.9.9", "1.1.1.1"]) if isinstance(u, str) and not u.startswith("http")]

    resp = None
    if qname.endswith(".onion") or qname.endswith(".exit"):
        th = tor_c.get("dns_host") or "127.0.0.1"
        tp = int(tor_c.get("dns_port") or 8853)
        resp = _forward_udp(data, th, tp, timeout=12.0)
    else:
        # clearnet; MagicDNS remains OS/Tailscale-side
        for u in ups:
            resp = _forward_udp(data, u, 53, timeout=2.5)
            if resp and len(resp) >= 12:
                break

    if not resp:
        # SERVFAIL
        flags = 0x8182
        resp = data[:2] + struct.pack("!HHHH", flags, 1, 0, 0) + data[12:]
    else:
        out = bytearray(resp)
        out[0:2] = data[0:2]
        resp = bytes(out)
    try:
        sock.sendto(resp, addr)
    except OSError:
        pass


def serve(blocking: bool = True) -> dict[str, Any]:
    cfg = _cfg()
    proxy = cfg.get("local_proxy") or {}
    host = proxy.get("listen_host") or "127.0.0.1"
    port = int(proxy.get("listen_port") or 5353)

    tor_state = start_tor_if_possible()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
    except OSError as e:
        return {"ok": False, "error": f"bind {host}:{port}: {e}", "tor": tor_state}

    state = {
        "ok": True,
        "listen": f"{host}:{port}",
        "tor": tor_state,
        "started_at": datetime.now(UTC).isoformat(),
    }
    state_path = Path.home() / ".fusion" / "dns" / "dns_tor_stack.status.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def loop() -> None:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except OSError:
                break
            threading.Thread(target=_handle_query, args=(data, addr, sock), daemon=True).start()

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    if blocking:
        try:
            while t.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            sock.close()
    return state


def status() -> dict[str, Any]:
    cfg = _cfg()
    tor_c = cfg.get("tor") or {}
    proxy = cfg.get("local_proxy") or {}
    dns_port = int(tor_c.get("dns_port") or 5354)
    socks_port = int(tor_c.get("socks_port") or 9050)
    listen_port = int(proxy.get("listen_port") or 5353)
    tor_exe = find_tor_exe()
    return {
        "ok": True,
        "tor_exe": tor_exe,
        "tor_dns_open": _port_open("127.0.0.1", dns_port, udp=True),
        "tor_socks_open": _port_open("127.0.0.1", socks_port),
        "proxy_listen": f"{proxy.get('listen_host') or '127.0.0.1'}:{listen_port}",
        "proxy_open": _port_open("127.0.0.1", listen_port, udp=True),
        "clearnet_upstream": cfg.get("clearnet_upstream"),
        "routing": cfg.get("routing_table"),
        "principle": (cfg.get("principle") or "")[:200],
        "tailscale_magicdns_suffix": (cfg.get("tailscale") or {}).get("magicdns_suffix"),
    }


def configure_tailscale_dns() -> dict[str, Any]:
    """Enable accept-dns; print guidance for MagicDNS + health."""
    import subprocess

    ts = Path(r"C:\Program Files\Tailscale\tailscale.exe")
    if not ts.is_file():
        return {"ok": False, "error": "tailscale.exe missing"}
    out = {}
    try:
        r = subprocess.run(
            [str(ts), "set", "--accept-dns=true"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        out["accept_dns"] = {"rc": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except Exception as e:  # noqa: BLE001
        out["accept_dns"] = {"error": str(e)}
    try:
        r = subprocess.run([str(ts), "dns", "status"], capture_output=True, text=True, timeout=30)
        out["dns_status"] = r.stdout
    except Exception as e:  # noqa: BLE001
        out["dns_status_error"] = str(e)
    out["ok"] = True
    out["note"] = (
        "Clearnet via Fusion proxy 127.0.0.1:5353; .onion via Tor DNSPort 5354; "
        "MagicDNS *.ts.net via Tailscale. Set NIC DNS only with elevation if desired."
    )
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Fusion DNS + Tor dual-stack")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--start-tor", action="store_true")
    ap.add_argument("--serve", action="store_true", help="run local DNS proxy (blocking)")
    ap.add_argument("--resolve", default="", help="test resolve name")
    ap.add_argument("--configure-tailscale", action="store_true")
    args = ap.parse_args()

    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    if args.configure_tailscale:
        print(json.dumps(configure_tailscale_dns(), indent=2, ensure_ascii=False))
        return 0
    if args.start_tor:
        print(json.dumps(start_tor_if_possible(), indent=2, ensure_ascii=False))
        return 0
    if args.resolve:
        print(json.dumps(resolve_once(args.resolve), indent=2, ensure_ascii=False))
        return 0
    if args.serve:
        print(json.dumps(serve(blocking=True), indent=2, ensure_ascii=False))
        return 0
    # default: status + tor start attempt
    t = start_tor_if_possible()
    print(json.dumps({"tor": t, "status": status()}, indent=2, ensure_ascii=False))
    return 0 if t.get("ok") or status().get("tor_exe") else 1


if __name__ == "__main__":
    raise SystemExit(main())
