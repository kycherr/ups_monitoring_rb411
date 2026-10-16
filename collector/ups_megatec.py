#!/usr/bin/env python3
"""Zabbix External check: Megatec Q1 via MikroTik RAW TCP.
Usage: ups_megatec.py HOST [PORT [TIMEOUT]]
Stdout: exactly one JSON object on success. Stderr + exit 1 on failure.
Read-only: sends only Q1.
"""
import json
import re
import socket
import sys
import time

Q1 = re.compile(
    r'^\(\s*(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+'
    r'(\d+(?:\.\d+)?)\s+(\d+)\s+(\d+(?:\.\d+)?)\s+'
    r'(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+([01]{8})\s*$'
)


def parse(reply):
    match = Q1.fullmatch(reply)
    if not match:
        raise ValueError('Invalid Q1 response: ' + repr(reply[:120]))
    vin, fault, vout, load, frequency, raw_batt, temp, bits = match.groups()
    on_battery = int(bits[0] == '1')
    battery_low = int(bits[1] == '1')
    if int(load) > 200 or float(frequency) > 100:
        raise ValueError('Implausible Q1 load or frequency')
    return {
        'ups.InputVoltage': float(vin),
        'ups.OutputVoltage': float(vout),
        'ups.UpsLoad': int(load),
        'ups.UpsFreq': float(frequency),
        'ups.UpsTemp': float(temp),
        'ups.UpsStatus': ('OB' if on_battery else 'OL') + (' LB' if battery_low else ''),
        'ups.OnBattery': on_battery,
        'ups.BatteryLow': battery_low,
        'ups.BatteryRaw': round(float(raw_batt), 2),
        'ups.FaultVoltage': float(fault),
        'ups.StatusBits': bits,
    }


def query_once(host, port, deadline, window):
    """Accept only one complete, valid CR/LF-terminated Megatec frame."""
    stop = min(deadline, time.monotonic() + window)
    leftover = bytearray()
    last_bad = None
    remaining = stop - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('Q1 attempt deadline expired')
    with socket.create_connection((host, port), timeout=remaining) as sock:
        sock.settimeout(max(.05, stop - time.monotonic()))
        sock.sendall(b'Q1\r')
        while len(leftover) < 1024:
            remaining = stop - time.monotonic()
            if remaining <= 0:
                break
            sock.settimeout(remaining)
            try:
                part = sock.recv(256)
            except socket.timeout:
                break
            if not part:
                break
            leftover.extend(part)
            # Work on complete lines only. TCP may split each UART frame anywhere.
            while True:
                positions = [p for p in (leftover.find(b'\r'), leftover.find(b'\n')) if p >= 0]
                if not positions:
                    break
                end = min(positions)
                raw = bytes(leftover[:end]).strip(b'\x00 \t')
                del leftover[:end + 1]
                if not raw:
                    continue
                try:
                    line = raw.decode('ascii')
                    return parse(line)
                except (UnicodeDecodeError, ValueError) as exc:
                    last_bad = str(exc)
                    # A partial leftover serial reply/echo isn't valid: discard it.
                    continue
    raise ValueError(last_bad or 'No complete Q1 frame received')


def query(host, port, timeout):
    deadline = time.monotonic() + timeout
    last_error = None
    # A stale UART fragment can arrive from a previous TCP client connection.
    # Retry once, respecting the TOTAL timeout (default 3s; Zabbix Timeout=4).
    for attempt in range(2):
        left = deadline - time.monotonic()
        if left <= .1:
            break
        window = left if attempt else min(left, max(.4, left * .55))
        try:
            return query_once(host, port, deadline, window)
        except (OSError, ValueError, TimeoutError) as exc:
            last_error = exc
        if attempt == 0 and deadline - time.monotonic() > .25:
            time.sleep(.15)
    raise RuntimeError(f'No valid Q1 after retries: {last_error}')


def main():
    if not 2 <= len(sys.argv) <= 4:
        raise ValueError('Usage: ups_megatec.py HOST [PORT [TIMEOUT]]')
    host = sys.argv[1].strip()
    if not host or any(c.isspace() for c in host):
        raise ValueError('Invalid host')
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else 9999
    timeout = float(sys.argv[3]) if len(sys.argv) >= 4 else 3.0
    if not (1 <= port <= 65535 and .5 <= timeout <= 20):
        raise ValueError('Port or timeout out of range')
    result = query(host, port, timeout)
    print(json.dumps(result, separators=(',', ':'), ensure_ascii=True))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TimeoutError, RuntimeError) as exc:
        print('UPS ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
