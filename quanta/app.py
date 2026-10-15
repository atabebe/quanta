# =============================================================================
# QTMS  –  Quantum Transport Measurement Systems
# Standalone Desktop App  (FastAPI backend + pywebview window)
# =============================================================================
# Run:   python app.py
# Build: pyinstaller --onefile --windowed --name QTMS app.py
# =============================================================================

import threading
import time
import webbrowser
import sys
import os
import base64
import zlib
import socket

# ── Windows-safe console encoding ────────────────────────────────────────────
# On Windows, sys.stdout / sys.stderr default to cp1252 (the legacy ANSI
# codepage). Any log message containing Unicode characters like → ± — Ω °
# (which we use throughout phase messages) triggers
#   UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'
# Reconfiguring to UTF-8 with errors='replace' makes logging safe — any
# character the console truly can't display becomes '?' but the app never
# crashes. Wrapped in try/except so non-Windows hosts or environments where
# stdout is captured (e.g. PyInstaller --windowed) don't break.
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ── Embedded HTML (compressed, decoded at runtime) ───────────────────────────
# ── Analysis window HTML (served at /analysis) ──────────────────────────────
_ANALYSIS_B64 = (
    "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"
    "6Ezxt58M/MP/B2Jsmq0="
)

_HTML_B64 = (
    "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"
)
def _get_html() -> str:
    raw = base64.b64decode(_HTML_B64.replace('\n','').replace(' ',''))
    return zlib.decompress(raw).decode('utf-8')


def _unique_path(fpath: str) -> str:
    """Return a path that doesn't yet exist on disk.

    If `fpath` doesn't exist, returns it unchanged. If it does exist, appends
    `(1)`, `(2)`, ... before the extension until an unused name is found.

    Examples:
        sample.txt           → sample.txt              (if doesn't exist)
        sample.txt           → sample(1).txt           (if sample.txt exists)
        sample(1).txt        → sample(2).txt           (if sample(1).txt exists too)
        sample_2.000K.txt    → sample_2.000K(1).txt    (handles dots in stem correctly)

    The helper is safe against the unlikely race where someone creates the
    candidate file between the existence check and our open() — but for the
    QUANTAS single-user case this is not a real concern.
    """
    import os
    if not os.path.exists(fpath):
        return fpath
    base, ext = os.path.splitext(fpath)
    n = 1
    while True:
        candidate = f"{base}({n}){ext}"
        if not os.path.exists(candidate):
            return candidate
        n += 1
        if n > 9999:   # sanity guard against infinite loops
            raise RuntimeError(
                f"_unique_path: more than 9999 collisions for {fpath} — "
                f"clean up the save folder or change sample name."
            )


# =============================================================================
# BACKEND  –  FastAPI instrument control server
# (identical logic to main.py, served on localhost:8000)
# =============================================================================

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import asyncio
import queue
import math
import random
import numpy as np
import re
import logging
import json
import hashlib
import secrets
import zipfile
import io
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# VERSION STAMP
# =============================================================================
# Single source of truth for "which build is this?".  Printed as the FIRST log
# line at startup (see the __main__ block) so a two-second glance at the console
# tells you exactly what is running — no more counting lines of code or chasing
# a fix that lives in a copy that isn't the one actually launched.
#
# Bump this string whenever app.py changes.  Convention: v<date>-<short-label>.
# History:
#   v2026-05-18-ramp-safety-lockstep
#       RAMP-mode safety, VTI/probe lock-step at identical rates,
#       ramp_mode=ON in both directions, live-T heartbeats,
#       vti_offset -> 1.0 K with preflight check.  (app.py = 8997 lines)
APP_VERSION = "v2026-05-18-ramp-safety-lockstep"

# =============================================================================
# AUTH  –  two-tier password protection (monitor | control)
# =============================================================================

_AUTH_FILE = Path(__file__).parent / 'qtms_auth.cfg'

def _pbkdf2(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260_000)
    return dk.hex()

def _load_auth() -> dict:
    """Load auth config, creating defaults on first run."""
    if _AUTH_FILE.exists():
        try:
            return json.loads(_AUTH_FILE.read_text())
        except Exception:
            pass

    # ── First run: generate random passwords and save ─────────────────
    secret_key      = secrets.token_hex(32)
    monitor_salt    = secrets.token_hex(16)
    control_salt    = secrets.token_hex(16)
    monitor_pass    = secrets.token_urlsafe(12)
    control_pass    = secrets.token_urlsafe(12)

    cfg = {
        'secret_key'    : secret_key,
        'monitor_salt'  : monitor_salt,
        'monitor_hash'  : _pbkdf2(monitor_pass, monitor_salt),
        'control_salt'  : control_salt,
        'control_hash'  : _pbkdf2(control_pass, control_salt),
    }
    _AUTH_FILE.write_text(json.dumps(cfg, indent=2))
    _AUTH_FILE.chmod(0o600)

    print("=" * 60)
    print("  QTMS — First-run passwords (save these now)")
    print("=" * 60)
    print(f"  Monitor password : {monitor_pass}")
    print(f"  Control password : {control_pass}")
    print(f"  Auth file saved  : {_AUTH_FILE}")
    print("  To change passwords, delete qtms_auth.cfg and restart.")
    print("=" * 60)
    return cfg

_AUTH_CFG = _load_auth()

def _check_password(password: str, role: str) -> bool:
    salt = _AUTH_CFG.get(f'{role}_salt', '')
    expected = _AUTH_CFG.get(f'{role}_hash', '')
    if not salt or not expected:
        return False
    return secrets.compare_digest(_pbkdf2(password, salt), expected)

# ── Auth middleware ───────────────────────────────────────────────────────────
_CONTROL_PATHS = {'/api/start', '/api/stop', '/api/pause',
                  '/api/resume', '/api/emergency', '/api/contact_check',
                  '/api/queue_transition', '/api/warmcool', '/api/warmcool_stop'}
_PUBLIC_PATHS  = {'/login', '/api/ping'}

class _AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in _PUBLIC_PATHS:
            return await call_next(request)
        role = request.session.get('role')
        if not role:
            if path.startswith('/api/'):
                return JSONResponse(
                    {'error': 'Authentication required', 'redirect': '/login'},
                    status_code=401)
            return RedirectResponse('/login', status_code=302)
        if path in _CONTROL_PATHS and role != 'control':
            return JSONResponse({'error': 'Control access required'}, status_code=403)
        return await call_next(request)



try:
    import pyvisa
    logger.info("pyvisa loaded")
except ImportError:
    pyvisa = None
    logger.warning("pyvisa not installed – hardware SMU will not work")

try:
    import serial
    from serial.tools import list_ports
    logger.info("pyserial loaded")
except ImportError:
    serial = None
    logger.warning("pyserial not installed – hardware 2182A will not work")

try:
    import zhinst.ziPython as zi
    logger.info("zhinst loaded")
except ImportError:
    zi = None
    logger.warning("zhinst not installed – MFLI lock-in will not work (pip install zhinst)")


# ── Temperature Filter ────────────────────────────────────────────────────────
# =============================================================================
# REAL-TIME PHYSICS CALCULATORS
# =============================================================================

class MobilityCalculator:
    """Per-point Hall mobility and 2D carrier density estimator.

    Physics (2DEG / thin-film sheet geometry):
        R_H   = Rxy / B          [Ω/T ≡ m²/C]  — Hall coefficient
        n_s   = 1 / (e |R_H|)   [m⁻²]          — sheet carrier density
        μ     = |R_H| / Rxx      [m²/Vs]        — Hall mobility

    Output units are converted to cm²/Vs and cm⁻² for reporting.
    Returns None for any point where |B| < 0.01 T (avoid divergence near zero).
    """
    E_CHARGE = 1.602176634e-19  # C

    def compute(self, Rxx: float, Rxy: float, B: float):
        if abs(B) < 0.01 or Rxx == 0 or Rxy == 0:
            return None
        R_H = Rxy / B                                         # Ω/T
        n_m2 = 1.0 / (self.E_CHARGE * abs(R_H))              # m⁻²
        mu_m2 = abs(R_H) / abs(Rxx)                          # m²/Vs
        return {
            'mobility_cm2':        mu_m2 * 1e4,              # cm²/Vs
            'carrier_density_cm2': n_m2  * 1e-4,             # cm⁻²
            'hall_coefficient':    R_H,                       # m²/C
        }


class PeakDetector:
    """Rolling z-score spike detector for real-time anomaly flagging.

    Maintains a sliding window of the last `window_size` values; a new
    value is flagged as a spike if it deviates more than `threshold`
    standard deviations from the window mean.  threshold=4.0 gives ~1
    false positive per 30,000 points under Gaussian noise.
    """

    def __init__(self, window_size: int = 15, threshold: float = 4.0):
        self.window_size = window_size
        self.threshold   = threshold
        self._buf: list  = []

    def detect(self, value: float) -> bool:
        self._buf.append(value)
        if len(self._buf) > self.window_size:
            self._buf.pop(0)
        if len(self._buf) < 5:   # need a few points before judging
            return False
        arr  = self._buf[:-1]    # exclude current point from reference stats
        mean = float(np.mean(arr))
        std  = float(np.std(arr))
        if std < 1e-15:
            return False
        return abs(value - mean) > self.threshold * std

    def reset(self):
        self._buf.clear()


class TemperatureFilter:
    def __init__(self, window_size=5, spike_threshold=2.0):
        # spike_threshold in Kelvin.  Must be large enough that legitimate
        # temperature ramps are never clipped, but small enough to catch
        # real thermometer glitches (e.g. ITC comms noise, ±10s K spikes).
        # Mercury iTC thermometer noise is typically < 0.05 K, so 2.0 K gives
        # a very comfortable margin and only rejects genuine bad readings.
        self.window_size = window_size
        self.spike_threshold = spike_threshold
        self.buffer = []
        self.last_valid_temp = None

    def filter(self, new_temp):
        if new_temp <= 0:
            return self.last_valid_temp if self.last_valid_temp is not None else new_temp
        self.buffer.append(new_temp)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        if len(self.buffer) < 3:
            self.last_valid_temp = new_temp
            return new_temp
        median = float(np.median(self.buffer))
        if abs(new_temp - median) > self.spike_threshold:
            filtered = median
            if self.last_valid_temp is not None:
                if abs(filtered - self.last_valid_temp) > self.spike_threshold * 2:
                    filtered = self.last_valid_temp + np.sign(filtered - self.last_valid_temp) * self.spike_threshold
        else:
            filtered = new_temp
        self.last_valid_temp = filtered
        return filtered

    def reset(self):
        self.buffer = []
        self.last_valid_temp = None


# ── Mercury iTC ───────────────────────────────────────────────────────────────
class MercuryITC:
    def __init__(self, host, port=7020, timeout_s=2.0, logger=None):
        self.host = host.strip()
        self.port = int(port)
        self.timeout_s = float(timeout_s)
        self.logger = logger or logging.getLogger(__name__)
        self.sock = None

    def open(self):
        if self.sock: return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout_s)
        s.connect((self.host, self.port))
        self.sock = s
        time.sleep(0.1)

    def close(self):
        if self.sock:
            try: self.sock.close()
            except: pass
        self.sock = None

    def write(self, cmd):
        self.sock.sendall((cmd.strip() + "\n").encode("ascii", errors="ignore"))

    def read_line(self):
        buf = bytearray()
        start = time.time()
        while True:
            try:
                ch = self.sock.recv(1)
                if not ch: break
                buf.extend(ch)
                if ch == b"\n": break
                if time.time() - start > self.timeout_s: break
            except socket.timeout: break
        return buf.decode("ascii", errors="ignore").strip()

    def query(self, cmd):
        self.write(cmd)
        return self.read_line()

    def read_temperature(self, device):
        try:
            resp = self.query(f"READ:DEV:{device}:TEMP:SIG:TEMP")
            m = re.search(r":([0-9.+-]+)K", resp)
            if m: return float(m.group(1))
            return 0.0
        except: return 0.0

    def set_temperature_setpoint(self, sp, device):
        try: return "VALID" in self.query(f"SET:DEV:{device}:TEMP:LOOP:TSET:{sp:.3f}")
        except: return False

    def set_control_mode(self, mode, device):
        state = "ON" if mode.upper() == "AUTO" else "OFF"
        try: return "VALID" in self.query(f"SET:DEV:{device}:TEMP:LOOP:FAUT:{state}")
        except: return False

    def set_ramp_rate(self, rate, device):
        try: return "VALID" in self.query(f"SET:DEV:{device}:TEMP:LOOP:RSET:{rate:.3f}")
        except: return False

    def set_ramp_mode(self, enabled, device):
        state = "ON" if enabled else "OFF"
        try: return "VALID" in self.query(f"SET:DEV:{device}:TEMP:LOOP:RENA:{state}")
        except: return False


# ── Mercury iPS ───────────────────────────────────────────────────────────────
class MercuryIPS:
    def __init__(self, host, port=7020, timeout_s=2.0, logger=None, group="GRPZ"):
        self.host = host.strip()
        self.port = int(port)
        self.timeout_s = float(timeout_s)
        self.logger = logger or logging.getLogger(__name__)
        self.group = group.strip()
        self.sock = None
        # Single lock guards every write/read pair so that multi-axis callers
        # (vector magnet) cannot interleave SCPI traffic on the shared socket.
        self._io_lock = threading.Lock()

    def open(self):
        if self.sock: return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout_s)
        s.connect((self.host, self.port))
        self.sock = s
        time.sleep(0.1)
        self.sock.settimeout(0.1)
        try:
            while True:
                if not self.sock.recv(4096): break
        except socket.timeout: pass
        finally: self.sock.settimeout(self.timeout_s)

    def close(self):
        if self.sock:
            try: self.sock.close()
            except: pass
        self.sock = None

    def _grp(self, group): return (group or self.group).strip()

    def write(self, cmd):
        self.sock.sendall((cmd.strip() + "\n").encode("ascii", errors="ignore"))

    def read_line(self):
        buf = bytearray()
        start = time.time()
        while True:
            try:
                ch = self.sock.recv(1)
                if not ch: break
                buf.extend(ch)
                if ch == b"\n": break
                if time.time() - start > self.timeout_s: break
            except socket.timeout: break
        return buf.decode("ascii", errors="ignore").strip()

    def query(self, cmd):
        # Atomic write+read under the I/O lock so concurrent group access is safe
        with self._io_lock:
            self.write(cmd)
            return self.read_line()

    @staticmethod
    def _parse_float_unit(resp, unit):
        if not resp or "N/A" in resp: return None
        m = re.search(rf":([0-9.+-]+){re.escape(unit)}", resp)
        try: return float(m.group(1)) if m else None
        except: return None

    def read_field(self, group=None):
        try:
            resp = self.query(f"READ:DEV:{self._grp(group)}:PSU:SIG:FLD")
            v = self._parse_float_unit(resp, "T")
            return (v if v is not None else 0.0, v is not None)
        except: return 0.0, False

    def get_status(self, group=None):
        try:
            resp = self.query(f"READ:DEV:{self._grp(group)}:PSU:ACTN")
            return resp.split(":")[-1].strip().upper()
        except: return "ERROR"

    def read_switch_heater(self, group=None):
        try:
            resp = self.query(f"READ:DEV:{self._grp(group)}:PSU:SIG:SWHT")
            t = resp.split(":")[-1].strip().upper()
            return t if t in ("ON","OFF") else ""
        except: return ""

    def set_switch_heater(self, state, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:SIG:SWHN:{'ON' if state else 'OFF'}")
            return "N/A" not in resp and resp != ""
        except: return False

    def set_catch_enable(self, enabled, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:SIG:CENA:{'ON' if enabled else 'OFF'}")
            return "N/A" not in resp and resp != ""
        except: return False

    def read_catch_enable(self, group=None):
        try:
            resp = self.query(f"READ:DEV:{self._grp(group)}:PSU:SIG:CENA")
            t = resp.split(":")[-1].strip().upper()
            if t in ("ON","OFF"): return t
            if "N/A" in resp or resp == "": return "UNSUPPORTED"
            return ""
        except: return ""

    def read_detailed_status(self, group=None):
        try:
            grp = self._grp(group)
            return {
                "catch_enable": self.read_catch_enable(grp),
                "switch": self.read_switch_heater(grp),
                "mode": self.get_status(grp),
            }
        except: return {"catch_enable":"ERROR","switch":"ERROR","mode":"ERROR"}

    def set_target_field(self, field_T, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:SIG:FSET:{field_T:.5f}")
            return "N/A" not in resp and resp != ""
        except: return False

    def set_ramp_rate_field(self, rate, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:SIG:RFST:{rate:.5f}")
            return "N/A" not in resp and resp != ""
        except: return False

    def set_hold(self, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:ACTN:HOLD")
            return "N/A" not in resp and resp != ""
        except: return False

    def set_to_setpoint(self, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:ACTN:RTOS")
            return "N/A" not in resp and resp != ""
        except: return False

    def set_to_zero(self, group=None):
        try:
            resp = self.query(f"SET:DEV:{self._grp(group)}:PSU:ACTN:RTOZ")
            return "N/A" not in resp and resp != ""
        except: return False


# ── Vector-magnet helpers ─────────────────────────────────────────────────────
def spherical_to_cartesian(B_mag, theta_deg, phi_deg):
    """Convert (|B|, θ, φ) in physics convention to (Bx, By, Bz).

    Convention: θ measured from +z (c-axis). For the EuGa2.4Al1.6 measurement,
    keep φ = 0 to tilt the field into the +x direction.
    """
    th = math.radians(float(theta_deg))
    ph = math.radians(float(phi_deg))
    Bx = B_mag * math.sin(th) * math.cos(ph)
    By = B_mag * math.sin(th) * math.sin(ph)
    Bz = B_mag * math.cos(th)
    return Bx, By, Bz


def cartesian_to_spherical(Bx, By, Bz):
    """Inverse of spherical_to_cartesian. Returns (|B|, θ_deg, φ_deg)."""
    B_mag = math.sqrt(Bx*Bx + By*By + Bz*Bz)
    if B_mag < 1e-9:
        return 0.0, 0.0, 0.0
    th = math.degrees(math.acos(max(-1.0, min(1.0, Bz / B_mag))))
    ph = math.degrees(math.atan2(By, Bx))
    return B_mag, th, ph


def max_B_at_angle(theta_deg, phi_deg, Bx_max, By_max, Bz_max):
    """Largest |B| achievable at the given (θ, φ) given per-axis limits.

    Returns (max_B, limiting_axis_name).
    """
    Bx_u, By_u, Bz_u = spherical_to_cartesian(1.0, theta_deg, phi_deg)
    candidates = []
    if abs(Bx_u) > 1e-9: candidates.append((Bx_max / abs(Bx_u), "x"))
    if abs(By_u) > 1e-9: candidates.append((By_max / abs(By_u), "y"))
    if abs(Bz_u) > 1e-9: candidates.append((Bz_max / abs(Bz_u), "z"))
    if not candidates:
        return 0.0, "none"
    max_B, axis = min(candidates, key=lambda pair: pair[0])
    return max_B, axis


class VectorMagnet:
    """Coordinate three IPS groups (GRPX, GRPY, GRPZ) on the same socket.

    The class wraps an existing MercuryIPS instance and exposes vector-aware
    operations. It does not own the socket; it shares it with the MercuryIPS
    instance, which already serialises I/O via its `_io_lock`.

    The intended usage is:
      vm = VectorMagnet(ips, Bx_max=1.0, By_max=1.0, Bz_max=4.0)
      vm.set_field_xyz(0.88, 0.0, 1.80, total_time_s=2.0)
      vm.wait_at_target(0.88, 0.0, 1.80, tol=5e-4)
    """

    def __init__(self, ips, Bx_max=1.0, By_max=1.0, Bz_max=4.0):
        self.ips = ips
        self.Bx_max = float(Bx_max)
        self.By_max = float(By_max)
        self.Bz_max = float(Bz_max)
        self._logger = logging.getLogger(__name__)

    def read_field_xyz(self):
        Bx, _ = self.ips.read_field("GRPX")
        By, _ = self.ips.read_field("GRPY")
        Bz, _ = self.ips.read_field("GRPZ")
        return float(Bx), float(By), float(Bz)

    def check_within_limits(self, Bx, By, Bz):
        """Return (ok, message). Refuses targets outside per-axis envelope."""
        for v, lim, name in [(Bx, self.Bx_max, "Bx"),
                             (By, self.By_max, "By"),
                             (Bz, self.Bz_max, "Bz")]:
            if abs(v) > lim + 1e-9:
                return False, f"{name}={v:+.4f} T exceeds limit ±{lim:.4f} T"
        return True, "ok"

    def _ensure_axis_ready(self, group):
        """Ensure switch heater on and catch enabled for one group."""
        try:
            s = self.ips.read_detailed_status(group)
            if s.get("catch_enable") == "OFF":
                self.ips.set_catch_enable(True, group); time.sleep(2)
            self.ips.set_switch_heater(True, group); time.sleep(3)
        except Exception as e:
            self._logger.warning(f"VectorMagnet._ensure_axis_ready({group}): {e}")

    def set_field_xyz(self, Bx_target, By_target, Bz_target, *,
                      total_time_s=2.0, max_rate_T_per_min=0.5):
        """Time-budgeted simultaneous ramp to (Bx, By, Bz).

        Each axis's ramp rate is set so all three finish in approximately
        total_time_s seconds. Each axis is capped at max_rate_T_per_min. If
        the budget would exceed the cap on any axis, the slowest axis dictates
        the achievable transit time.
        """
        ok, msg = self.check_within_limits(Bx_target, By_target, Bz_target)
        if not ok:
            raise ValueError(f"VectorMagnet: target outside limits — {msg}")

        Bx_now, By_now, Bz_now = self.read_field_xyz()
        deltas = {
            "GRPX": abs(Bx_target - Bx_now),
            "GRPY": abs(By_target - By_now),
            "GRPZ": abs(Bz_target - Bz_now),
        }
        targets = {"GRPX": Bx_target, "GRPY": By_target, "GRPZ": Bz_target}

        # Budget rate per axis: rate = ΔB / time, with floor at 0.001 T/min and
        # ceiling at max_rate_T_per_min.
        time_min = max(1e-3, total_time_s / 60.0)
        rates = {}
        for grp, dB in deltas.items():
            r = dB / time_min
            r = min(max_rate_T_per_min, max(0.001, r))
            rates[grp] = r

        # Ensure every axis is ready, set rate + target, command go.
        for grp in ("GRPX", "GRPY", "GRPZ"):
            self._ensure_axis_ready(grp)
            try:
                self.ips.set_ramp_rate_field(rates[grp], grp); time.sleep(0.2)
                self.ips.set_target_field(targets[grp], grp);  time.sleep(0.2)
                self.ips.set_to_setpoint(grp)
            except Exception as e:
                self._logger.error(f"VectorMagnet.set_field_xyz({grp}): {e}")
                raise

    def wait_at_target(self, Bx_target, By_target, Bz_target, *,
                       tol=5e-4, timeout_s=120.0, settle_s=0.1, n_stable=3):
        """Block until all three axes are within tol of their targets for
        n_stable consecutive readings, or timeout. Returns the actual
        (Bx, By, Bz) at exit and a settled-flag.
        """
        start = time.time()
        stable = 0
        while True:
            Bx, By, Bz = self.read_field_xyz()
            errs = (abs(Bx - Bx_target),
                    abs(By - By_target),
                    abs(Bz - Bz_target))
            if all(e <= tol for e in errs):
                stable += 1
                if stable >= n_stable:
                    # HOLD all axes at the settled value
                    for grp in ("GRPX", "GRPY", "GRPZ"):
                        try: self.ips.set_hold(grp)
                        except: pass
                    return (Bx, By, Bz, True)
            else:
                stable = 0
            if time.time() - start > timeout_s:
                self._logger.error(
                    f"VectorMagnet.wait_at_target TIMEOUT @ {time.time()-start:.0f}s — "
                    f"target=({Bx_target:+.4f},{By_target:+.4f},{Bz_target:+.4f}), "
                    f"actual=({Bx:+.4f},{By:+.4f},{Bz:+.4f}), "
                    f"errs=({errs[0]:.4f},{errs[1]:.4f},{errs[2]:.4f})")
                for grp in ("GRPX", "GRPY", "GRPZ"):
                    try: self.ips.set_hold(grp)
                    except: pass
                return (Bx, By, Bz, False)
            time.sleep(settle_s)

    def hold_all(self):
        for grp in ("GRPX", "GRPY", "GRPZ"):
            try: self.ips.set_hold(grp)
            except: pass

    def zero_all(self):
        """Ramp all three axes to zero. Does not block."""
        for grp in ("GRPX", "GRPY", "GRPZ"):
            try:
                self.ips.set_target_field(0.0, grp); time.sleep(0.1)
                self.ips.set_to_setpoint(grp)
            except: pass


# ── Serial 2182A ──────────────────────────────────────────────────────────────
class Serial2182A:
    def __init__(self, com_port, baud=9600, timeout_s=3.0, logger=None):
        self.com_port = com_port.strip()
        self.serial = None
        self.connected = False
        self._term = "\n"
        self.logger = logger or logging.getLogger(__name__)
        if serial is None:
            raise ImportError("pyserial not installed")
        self.serial = serial.Serial(
            port=self.com_port, baudrate=int(baud),
            bytesize=8, parity="N", stopbits=1,
            timeout=float(timeout_s), write_timeout=float(timeout_s),
            xonxoff=True,
        )
        self.connected = True
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

    def write(self, cmd):
        self.serial.write((cmd.strip() + self._term).encode("ascii", errors="ignore"))
        self.serial.flush()

    def query(self, cmd):
        try: self.serial.reset_input_buffer()
        except: pass
        self.write(cmd)
        line = self.serial.readline()
        if not line: raise TimeoutError(f"2182A timeout on {self.com_port}")
        return line.decode("ascii", errors="ignore").strip()

    def clear_status(self):
        try: self.write("*CLS"); time.sleep(0.02)
        except: pass

    def read_error(self):
        try: return self.query("SYST:ERR?")
        except Exception as e: return f"ERRQUERY_FAILED:{e}"

    def drain_errors(self, maxn=10):
        out = []
        for _ in range(maxn):
            s = self.read_error()
            out.append(s)
            if s.strip().startswith("0") or "No error" in s: break
        return out

    def read_voltage(self, nplc=1.0, line_freq_hz=50.0):
        try:
            self.write("INIT")
            time.sleep(max(0.02, 1.3 * (float(nplc) / float(line_freq_hz))))
            raw = self.query("FETCh?")
            return float(raw.replace("V","").replace("v","").strip())
        except Exception as e:
            self.logger.warning(f"2182A read failed: {e}")
            return float("nan")

    def close(self):
        if self.serial:
            try: self.serial.close()
            except: pass
        self.connected = False



# ── MFLI Lock-in Amplifier ────────────────────────────────────────────────────
class MFLI:
    """
    Zurich Instruments MFLI driver.

    role="master":  generates AC excitation via Signal Output 1, reads Vxx on Input 1.
                    Clock 10 MHz Out → slave Clock 10 MHz In (1 BNC cable, rear panel).
    role="slave":   locks to master 10 MHz clock, reads Vxy on Input 1, no output used.

    Wiring (MFLI_DUAL):
      DEV6568 (master)  Signal Output +V → R_series → sample I+ contact
                        Signal Input  +V / -V Diff  → Vxx contacts (differential)
                        Clock 10 MHz Out  ──BNC──▶  Clock 10 MHz In  DEV6597 (slave)
      DEV6597 (slave)   Signal Input  +V / -V Diff  → Vxy / Hall contacts (differential)

    Wiring (MFLI_SINGLE):
      DEV6568 only — Signal Output → sample, Input 1 → Vxx. Rxy = quadrature of Vxx.

    AC current:  I_ac = output_amplitude / series_resistance
    Rxx = X_master / I_ac   (in-phase longitudinal voltage / current)
    Rxy = X_slave  / I_ac   (in-phase Hall voltage / current, dual mode only)
    """

    def __init__(self, device_id, host, port,
                 frequency, output_amplitude, series_resistance,
                 time_constant, filter_order,
                 input_range, output_range,
                 settle_tc=5, role="master", logger=None):
        self.device_id         = device_id.upper().strip()
        self.device            = device_id.lower().strip()
        self.host              = host.strip()
        self.port              = int(port)
        self.frequency         = float(frequency)
        self.output_amplitude  = float(output_amplitude)
        self.series_resistance = float(series_resistance)
        self.time_constant     = float(time_constant)
        self.filter_order      = int(filter_order)
        self.input_range       = float(input_range)
        self.output_range      = float(output_range)
        self.settle_tc         = float(settle_tc)
        self.role              = role.lower()    # "master" | "slave"
        self.logger = logger or logging.getLogger(__name__)
        self.daq    = None

    def open(self):
        if zi is None:
            raise ImportError("zhinst not installed — pip install zhinst")

        # ── API level fallback ──────────────────────────────────────────
        # API level 6 requires LabOne 23.x or newer; older LabOne versions
        # (22.x and earlier) only accept API levels 1, 4, or 5. Try newest
        # first, fall back gracefully so older LabOne installations work too.
        last_err = None
        for api_level in (6, 5, 4, 1):
            try:
                self.daq = zi.ziDAQServer(self.host, self.port, api_level)
                self._api_level = api_level
                break
            except Exception as e:
                last_err = e
                self.daq = None
        if self.daq is None:
            raise RuntimeError(
                f"MFLI {self.device_id}: cannot connect to LabOne data server at "
                f"{self.host}:{self.port} at any API level (tried 6, 5, 4, 1). "
                f"Last error: {last_err}. Check that LabOne is running, the device "
                f"is connected, and the host/port match the LabOne 'Data Server' settings."
            )

        # ── Read LabOne / firmware versions for the log ─────────────────
        try:
            ds_ver = self.daq.getString('/zi/about/version')
            ds_rev = self.daq.getString('/zi/about/revision')
            self.logger.info(
                f"MFLI {self.device_id}: connected to LabOne data server "
                f"v{ds_ver} (rev {ds_rev}) at {self.host}:{self.port} "
                f"(API level {self._api_level})"
            )
        except Exception:
            self.logger.info(
                f"MFLI {self.device_id}: connected at {self.host}:{self.port} "
                f"(API level {self._api_level})"
            )

        # ── Connect the device through the data server ──────────────────
        # The interface name 'PCIe' matches the Connect-via setting in LabOne;
        # if your MFLI is on Ethernet (1GbE) the interface is '1GbE'. Try PCIe
        # first (your screenshot confirms PCIe), fall back to 1GbE.
        connect_err = None
        for iface in ('PCIe', '1GbE', 'USB'):
            try:
                self.daq.connectDevice(self.device_id, iface)
                self._connect_iface = iface
                self.logger.info(
                    f"MFLI {self.device_id} connected via {iface}"
                )
                return
            except Exception as e:
                connect_err = e
        raise RuntimeError(
            f"MFLI {self.device_id}: connectDevice failed on all interfaces "
            f"(PCIe, 1GbE, USB). Last error: {connect_err}. "
            f"In LabOne, check that the device shows up under 'Connected Devices' "
            f"and that the interface matches the actual hardware connection."
        )

    def configure(self):
        d, daq = self.device, self.daq

        if self.role == "slave":
            # ── Slave: lock to master 10 MHz external clock ───────────
            daq.setInt(f'/{d}/system/extclk', 1)   # use Clock 10 MHz In
            self.logger.info(f"MFLI {self.device_id}: external 10 MHz clock requested")
            # Verify the lock actually established. Some LabOne versions
            # report the clock-source status at /system/extclk readback;
            # 1 = locked to external. Wait up to 3 s; if still 0, the
            # 10 MHz cable isn't connected or master isn't outputting.
            t0 = time.time()
            locked = False
            while time.time() - t0 < 3.0:
                try:
                    val = daq.getInt(f'/{d}/system/extclk')
                    if val == 1:
                        locked = True
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            if not locked:
                self.logger.warning(
                    f"MFLI {self.device_id}: external clock readback ≠ 1 after 3 s. "
                    f"Slave may NOT be locked to master 10 MHz. Check the BNC cable from "
                    f"master Clock 10 MHz Out → slave Clock 10 MHz In. Continuing anyway."
                )
            else:
                self.logger.info(f"MFLI {self.device_id}: slave locked to external 10 MHz")

        # ── Input 1: differential, AC coupled, manual range ──────────
        daq.setInt   (f'/{d}/sigins/0/diff',      1)
        daq.setInt   (f'/{d}/sigins/0/ac',        1)
        daq.setInt   (f'/{d}/sigins/0/autorange',  0)
        daq.setDouble(f'/{d}/sigins/0/range',      self.input_range)

        # ── Oscillator 0: set frequency (master drives it;
        #    slave inherits it via the 10 MHz clock lock) ──────────────
        daq.setDouble(f'/{d}/oscs/0/freq', self.frequency)

        # ── Demodulator 0: locked to oscillator 0, reading Input 1 ───
        daq.setInt   (f'/{d}/demods/0/oscselect',    0)
        daq.setInt   (f'/{d}/demods/0/adcselect',    0)
        daq.setDouble(f'/{d}/demods/0/timeconstant', self.time_constant)
        daq.setInt   (f'/{d}/demods/0/order',        self.filter_order)
        daq.setDouble(f'/{d}/demods/0/rate',         100.0)
        daq.setInt   (f'/{d}/demods/0/enable',       1)

        if self.role == "master":
            # ── Signal Output 1: master only ─────────────────────────
            daq.setDouble(f'/{d}/sigouts/0/range',        self.output_range)
            daq.setDouble(f'/{d}/sigouts/0/amplitudes/0', self.output_amplitude)
            daq.setInt   (f'/{d}/sigouts/0/enables/0',    1)
            daq.setInt   (f'/{d}/sigouts/0/on',           1)
        else:
            # ── Slave: ensure Signal Output is OFF ───────────────────
            daq.setInt(f'/{d}/sigouts/0/on', 0)

        daq.sync()
        I_ac = self.output_amplitude / self.series_resistance
        self.logger.info(
            f"MFLI {self.device_id} ({self.role}) configured | "
            f"f={self.frequency} Hz | TC={self.time_constant*1e3:.0f} ms | "
            f"order={self.filter_order} | input={self.input_range} V"
            + (f" | I_ac={I_ac*1e9:.2f} nA" if self.role == "master" else ""))

    def measure(self, avg_n=3):
        """Single-channel measurement from this unit's demodulator 0.
        Returns a dict in _measure_dc() format (Vxy=0 in single mode)."""
        d    = self.device
        n    = int(max(1, avg_n))
        I_ac = self.output_amplitude / self.series_resistance

        time.sleep(self.settle_tc * self.time_constant)

        xs, ys = [], []
        for _ in range(n):
            s = self.daq.getSample(f'/{d}/demods/0/sample')
            xs.append(float(s['x'][0]))
            ys.append(float(s['y'][0]))
            if n > 1:
                time.sleep(self.time_constant * 0.5)

        X   = float(np.mean(xs))
        Y   = float(np.mean(ys))
        Rxx = X / I_ac if abs(I_ac) > 1e-18 else float('nan')
        # Single-channel: Y is capacitive quadrature, NOT Hall. Rxy = NaN.
        # For Hall measurements use source_mode='MFLI_DUAL'.
        Rxy_ac = float('nan')
        rms_n  = float(np.nanstd([xi/I_ac for xi in xs])*1000) if (len(xs)>1 and abs(I_ac)>1e-18) else float('nan')

        return {
            'I_eff'  : I_ac,         'Ip_m'   : I_ac,
            'Vxxp_m' : X,            'Vxxm_m' : Y,
            'Vxyp_m' : float('nan'), 'Vxym_m' : float('nan'),
            'Rxx'    : Rxx,          'Rxy'    : Rxy_ac,
            'rms_noise_mOhm': rms_n,
        }

    def measure_dual(self, slave, avg_n=3):
        """Dual-channel measurement: Vxx from master, Vxy from slave.
        Both demodulators are phase-coherent via the 10 MHz clock link.
        Returns a complete dict with true Rxx and Rxy."""
        d_m  = self.device
        d_s  = slave.device
        n    = int(max(1, avg_n))
        I_ac = self.output_amplitude / self.series_resistance

        # Single settle wait — both demodulators run continuously
        time.sleep(self.settle_tc * self.time_constant)

        xs, ys, xh, yh = [], [], [], []
        for _ in range(n):
            # Read both units back-to-back (< 1 ms apart — negligible vs TC)
            s_m = self.daq.getSample(f'/{d_m}/demods/0/sample')
            s_s = slave.daq.getSample(f'/{d_s}/demods/0/sample')
            xs.append(float(s_m['x'][0]))
            ys.append(float(s_m['y'][0]))
            xh.append(float(s_s['x'][0]))
            yh.append(float(s_s['y'][0]))
            if n > 1:
                time.sleep(self.time_constant * 0.5)

        X_xx = float(np.mean(xs))   # Vxx in-phase  (resistive)
        Y_xx = float(np.mean(ys))   # Vxx quadrature
        X_xy = float(np.mean(xh))   # Vxy in-phase  (Hall — resistive part)
        Y_xy = float(np.mean(yh))   # Vxy quadrature

        Rxx  = X_xx / I_ac if abs(I_ac) > 1e-18 else float('nan')
        Rxy  = X_xy / I_ac if abs(I_ac) > 1e-18 else float('nan')

        rms_n = float(np.nanstd([xi/I_ac for xi in xs])*1000) if (len(xs)>1 and abs(I_ac)>1e-18) else float('nan')
        return {
            'I_eff'  : I_ac,  'Ip_m'   : I_ac,
            'Vxxp_m' : X_xx,  'Vxxm_m' : Y_xx,
            'Vxyp_m' : X_xy,  'Vxym_m' : Y_xy,
            'Rxx'    : Rxx,   'Rxy'    : Rxy,
            'rms_noise_mOhm': rms_n,
        }

    def output_off(self):
        if self.daq:
            try:
                self.daq.setInt(f'/{self.device}/sigouts/0/on', 0)
                self.logger.info(f"MFLI {self.device_id} output OFF")
            except Exception as e:
                self.logger.warning(f"MFLI output_off: {e}")

    def close(self):
        self.output_off()
        if self.daq:
            try: self.daq.disconnect()
            except Exception as e:
                self.logger.warning(f"MFLI {self.device_id} disconnect: {e}")
        self.daq = None
        self.logger.info(f"MFLI {self.device_id} disconnected")

# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class SweepConfig:
    smu_resource: str; channel: str
    com_port_1: str; com_port_2: str
    I_const: float; mode: str
    T_start: float; T_end: float; T_step: float
    T_delta: float; T_ramp_rate: float
    B_max: float; B_step: float; B_start: float; B_end: float
    avg_n: int; v_limit: float; nplc: float; nvm_range: float
    tol_T: float; tol_B: float; nstable_T: int; nstable_B: int
    settle_s: float; timeout_T: float; timeout_B: float
    temp_device: str; field_group: str; sample_name: str; save_folder: str
    itc_ip: str = "192.168.123.101"; itc_port: int = 7020
    ips_ip: str = "192.168.123.102"; ips_port: int = 7020
    ramp_rate_B: float = 0.1
    # ── MFLI fields ───────────────────────────────────────────────────────────
    source_mode: str = "DC"                  # "DC" | "MFLI"
    mfli_host: str = "192.168.123.108"
    mfli_port: int = 8004
    mfli_device_id: str = "DEV6568"
    mfli_frequency: float = 17.77           # Hz — avoid 50 Hz harmonics
    mfli_output_amplitude: float = 0.1      # V_rms at Signal Output 1
    mfli_series_resistance: float = 1e6     # Ω — I_ac = V_out / R_series
    mfli_time_constant: float = 0.1         # s — demodulator filter TC
    mfli_filter_order: int = 4              # 1–8
    mfli_input_range: float = 0.01          # V — Input 1 range
    mfli_output_range: float = 0.1          # V — Signal Output 1 range
    mfli_settle_tc: float = 5.0             # × TC to wait before sampling
    # ── MFLI slave (DEV6597, Vxy channel — used when source_mode=="MFLI_DUAL") ──
    mfli_slave_device_id: str = "DEV6597"
    mfli_slave_input_range: float = 0.01    # V — Input 1 range on slave (for Vxy)
    # ── Real-time analysis flags ──────────────────────────────────────────────
    enable_anomaly_detection: bool = True   # log spike alerts + Hall metrics per point
    sweep_notes: str = ""                   # free-text annotation written to data file header and sample log
    min_stability_score: float = 0.75      # 0–1: required T stability before sweep starts (0 = disabled)
    auto_symmetrise: bool = True           # write _sym.txt after STEP sweep completes
    B_step_fine: float = 0.0              # adaptive fine step (T); 0 = disabled
    # ── Back-gate / top-gate sweep ────────────────────────────────────────────
    gate_enable: bool = False          # True = wrap sweeps in a V_gate loop
    gate_channel: str = "A"           # SMU channel for gate bias (other channel does current)
    gate_start: float = 0.0           # V — first gate voltage
    gate_end: float = 0.0             # V — last gate voltage
    gate_step: float = 1.0            # V — step between gate voltages
    gate_settle_s: float = 3.0        # s — wait after applying V_gate before sweep
    gate_v_limit: float = 10.0        # V — SMU compliance (safety: never exceed this)
    gate_leakage_max: float = 10e-9   # A — abort if |I_leak| exceeds this

    # ── Hysteresis mode ───────────────────────────────────────────────────────
    hysteresis: bool = False       # If True: sweep B out then back (full loop)
    hyst_return_zero: bool = True  # Whether to return to 0T between branches
    # ── Relaxation / Creep mode ────────────────────────────────────────────────
    relax_duration_s: float = 600.0
    relax_interval_s: float = 2.0
    relax_B_step: float = 0.0
    # ── RELAX_SCAN mode — relaxation spectroscopy across B values ────────────
    relaxscan_B_list: str = ""          # comma-separated B values (T)
    relaxscan_duration_s: float = 1800  # seconds per point (30 min default)
    relaxscan_interval_s: float = 1.0   # sampling interval (s)

    # ── Tc Scan mode ───────────────────────────────────────────────────────────
    tcscan_T_start: float = 1.5
    tcscan_T_end:   float = 10.0
    tcscan_dT:      float = 0.05
    tcscan_B_fixed: float = 0.0
    tcscan_wait_s:  float = 30.0
    # ── Multi-B TCSCAN (mode == "TCSCAN_MULTI_B" only) ────────────────────────
    # Comma-separated list of B values (Tesla) at which to repeat the entire
    # TCSCAN. Each B value produces its own data file. The existing TCSCAN
    # code is NOT modified — the multi-B mode wraps it in a loop. Field is
    # ignored in any other mode. Example: "0.0, 0.5, 1.0, -0.5".
    tcscan_B_list_csv: str = "0.0"

    # ── VTI tracking ──────────────────────────────────────────────────────────
    vti_device:   str   = "MB1.T1"   # VTI sensor/heater loop on the Mercury iTC
    vti_offset:   float = 1.0        # K — VTI setpoint = probe setpoint − offset (VTI always BELOW probe)
    vti_tracking: bool  = True       # drive VTI setpoint alongside probe

    # ── ANGLE_HYST mode (vector magnet, full B loop along (θ, φ)) ─────────────
    Bx_max:           float = 1.0    # T — per-axis hardware/software limits
    By_max:           float = 1.0
    Bz_max:           float = 4.0
    angle_phi_deg:    float = 0.0    # azimuth (held fixed during a sweep)
    angle_theta_deg:  float = 0.0    # polar angle for Single-θ submode
    angle_theta_start: float = 0.0   # θ-list submode: first angle
    angle_theta_end:   float = 15.0  # θ-list submode: last angle
    angle_theta_step:  float = 1.0   # θ-list submode: step
    angle_B_max:       float = 2.0   # T — hysteresis loop amplitude
    angle_B_step:      float = 0.05  # T — field resolution along the loop
    angle_transit_s:   float = 2.0   # s — total time budget for each (Bx,By,Bz) ramp
    angle_max_rate:    float = 0.5   # T/min — per-axis ramp-rate cap
    angle_use_theta_list: bool = False  # False = single-θ; True = θ from theta_start..end

    # ── CURRENT_OPT mode (pre-test current optimizer) ─────────────────────────
    # Sweeps current geometrically from I_start_mA upward, monitoring temperature
    # rise and resistance drift. Stops at the largest current that satisfies
    # all stability/linearity criteria. Holds magnet at copt_B_T while running.
    copt_I_start_mA:  float = 0.1     # starting current (mA)
    copt_I_max_mA:    float = 5.0     # ceiling — won't exceed even if all checks pass
    copt_I_mult:      float = 1.4     # geometric step multiplier (×1.4 ≈ 13 steps from 0.1 → 5)
    copt_dwell_s:     float = 15.0    # seconds at each current before measurement
    copt_n_samples:   int   = 8       # readings averaged at each current
    copt_dT_tol_K:    float = 0.020   # max allowed probe-T rise above baseline
    copt_R_drift_pct: float = 2.0     # max allowed R deviation from low-current baseline (%)
    copt_B_T:         float = 0.0     # magnetic field to hold during the test (T)
    copt_T_K:         float = 2.0     # temperature setpoint during the test (K)

    # ── Current reversal (DC mode) ────────────────────────────────────────────
    # When True, _measure_dc takes interleaved ±I pairs and computes the
    # per-pair antisymmetric voltage (V(+I) − V(−I))/2 to cancel thermal EMF.
    #
    # Scheme is INTERLEAVED, not block:
    #   pair 1: set +I, wait rev_settle, read; set −I, wait rev_settle, read
    #   pair 2: set +I, wait rev_settle, read; set −I, wait rev_settle, read
    #   ... (N pairs total) ...
    #   restore +I for next sweep point
    # Each ±I pair is taken back-to-back so any drift slower than ~2·rev_settle
    # cancels in the per-pair difference. This is much better than the
    # block scheme (all +I then all −I) which allows drift to accumulate
    # over the full averaging time between the two blocks.
    #
    # Cost: ~1.5–2× slower per sweep point (one extra polarity flip per pair).
    # If sweep speed matters, lower reverse_settle_s to 0.05 s (the SMU's
    # actual source-update settling is < 10 ms; the settle is mostly there
    # to let the NVM noise relax after the step).
    #
    # Default OFF for backward compatibility with high-precision QHE / plateau
    # measurements that don't tolerate flip transients. Recommended ON for
    # sub-µV signals where thermal EMF dominates.
    current_reverse: bool = False
    reverse_settle_s: float = 0.2

    # ── NVM REL auto-zero (thermal-EMF offset removal) ───────────────────────
    # When True, at sweep start the app commands both 2182A nanovoltmeters
    # to capture their current reading at I=0 as a REL reference and enable
    # subtraction. All subsequent NVM reads then return V_raw − V_reference,
    # zeroing the slowly varying thermal EMF in cables and contacts.
    #
    # Uses the SCPI dialect confirmed by probe_2182a.py on firmware C08/B01:
    #   SENS:VOLT:DC:REF:ACQ / :STAT ON/OFF / SENS:VOLT:DC:REF?
    # Avoids the value-write form (SENS:VOLT:DC:REF <value>) which was the
    # likely source of the original -113 errors. Also avoids SYST:AZER:ONCE
    # which is unnecessary (AZER:STAT? = 1 always, so it's continuously on).
    #
    # auto_zero_rel_settle_s: time to wait at I=0 for thermal EMF to settle
    # auto_zero_rel_max_uV:   if captured |offset| > this, log a warning
    # Set False for diagnostic measurements that need raw NVM readings.
    auto_zero_rel: bool = True
    auto_zero_rel_settle_s: float = 3.0
    auto_zero_rel_max_uV: float = 500.0

    # ── IV (V-I) sweep mode ───────────────────────────────────────────────────
    # mode == "IV" → step current from −iv_Imax_A to +iv_Imax_A (and back if
    # bidirectional) in steps of iv_Istep_A. Measure Vxx (and Vxy if available)
    # at each point after iv_settle_s.
    #
    # Two sub-modes:
    #  * passive (iv_active_bt = False): app does NOT control IPS or iTC.
    #    User holds B and T externally; app reads them for logging only.
    #  * active  (iv_active_bt = True): app sets IPS to iv_B_fixed_T and iTC
    #    to iv_T_fixed_K, waits for stability, then sweeps. After sweep,
    #    SMU current returns to 0 (safety).
    iv_Imax_A:           float = 1.0e-4    # current amplitude (A)
    iv_Istep_A:          float = 1.0e-5    # step size (A)
    iv_bidirectional:    bool  = False     # if True: −Imax → +Imax → −Imax
    iv_active_bt:        bool  = False     # False = passive (no IPS/iTC commands)
    iv_B_fixed_T:        float = 0.0       # only used when iv_active_bt = True
    iv_T_fixed_K:        float = 1.5       # only used when iv_active_bt = True
    iv_settle_s:         float = 0.5       # dwell at each I before measuring
    iv_show_antisymm:    bool  = True      # display antisymmetric overlay (V_anti = (V(+I)-V(-I))/2)
    iv_return_to_zero:   bool  = True      # always-on default; reserved for future toggle
    iv_tol_B_T:          float = 0.005     # B tolerance for active mode
    iv_tol_T_K:          float = 0.020     # T tolerance for active mode
    iv_stab_timeout_s:   float = 600.0     # max wait for B,T stability in active mode

    # ── RAMP safety caps (prevent runaway iTC commands) ──────────────────────
    # These guard against accidentally large T_end or T_ramp_rate values that
    # would drive the probe/VTI to dangerous temperatures. RAMP refuses to start
    # if T_end or T_ramp_rate exceeds these caps. Adjust here if you genuinely
    # need a higher range.
    #
    # WHY THIS EXISTS: a misconfigured T_end (e.g. 300 K when 10 K was meant) +
    # high ramp_rate combined with VTI tracking at the SAME rate as the probe
    # has caused the iTC to drive the VTI to 75 K in minutes. These caps + the
    # VTI-rate separation (vti_rate_max_K_per_min) make that impossible.
    ramp_T_max_K:                float = 310.0 # max safe T_end (covers full 1.5→300K survey runs; values above this are almost certainly typos)
    ramp_rate_max_K_per_min:     float = 5.0   # max safe T_ramp_rate (this is the KEY accident-prevention cap)
    vti_T_max_K:                 float = 310.0 # max safe VTI setpoint (tracks probe up to room T; cap exists to catch wild values)
    vti_rate_max_K_per_min:      float = 5.0   # hard cap on VTI ramp rate. VTI matches probe rate (T_ramp_rate); this cap is the absolute ceiling
    ramp_pre_arm_delay_s:        float = 10.0  # arm-delay countdown — long enough for you to read the trajectory and click STOP
    ramp_overshoot_abort_K:      float = 5.0   # abort RAMP if T exceeds T_end by more than this (allows reasonable PID overshoot)


class SweepConfigModel(BaseModel):
    smu_resource: str = "TCPIP::192.168.123.103::inst0::INSTR"
    channel: str = "B"
    com_port_1: str = "COM6"; com_port_2: str = "COM8"
    I_const: float = 100e-6; mode: str = "STEP"
    T_start: float = 2.0; T_end: float = 20.0; T_step: float = 2.0
    T_delta: float = 0.25; T_ramp_rate: float = 1.0
    B_max: float = 1.0; B_step: float = 0.05
    B_start: float = 0.0; B_end: float = 1.0
    avg_n: int = 3; v_limit: float = 2.0; nplc: float = 1.0; nvm_range: float = 0.0
    # Current reversal: when True, _measure_dc reads V at +I and −I and computes
    # (V(+I)−V(−I))/2 to cancel thermal-EMF offsets. Adds reverse_settle_s after
    # each polarity flip before measurement. Default OFF for backward compatibility
    # with high-precision QHE measurements that don't tolerate flip transients.
    current_reverse: bool = False
    reverse_settle_s: float = 0.2
    # NVM REL auto-zero — see dataclass for full doc
    auto_zero_rel: bool = True
    auto_zero_rel_settle_s: float = 3.0
    auto_zero_rel_max_uV: float = 500.0
    tol_T: float = 0.02; tol_B: float = 0.0005
    nstable_T: int = 3; nstable_B: int = 3
    settle_s: float = 0.1; timeout_T: float = 300.0; timeout_B: float = 120.0
    ramp_rate_B: float = 0.1
    temp_device: str = "DB8.T1"; field_group: str = "GRPZ"
    sample_name: str = "Sample1"; save_folder: str = ""
    itc_ip: str = "192.168.123.101"; itc_port: int = 7020
    ips_ip: str = "192.168.123.102"; ips_port: int = 7020
    source_mode: str = "DC"
    mfli_host: str = "192.168.123.108"
    mfli_port: int = 8004
    mfli_device_id: str = "DEV6568"
    mfli_frequency: float = 17.77
    mfli_output_amplitude: float = 0.1
    mfli_series_resistance: float = 1e6
    mfli_time_constant: float = 0.1
    mfli_filter_order: int = 4
    mfli_input_range: float = 0.01
    mfli_output_range: float = 0.1
    mfli_settle_tc: float = 5.0
    mfli_slave_device_id: str = "DEV6597"
    mfli_slave_input_range: float = 0.01
    enable_anomaly_detection: bool = True
    sweep_notes: str = ""
    min_stability_score: float = 0.75
    auto_symmetrise: bool = True
    B_step_fine: float = 0.0
    gate_enable: bool = False
    gate_channel: str = "A"
    gate_start: float = 0.0
    gate_end: float = 0.0
    gate_step: float = 1.0
    gate_settle_s: float = 3.0
    gate_v_limit: float = 10.0
    gate_leakage_max: float = 10e-9
    # ── Relaxation / Creep mode ────────────────────────────────────────────────
    relax_duration_s: float = 600.0
    relax_interval_s: float = 2.0
    relax_B_step: float = 0.0
    # ── RELAX_SCAN mode ────────────────────────────────────────────────────────
    relaxscan_B_list: str = ""
    relaxscan_duration_s: float = 1800
    relaxscan_interval_s: float = 1.0

    # ── Tc Scan mode ───────────────────────────────────────────────────────────
    tcscan_T_start: float = 1.5
    tcscan_T_end:   float = 10.0
    tcscan_dT:      float = 0.05
    tcscan_B_fixed: float = 0.0
    tcscan_wait_s:  float = 30.0
    # Multi-B TCSCAN: comma-separated B list (see dataclass for full doc)
    tcscan_B_list_csv: str = "0.0"

    # ── VTI tracking ──────────────────────────────────────────────────────────
    vti_device:   str   = "MB1.T1"
    vti_offset:   float = 1.0
    vti_tracking: bool  = True

    # ── ANGLE_HYST mode ───────────────────────────────────────────────────────
    Bx_max:           float = 1.0
    By_max:           float = 1.0
    Bz_max:           float = 4.0
    angle_phi_deg:    float = 0.0
    angle_theta_deg:  float = 0.0
    angle_theta_start: float = 0.0
    angle_theta_end:   float = 15.0
    angle_theta_step:  float = 1.0
    angle_B_max:       float = 2.0
    angle_B_step:      float = 0.05
    angle_transit_s:   float = 2.0
    angle_max_rate:    float = 0.5
    angle_use_theta_list: bool = False

    # ── CURRENT_OPT fields ────────────────────────────────────────────────────
    copt_I_start_mA:  float = 0.1
    copt_I_max_mA:    float = 5.0
    copt_I_mult:      float = 1.4
    copt_dwell_s:     float = 15.0
    copt_n_samples:   int   = 8
    copt_dT_tol_K:    float = 0.020
    copt_R_drift_pct: float = 2.0
    copt_B_T:         float = 0.0
    copt_T_K:         float = 2.0

    # ── IV (V-I) sweep mode ───────────────────────────────────────────────────
    iv_Imax_A:           float = 1.0e-4
    iv_Istep_A:          float = 1.0e-5
    iv_bidirectional:    bool  = False
    iv_active_bt:        bool  = False
    iv_B_fixed_T:        float = 0.0
    iv_T_fixed_K:        float = 1.5
    iv_settle_s:         float = 0.5
    iv_show_antisymm:    bool  = True
    iv_return_to_zero:   bool  = True
    iv_tol_B_T:          float = 0.005
    iv_tol_T_K:          float = 0.020
    iv_stab_timeout_s:   float = 600.0
    # ── RAMP safety caps (mirror of dataclass; see SweepConfig for full doc) ──
    ramp_T_max_K:                float = 310.0
    ramp_rate_max_K_per_min:     float = 5.0
    vti_T_max_K:                 float = 310.0
    vti_rate_max_K_per_min:      float = 5.0
    ramp_pre_arm_delay_s:        float = 10.0
    ramp_overshoot_abort_K:      float = 5.0


class LiveData(BaseModel):
    I_mA: Optional[float] = None
    Vxx_V: Optional[float] = None; Vxy_V: Optional[float] = None
    Rxx_Ohm: Optional[float] = None; Rxy_Ohm: Optional[float] = None
    T_K: Optional[float] = None; B_T: Optional[float] = None
    progress: Optional[str] = None; phase: Optional[str] = None
    main_x: Optional[float] = None
    main_Vxx: Optional[float] = None; main_Vxy: Optional[float] = None
    main_Rxx: Optional[float] = None; main_Rxy: Optional[float] = None
    t_s: Optional[float] = None; seq: int = 0
    # ── Real-time physics metrics (computed in _add_point when anomaly detection on) ──
    mobility: Optional[float] = None          # cm²/Vs
    carrier_density: Optional[float] = None   # cm⁻²
    hall_coefficient: Optional[float] = None  # m²/C
    anomaly: Optional[str] = None             # human-readable spike description
    # ── Sweep progress (published each _add_point) ────────────────────────────
    progress_frac: Optional[float] = None     # 0.0–1.0
    n_pts: Optional[int] = None               # points acquired so far
    total_pts: Optional[int] = None           # total expected points
    eta_s: Optional[float] = None             # estimated seconds remaining
    # ── Temperature stability (published during _wait_T) ──────────────────────
    T_stability: Optional[float] = None       # 0.0–1.0  (1.0 = perfectly stable)
    T_drift_mKmin: Optional[float] = None     # linear drift rate in mK/min
    # ── Gate bias ─────────────────────────────────────────────────────────────
    V_gate: Optional[float] = None            # applied gate voltage (V)
    I_leak: Optional[float] = None            # gate leakage current (A)
    rms_noise_mOhm: Optional[float] = None   # RMS noise of Rxx over avg_n readings (mΩ)
    sweep_mode: Optional[str] = None          # 'STEP' or 'RAMP' — broadcast every point
    # ── Vector-magnet readback (ANGLE_HYST mode) ──────────────────────────────
    # When non-None, the frontend's 3D Vector tab uses these to draw the live
    # field-vector arrow and the trajectory trail.
    Bx_T: Optional[float] = None
    By_T: Optional[float] = None
    Bz_T: Optional[float] = None
    theta_deg: Optional[float] = None
    phi_deg: Optional[float] = None
    # ── IV (V-I) mode fields ──────────────────────────────────────────────────
    # I_set_A is published per measured point so the live plot can draw
    # Vxx vs I directly without inferring I from main_x. iv_branch identifies
    # which leg of a bidirectional sweep we're on ("forward" | "return").
    # iv_polarity is +1 for I≥0, -1 for I<0 — used by the antisymm overlay.
    I_set_A: Optional[float] = None
    iv_branch: Optional[str] = None       # "forward" | "return" | None
    iv_polarity: Optional[int] = None     # +1, -1
    iv_fit_R: Optional[float] = None      # linear fit slope (Ω), updated as sweep progresses
    iv_fit_R2: Optional[float] = None     # linear fit R² goodness
    # ── (deprecated) NVM REL zero offsets ─────────────────────────────────────
    # Kept as optional fields for schema/saved-config compatibility, but never
    # populated in this build. REL auto-zero was removed (see _configure_nvm
    # note) because the SCPI dialect wasn't compatible with this 2182A setup.
    rel_offset_vxx_uV: Optional[float] = None
    rel_offset_vxy_uV: Optional[float] = None


# ── FastAPI app ───────────────────────────────────────────────────────────────
import threading as _threading

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
# NOTE: add_middleware uses LIFO order — last added runs first.
# _AuthMiddleware must be added BEFORE SessionMiddleware so that
# SessionMiddleware runs first and populates request.session.
app.add_middleware(_AuthMiddleware)
app.add_middleware(SessionMiddleware,
                   secret_key=_AUTH_CFG['secret_key'],
                   session_cookie='qtms_session',
                   max_age=86400 * 7,   # 7-day session
                   https_only=False)    # set True if you add TLS


# ── SSE subscriber list (one bounded queue per connected browser tab) ────────
# Using a per-client queue instead of a single global queue means multiple
# browser tabs / remote PCs all receive every message independently.
# A disconnected tab's queue fills to maxsize and new messages are silently
# dropped (queue.Full) so it never causes memory growth or blocks the sweep.
_sse_subscribers: list = []          # list[queue.Queue]
_sse_lock = _threading.Lock()        # protects _sse_subscribers mutations

def _sse_broadcast(data):
    """Put data into every connected client's queue; prune dead (full) clients."""
    dead = []
    with _sse_lock:
        for q in _sse_subscribers:
            try:
                q.put_nowait(data)
            except queue.Full:
                dead.append(q)
        for q in dead:
            try:
                _sse_subscribers.remove(q)
            except ValueError:
                pass

# ── Idle instrument polling ───────────────────────────────────────────────────
# When no sweep is running we still want the header to show live T and B so
# the operator can watch cooldown / magnet ramp without starting a sweep.
# A background thread polls ITC/IPS every 5 s using the IP/port from the last
# config, broadcasts a T/B LiveData message to all SSE subscribers.
_idle_poll_thread: Optional[_threading.Thread] = None
_idle_poll_stop  = _threading.Event()
_last_itc_cfg: dict = {}   # {ip, port, device}  — updated on every sweep start
_last_ips_cfg: dict = {}   # {ip, port, group}   — updated on every sweep start

def _idle_poll_worker():
    """Background thread: read T and B every 5 s when no sweep is active."""
    while not _idle_poll_stop.wait(5.0):
        with lock:
            running = sweep_thread is not None and sweep_thread.is_alive()
        if running:
            continue   # sweep is active — it handles its own publishing
        itc_cfg = dict(_last_itc_cfg)
        ips_cfg = dict(_last_ips_cfg)
        if not itc_cfg and not ips_cfg:
            continue   # no config yet — nothing to poll
        T_val = B_val = None
        if itc_cfg:
            try:
                itc = MercuryITC(itc_cfg['ip'], port=itc_cfg['port'], timeout_s=2.0)
                itc.open()
                T_val = itc.read_temperature(itc_cfg['device'])
                itc.close()
                if T_val is not None and T_val <= 0:
                    T_val = None
            except Exception:
                pass
        if ips_cfg:
            try:
                ips = MercuryIPS(ips_cfg['ip'], port=ips_cfg['port'],
                                  group=ips_cfg['group'])
                ips.open()
                B_val, _ = ips.read_field(ips_cfg['group'])
                ips.close()
            except Exception:
                pass
        if T_val is not None or B_val is not None:
            _sse_broadcast(LiveData(T_K=T_val, B_T=B_val,
                                    phase="IDLE", t_s=None))


# When the frontend scheduler has a next sweep lined up it POSTs
# /api/queue_transition with the next sweep's T_start / B_start before the
# current sweep ends.  _safe_shutdown checks this: if set it transitions to
# those conditions rather than ramping all the way to base (0 T, 1.5 K),
# saving the time and energy that would otherwise be wasted.
_next_conditions: Optional[dict] = None   # {"T_start": float, "B_start": float}

current_config: Optional[SweepConfig] = None
sweep_thread: Optional[_threading.Thread] = None
stop_event   = _threading.Event()
pause_event  = _threading.Event()   # set = paused, clear = running
lock = _threading.Lock()
seq_counter = 0



def clean(value):
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


# ── Sweep Engine ──────────────────────────────────────────────────────────────
class SweepEngine:
    def __init__(self, config: SweepConfig, stop_event: _threading.Event,
                 pause_event: _threading.Event):
        self.config = config
        self.temp_filter = TemperatureFilter()
        self.smu = self.nvm1 = self.nvm2 = self.itc = self.ips = None
        self.stop_event  = stop_event
        self.pause_event = pause_event
        self.armed       = False   # True only after B & T initial conditions met
        self._data_file  = None    # currently open data file handle
        self._file_group = None    # key of the currently open file (T_set or B_set)
        self._ch = "smua" if config.channel == "A" else "smub"
        self.mfli       = None   # MFLI master (DEV6568) — None in DC mode
        self.mfli_slave = None   # MFLI slave  (DEV6597) — None unless MFLI_DUAL
        # ── Pause/resume state: last known targets for each instrument ─────
        self._active_T_target = None   # last T setpoint sent to ITC
        self._active_T_ramp   = False  # whether ITC was in ramp mode when paused
        self._active_B_target = None   # last B setpoint sent to IPS
        # ── Last actual readings — so every time-series publish includes both ─
        self._last_T_now = None   # most recent actual T reading (K)
        self._last_B_now = None   # most recent actual B reading (T)
        self.logger = logging.getLogger(__name__)
        # ── Real-time physics analysis ────────────────────────────────────────
        self.mobility_calc  = MobilityCalculator()
        self.peak_detector  = PeakDetector(window_size=15, threshold=4.0)
        self._B_hist:   list = []   # rolling B history for Hall calc
        self._Rxx_hist: list = []   # rolling Rxx history
        self._Rxy_hist: list = []   # rolling Rxy history
        # ── Gate bias (second SMU channel) ────────────────────────────────────
        self.gate_smu   = None        # pyvisa resource for gate channel
        self._gate_ch   = ""          # "smua" or "smub"
        self._V_gate_now: Optional[float] = None   # last applied gate voltage

    def _publish(self, data: LiveData):
        global seq_counter
        with lock:
            seq_counter += 1
            data.seq = seq_counter
        _sse_broadcast(data)

    def _check_stop(self):
        if self.pause_event.is_set():
            # ── PAUSE ENTRY: freeze instruments at their current values ───────
            try:
                if self.itc:
                    T_now = self.itc.read_temperature(self.config.temp_device)
                    if T_now and T_now > 0:
                        self.itc.set_ramp_mode(False, self.config.temp_device)
                        self.itc.set_temperature_setpoint(T_now, self.config.temp_device)
                        self.itc.set_control_mode("AUTO", self.config.temp_device)
                        # ── VTI: also freeze at current reading ───────────────
                        if getattr(self.config, 'vti_tracking', True):
                            vti_dev = getattr(self.config, 'vti_device', 'MB1.T1')
                            try:
                                T_vti = self.itc.read_temperature(vti_dev)
                                if T_vti and T_vti > 0:
                                    self.itc.set_ramp_mode(False, vti_dev)
                                    self.itc.set_temperature_setpoint(T_vti, vti_dev)
                                    self.itc.set_control_mode("AUTO", vti_dev)
                            except Exception:
                                pass
            except Exception as e:
                self.logger.warning(f"Pause: ITC freeze error: {e}")
            try:
                if self.ips:
                    self.ips.set_hold(self.config.field_group)
            except Exception as e:
                self.logger.warning(f"Pause: IPS hold error: {e}")

            # ── WAIT while paused ─────────────────────────────────────────────
            while self.pause_event.is_set():
                if self.stop_event.is_set():
                    raise RuntimeError("Stopped by user")
                time.sleep(0.2)

            # ── RESUME: restore instruments to the targets they were heading to
            try:
                if self.itc and self._active_T_target is not None:
                    # SAME SAFE ORDER as _wait_T / _set_vti: rate -> mode=True
                    # -> AUTO -> setpoint LAST. Never set setpoint while
                    # ramp_mode could be False (would cause iTC to drive
                    # heater at max power between Resume's setpoint write
                    # and the ramp_mode=True write).
                    _rate_resume = float(getattr(self.config, 'T_ramp_rate', 1.0))
                    if _rate_resume <= 0:
                        _rate_resume = 1.0
                    _rate_cap_resume = float(getattr(self.config, 'ramp_rate_max_K_per_min', 5.0))
                    _rate_resume = max(0.1, min(_rate_resume, _rate_cap_resume))
                    self.itc.set_ramp_rate(_rate_resume, self.config.temp_device)
                    self.itc.set_ramp_mode(True, self.config.temp_device)  # always True
                    self.itc.set_control_mode("AUTO", self.config.temp_device)
                    self.itc.set_temperature_setpoint(
                        self._active_T_target, self.config.temp_device)
                    # ── VTI: restore tracking setpoint ────────────────────────
                    self._set_vti(self._active_T_target, enable_ramp=True)
            except Exception as e:
                self.logger.warning(f"Resume: ITC restore error: {e}")
            try:
                if self.ips and self._active_B_target is not None:
                    self.ips.set_target_field(
                        self._active_B_target, self.config.field_group)
                    self.ips.set_to_setpoint(self.config.field_group)
            except Exception as e:
                self.logger.warning(f"Resume: IPS restore error: {e}")

        if self.stop_event.is_set():
            raise RuntimeError("Stopped by user")

    def _build_B_loop_sequence(self, Bmax, Bstep):
        Bmax, Bstep = abs(float(Bmax)), abs(float(Bstep))
        def ls(start, stop, step):
            out, x = [], start
            if step > 0:
                while x <= stop + 1e-12: out.append(round(x,12)); x += step
            else:
                while x >= stop - 1e-12: out.append(round(x,12)); x += step
            if out and abs(out[-1]-stop) > 1e-9: out.append(round(stop,12))
            elif not out: out = [round(stop,12)]
            return out
        s1 = ls(+Bmax, 0.0, -Bstep)
        s2 = ls(0.0, -Bmax, -Bstep)[1:]
        s3 = ls(-Bmax, 0.0, +Bstep)[1:]
        s4 = ls(0.0, +Bmax, +Bstep)[1:]
        return s1 + s2 + s3 + s4

    def _build_B_step_sequence(self, Bstart, Bend, Bstep):
        Bstart, Bend, Bstep = float(Bstart), float(Bend), abs(float(Bstep))
        # ── Guard against B_step = 0 ──────────────────────────────────────
        # A zero step would cause the while-loop below to never terminate
        # (b never increments). When step is 0, the user almost certainly
        # wants a single B value — use Bstart (which equals Bend in that
        # intended case, but we don't assume that).
        if Bstep < 1e-12:
            return [round(Bstart, 12)]
        direction = 1.0 if Bend >= Bstart else -1.0
        step = Bstep * direction
        out, b = [], Bstart
        if direction > 0:
            while b <= Bend + 1e-12: out.append(round(b,12)); b += step
        else:
            while b >= Bend - 1e-12: out.append(round(b,12)); b += step
        if out and abs(out[-1]-Bend) > 1e-9: out.append(round(Bend,12))
        elif not out: out = [round(Bend,12)]
        return out

    def _crossed_threshold(self, T_prev, T_now, T_next):
        if np.isnan(T_prev) or np.isnan(T_now): return False
        if T_now >= T_prev: return (T_prev < T_next) and (T_now >= T_next)
        else: return (T_prev > T_next) and (T_now <= T_next)

    def _measure_dc(self, settle=0.05):
        ch, I, n = self._ch, float(self.config.I_const), int(max(1, self.config.avg_n))

        def set_I(level):
            if self.smu: self.smu.write(f"{ch}.source.leveli = {level}")
            time.sleep(settle)

        def reads():
            vxx_l, vxy_l, vsmu_l, imeas_l = [], [], [], []
            for _ in range(n):
                self._check_stop()
                if self.smu:
                    vsmu_l.append(float(self.smu.query(f"print({ch}.measure.v())").strip()))
                    imeas_l.append(float(self.smu.query(f"print({ch}.measure.i())").strip()))
                else:
                    vsmu_l.append(0.0); imeas_l.append(0.0)
                vxx_l.append(self.nvm1.read_voltage(nplc=self.config.nplc) if self.nvm1 else float("nan"))
                vxy_l.append(self.nvm2.read_voltage(nplc=self.config.nplc) if self.nvm2 else float("nan"))
                time.sleep(0.01)
            return np.array(imeas_l), np.array(vsmu_l), np.array(vxx_l), np.array(vxy_l)

        # ── Polarity branching ──────────────────────────────────────────────
        # If current_reverse is enabled: interleave +I and -I readings —
        # take ONE +I reading, flip to -I, take ONE -I reading, flip back,
        # repeat N times. Each ±I pair is taken back-to-back so drift
        # slower than ~2·rev_settle cancels in the per-pair difference
        # (V(+I) − V(−I))/2. This is MUCH better than the legacy block
        # scheme (all +I, then all −I) because the block scheme lets
        # thermal drift accumulate over the full averaging time between
        # the two blocks, surviving the subtraction as a slope error.
        #
        # The cost is one extra polarity flip per pair (N-1 extra flips vs
        # the block scheme's 1), so the sweep is ~1.5–2× slower per point
        # depending on rev_settle. If sweep time matters, reduce
        # reverse_settle_s — the SMU's actual source-update settling is
        # fast (~1–10 ms); the rev_settle is mostly there to let the NVM
        # noise relax after the step.
        #
        # Otherwise: read +I only and use the legacy single-polarity path.
        if bool(getattr(self.config, 'current_reverse', False)):
            rev_settle = float(getattr(self.config, 'reverse_settle_s', 0.2))

            # ── Debug visibility: print a one-line log on the FIRST measurement
            # of each sweep confirming that the interleaved reversal is actually
            # firing. Without this it's hard to be sure from a long log whether
            # the per-point flips are happening. We use a sentinel attribute
            # to ensure this prints just once per sweep, not per point.
            if not getattr(self, '_logged_reversal_proof', False):
                logger.info(
                    f"Current reversal (interleaved): about to flip SMU "
                    f"between +{I*1e3:+.4f} mA and {-I*1e3:+.4f} mA, "
                    f"{n} pair(s), {rev_settle:.3f} s settle each. "
                    f"You should see the SMU front-panel current oscillate "
                    f"~{2*n} times per measurement point.")
                self._logged_reversal_proof = True

            # Per-iteration single-sample readers (no internal averaging —
            # the outer loop does that)
            def _read_one():
                """Take one Vxx, Vxy, I_smu reading at the current polarity."""
                self._check_stop()
                if self.smu:
                    try:
                        i_smu  = float(self.smu.query(f"print({ch}.measure.i())").strip())
                    except Exception:
                        i_smu = float('nan')
                else:
                    i_smu = 0.0
                vxx = self.nvm1.read_voltage(nplc=self.config.nplc) if self.nvm1 else float("nan")
                vxy = self.nvm2.read_voltage(nplc=self.config.nplc) if self.nvm2 else float("nan")
                return i_smu, vxx, vxy

            Ip_l, Vxxp_l, Vxyp_l = [], [], []
            Im_l, Vxxm_l, Vxym_l = [], [], []
            for _i in range(n):
                # +I read
                set_I(+I)
                time.sleep(rev_settle)
                i_p, vxx_p, vxy_p = _read_one()
                Ip_l.append(i_p); Vxxp_l.append(vxx_p); Vxyp_l.append(vxy_p)
                # −I read (immediately after, so drift over the past
                # ~rev_settle seconds cancels in the pair difference)
                set_I(-I)
                time.sleep(rev_settle)
                i_m, vxx_m, vxy_m = _read_one()
                Im_l.append(i_m); Vxxm_l.append(vxx_m); Vxym_l.append(vxy_m)
            # Restore to +I for the next sweep point (last polarity was −I)
            set_I(+I)
            time.sleep(rev_settle)

            Ip   = np.array(Ip_l);   Im   = np.array(Im_l)
            Vxxp = np.array(Vxxp_l); Vxxm = np.array(Vxxm_l)
            Vxyp = np.array(Vxyp_l); Vxym = np.array(Vxym_l)

            # Per-pair antisymmetric voltages — each pair is ~2·rev_settle
            # plus one read time apart, so drift cancels at first order.
            Vxx_pair = (Vxxp - Vxxm) / 2.0   # length-N array of V_anti values
            Vxy_pair = (Vxyp - Vxym) / 2.0

            nm = lambda x: float(np.nanmean(x)) if np.size(x) else float("nan")
            Ip_m = nm(Ip); Im_m = nm(Im)
            # I_eff is the magnitude; sign asymmetry between Ip_m and Im_m would
            # indicate a current-source asymmetry and is reported in the log.
            I_eff = (abs(Ip_m) + abs(Im_m)) / 2.0 if np.isfinite(Ip_m) and np.isfinite(Im_m) else float("nan")
            Vxxp_m = nm(Vxxp); Vxxm_m = nm(Vxxm)
            Vxyp_m = nm(Vxyp); Vxym_m = nm(Vxym)
            # The two formulations (per-pair mean vs (mean(+) − mean(−))/2)
            # are algebraically identical for the central value, but the
            # per-pair form lets us estimate noise correctly below.
            Vxx_resistive = nm(Vxx_pair)
            Vxy_resistive = nm(Vxy_pair)
            Rxx = Vxx_resistive / I_eff if (np.isfinite(I_eff) and abs(I_eff) > 1e-15) else float("nan")
            Rxy = Vxy_resistive / I_eff if (np.isfinite(I_eff) and abs(I_eff) > 1e-15) else float("nan")
            # Per-PAIR noise estimate — this is the true measurement noise
            # AFTER drift cancellation, not the raw single-polarity noise
            # (which mixes in drift on the averaging timescale).
            if np.isfinite(I_eff) and abs(I_eff) > 1e-15:
                Rxx_pair_samples = Vxx_pair / I_eff
                rms_noise = float(np.nanstd(Rxx_pair_samples) * 1000) if np.any(np.isfinite(Rxx_pair_samples)) else float('nan')
            else:
                rms_noise = float('nan')
            return {
                "I_eff":I_eff, "Ip_m":Ip_m,
                "Vxxp_m":Vxxp_m, "Vxxm_m":Vxxm_m,
                "Vxyp_m":Vxyp_m, "Vxym_m":Vxym_m,
                "Rxx":Rxx, "Rxy":Rxy,
                "rms_noise_mOhm": rms_noise,
            }

        # ── Positive current only (no reversal) ──────────────────────────────
        set_I(+I); Ip, Vsp, Vxxp, Vxyp = reads()

        nm = lambda x: float(np.nanmean(x)) if np.size(x) else float("nan")
        Ip_m = nm(Ip)
        I_eff = abs(Ip_m) if np.isfinite(Ip_m) else float("nan")
        Vxxp_m = nm(Vxxp)
        Vxyp_m = nm(Vxyp)
        Rxx = Vxxp_m / I_eff if (np.isfinite(I_eff) and abs(I_eff) > 1e-15) else float("nan")
        Rxy = Vxyp_m / I_eff if (np.isfinite(I_eff) and abs(I_eff) > 1e-15) else float("nan")
        # Per-sample Rxx array for noise estimation
        Rxx_samples = Vxxp / I_eff if (np.isfinite(I_eff) and abs(I_eff) > 1e-15) else np.array([float('nan')])
        rms_noise   = float(np.nanstd(Rxx_samples) * 1000) if np.any(np.isfinite(Rxx_samples)) else float('nan')
        # Compatibility: set "−I" values so downstream (V+−V−)/2 formulas
        # produce the correct single-polarity result:  (Vp − (−Vp))/2 = Vp
        return {
            "I_eff":I_eff, "Ip_m":Ip_m,
            "Vxxp_m":Vxxp_m, "Vxxm_m":-Vxxp_m,
            "Vxyp_m":Vxyp_m, "Vxym_m":-Vxyp_m,
            "Rxx":Rxx, "Rxy":Rxy,
            "rms_noise_mOhm": rms_noise,
        }


    def _measure_mfli(self):
        """Route to dual (Rxx + Rxy) or single (Rxx only) lock-in measurement."""
        if self.mfli is None:
            raise RuntimeError("MFLI master not initialised")
        mode = getattr(self.config, 'source_mode', 'DC')
        if mode == 'MFLI_DUAL':
            if self.mfli_slave is None:
                raise RuntimeError("MFLI slave not initialised (source_mode=MFLI_DUAL)")
            return self.mfli.measure_dual(self.mfli_slave, avg_n=self.config.avg_n)
        return self.mfli.measure(avg_n=self.config.avg_n)

    def _measure(self, settle=0.05):
        """Dispatch: DC instruments or MFLI lock-in depending on source_mode."""
        mode = getattr(self.config, 'source_mode', 'DC')
        if mode in ('MFLI', 'MFLI_SINGLE', 'MFLI_DUAL'):
            return self._measure_mfli()
        return self._measure_dc(settle=settle)

    # ── VTI coordinated tracking ─────────────────────────────────────────────
    def _set_vti(self, probe_target, enable_ramp=True, ramp_rate=None):
        """Set VTI setpoint to track the probe with the configured offset.

        VTI_setpoint = max(1.5, probe_target - vti_offset)
        Uses the same ITC connection on a different device address (MB1.T1).

        ════════════════════════════════════════════════════════════════════
        DIRECTION-AWARE SAFE COMMANDING:
          - If the new VTI setpoint is ABOVE current VTI T (heating): use
            ramp_mode=True at the clamped vti_rate. This prevents the iTC
            from driving the VTI heater at MAX power (the prior incident).
          - If the new VTI setpoint is AT or BELOW current VTI T (cooling
            or hold): use ramp_mode=False. Safe — PID just turns the VTI
            heater off and lets natural pumping cool the VTI. Faster than
            a forced slow ramp.

        The `enable_ramp` parameter is now informational only — the actual
        choice is made by direction. The `ramp_rate` parameter is the rate
        used WHEN heating; for cooling no rate is used.

        Command order: (rate) -> mode -> AUTO -> setpoint LAST. Setpoint
        must be last so the iTC sees it under the new ramp_mode.
        Wrapped in try/except so a single transient failure doesn't break
        the caller.
        ════════════════════════════════════════════════════════════════════
        """
        if not self.itc:
            return
        if not getattr(self.config, 'vti_tracking', True):
            return
        vti_dev = getattr(self.config, 'vti_device', 'MB1.T1')
        offset  = float(getattr(self.config, 'vti_offset', 1.0))
        # VTI setpoint MUST stay BELOW probe setpoint by at least `offset` K.
        # Hard-floor at 1.5 K (helium base).
        vti_sp  = max(1.5, float(probe_target) - offset)
        # ── Rate selection ───────────────────────────────────────────────────
        # Per spec: VTI rate ALWAYS matches the probe rate so the two loops
        # advance in lock-step. The caller passes `ramp_rate` (probe rate).
        # If absent we fall back to the probe rate from config (T_ramp_rate),
        # then the legacy vti_rate_max_K_per_min cap. The cap also acts as a
        # hard upper bound on whatever is selected.
        if ramp_rate is not None and float(ramp_rate) > 0:
            rate = float(ramp_rate)
        else:
            rate = float(getattr(self.config, 'T_ramp_rate', 1.0))
            if rate <= 0:
                rate = float(getattr(self.config, 'vti_rate_max_K_per_min', 1.0))
        if rate <= 0:
            rate = 1.0
        rate_cap = float(getattr(self.config, 'vti_rate_max_K_per_min', 5.0))
        # Cap at the configured maximum but DON'T silently shrink below a
        # reasonable floor — if the user genuinely wants a fast rate, the
        # safety preflight already rejected anything truly dangerous.
        rate = max(0.05, min(rate, rate_cap))
        try:
            # Direction detection (informational only — we use ramp_mode=ON
            # in BOTH directions for safety. Under ramp_mode=ON, the iTC
            # never commands max heater — it ramps at the configured rate.
            # That's safe for heating AND cooling: for cooling the PID
            # simply turns the heater off and lets natural cooling proceed
            # (it will undershoot the slow ramp, which is fine).
            try:
                _vti_T_current = self.itc.read_temperature(vti_dev)
                if not (_vti_T_current and _vti_T_current > 0):
                    _vti_T_current = float('nan')
            except Exception:
                _vti_T_current = float('nan')
            _direction = ("HEATING" if (not np.isnan(_vti_T_current)
                                        and vti_sp > _vti_T_current + 0.1)
                          else ("COOLING" if (not np.isnan(_vti_T_current)
                                              and vti_sp < _vti_T_current - 0.1)
                                else "HOLD"))
            # ── Command order: RATE → MODE=ON → AUTO → SETPOINT LAST ─────
            # Setpoint must be LAST so the iTC interprets it under the new
            # ramp_mode and rate. With ramp_mode=ON the iTC will ramp from
            # current VTI T to vti_sp at `rate` K/min — no heater spike.
            self.itc.set_ramp_rate(rate, vti_dev)
            self.itc.set_ramp_mode(True, vti_dev)
            self.itc.set_control_mode("AUTO", vti_dev)
            self.itc.set_temperature_setpoint(vti_sp, vti_dev)
            _from = ("?" if np.isnan(_vti_T_current)
                     else f"{_vti_T_current:.3f}K")
            self.logger.info(
                f"VTI {_direction}: {vti_dev} {_from} -> {vti_sp:.3f}K "
                f"@ {rate:.3f}K/min (probe_target={probe_target:.3f}K, "
                f"offset={offset:.2f}K, ramp_mode=ON — safe in both directions)"
            )
        except Exception as e:
            self.logger.warning(f"VTI set error ({vti_dev}): {e}")

    def _wait_T(self, target, t0, enable_ramp=False, extra_wait=0.0):
        """Wait until temperature reaches the target and is stable.

        After reaching stability, optionally dwells for `extra_wait` seconds.
        This extra dwell is important for measurements where the sample
        temperature lags the thermometer (e.g. TCSCAN at low T).

        If self.itc is None (passive mode — iTC was unreachable at connect
        time), this function returns the requested target immediately
        instead of looping forever. The caller is responsible for knowing
        that no actual T control happened and that subsequent reads will
        return NaN/0.
        """
        # ── Passive-mode short-circuit ────────────────────────────────────
        if self.itc is None:
            self._last_T_now = float('nan')
            self._publish(LiveData(
                phase=f"_wait_T (passive): no iTC, returning target={target:.3f} K immediately",
                T_K=float('nan'), B_T=self._last_B_now, t_s=time.time()-t0))
            # Return the target value so downstream code that records "T_set"
            # still gets a number. Actual T is unknown.
            return float(target)
        # Reset the filter buffer: readings from the previous T_set would make
        # the first readings at the new target look like spikes and get clipped,
        # producing the characteristic artificial dip on the T(t) plot.
        self.temp_filter.reset()
        start = time.time()
        stable_count = 0
        readings = []
        last_publish = 0.0          # rate-limit: publish at most 4 Hz
        PUBLISH_INTERVAL = 0.25     # seconds between T/B status publishes
        # Track for pause/resume restore
        self._active_T_target = target
        self._active_T_ramp   = enable_ramp
        if self.itc:
            # ════════════════════════════════════════════════════════════════
            # DIRECTION-AWARE SAFE iTC SETPOINT COMMANDING
            #
            # Mercury iTC heater behaviour depends on ramp_mode:
            #   - ramp_mode=True:  setpoint changes propagate at the configured
            #                      rate. Controlled approach for both heating
            #                      and cooling.
            #   - ramp_mode=False: setpoint changes are immediate. PID drives
            #                      the heater to whatever power is needed to
            #                      reach setpoint ASAP. For HEATING this can
            #                      mean MAX heater power (dangerous). For
            #                      COOLING the PID just turns the heater OFF
            #                      and lets the cryostat cool naturally
            #                      (safe AND fast — no waiting for a slow ramp).
            #
            # SAFE STRATEGY:
            #   - If target > current_T (HEATING): ramp_mode=True at clamped
            #     rate (prevents heater runaway).
            #   - If target <= current_T (COOLING or HOLDING): ramp_mode=False
            #     is safe and faster (no slow ramp through the helium pumping).
            #
            # Either way, command order is: (rate) -> mode -> AUTO -> setpoint
            # LAST. Setpoint must be the LAST command so the iTC interprets it
            # under the new ramp_mode, not the previous state.
            # Commands are wrapped in try/except so a single transient failure
            # doesn't abort the entire sweep — without this, the next line
            # never runs and the polling loop is never entered.
            # ════════════════════════════════════════════════════════════════
            # ── Read current T robustly: try a few times so a single
            # transient hiccup doesn't poison the direction decision.
            _T_current_for_dir = None
            for _try in range(3):
                try:
                    _t = self.itc.read_temperature(self.config.temp_device)
                    if _t and _t > 0:
                        _T_current_for_dir = float(_t)
                        break
                except Exception:
                    pass
                time.sleep(0.15)
            _direction_known = _T_current_for_dir is not None
            if not _direction_known:
                # Direction unknown — pick the SAFE assumption: HEATING.
                # Heating under ramp_mode=ON enforces a rate limit (no heater
                # spike). Cooling under ramp_mode=ON also works (PID just
                # turns off heater + natural cooldown). Either way, no
                # heater runaway. Defaulting to HEATING was the WRONG choice
                # historically only because the old code used ramp_mode=OFF
                # for cooling, which IS a heater-spike risk on heating.
                _T_current_for_dir = float(target)  # placeholder for logging
            _is_heating = (_direction_known
                           and float(target) > _T_current_for_dir + 0.1)
            _rate = float(getattr(self.config, 'T_ramp_rate', 1.0))
            if _rate <= 0:
                _rate = 1.0
            _rate_cap = float(getattr(self.config, 'ramp_rate_max_K_per_min', 5.0))
            _rate = max(0.05, min(_rate, _rate_cap))
            try:
                # ═══════════════════════════════════════════════════════════
                # SAFE UNIVERSAL COMMAND ORDER (works for heat & cool):
                #   1. RSET = rate (K/min)
                #   2. RENA = ON (ramp_mode=True)
                #   3. FAUT = ON (AUTO control)
                #   4. TSET = target (setpoint LAST)
                # Setpoint must be LAST so the iTC interprets it under the
                # NEW ramp_mode and rate. Under ramp_mode=ON the iTC NEVER
                # commands max heater — it ramps from current T to setpoint
                # at the configured rate. This is the principle that
                # eliminates the shoot-up bug.
                # ═══════════════════════════════════════════════════════════
                self.itc.set_ramp_rate(_rate, self.config.temp_device)
                self.itc.set_ramp_mode(True, self.config.temp_device)
                self.itc.set_control_mode("AUTO", self.config.temp_device)
                self.itc.set_temperature_setpoint(target, self.config.temp_device)
                _from = (f"{_T_current_for_dir:.3f}K" if _direction_known
                         else "?K (read failed)")
                _dir_label = ("HEATING" if _is_heating
                              else "COOLING" if _direction_known
                              else "UNKNOWN→safe-ramp")
                self.logger.info(
                    f"_wait_T {_dir_label}: probe {_from} -> {target:.3f}K "
                    f"@ {_rate:.3f}K/min (ramp_mode=ON in BOTH directions — "
                    f"no heater spike possible)"
                )
            except Exception as _itc_e:
                self.logger.error(
                    f"_wait_T: iTC command failed: {_itc_e} — proceeding to poll "
                    f"anyway, but T may not change as expected."
                )
                self._publish(LiveData(
                    phase=f"_wait_T: iTC commanding failed ({_itc_e}) — polling anyway",
                    T_K=self._last_T_now, t_s=time.time() - t0))
            # ── VTI coordinated tracking: SAME rate as probe (lock-step) ──
            try:
                self._set_vti(target, enable_ramp=True, ramp_rate=_rate)
            except Exception as _vti_e:
                self.logger.warning(f"_wait_T: _set_vti failed: {_vti_e}")
            # ── Immediate publish so the UI shows something right away ────────
            # Without this, the UI is silent until the first polling iteration
            # finds tK > 0, which can be several seconds.
            self._publish(LiveData(
                phase=f"_wait_T polling: target={target:.3f}K @ {_rate:.3f}K/min, "
                      f"VTI={max(1.5, target - float(getattr(self.config, 'vti_offset', 1.0))):.3f}K",
                T_K=self._last_T_now, B_T=self._last_B_now, t_s=time.time()-t0))
        # ── Polling-loop iTC read protection ─────────────────────────────────
        # A single transient COM/VISA hiccup must NOT kill the entire sweep
        # by letting an exception propagate out of _wait_T. We log, count,
        # and only give up after ~15 s of sustained failure.
        _wt_consec_read_fail = 0
        _wt_consec_read_fail_max = 30  # at settle_s≈0.5s, ~15 s before giving up
        while True:
            self._check_stop()
            try:
                tK = self.itc.read_temperature(self.config.temp_device) if self.itc else 0.0
                _wt_consec_read_fail = 0
            except Exception as _wt_read_e:
                tK = 0.0
                _wt_consec_read_fail += 1
                if _wt_consec_read_fail <= 3 or _wt_consec_read_fail % 10 == 0:
                    logger.warning(
                        f"_wait_T: iTC read failed ({_wt_consec_read_fail}x): "
                        f"{_wt_read_e}. Retrying — will give up after "
                        f"~{_wt_consec_read_fail_max * self.config.settle_s:.1f}s."
                    )
                if _wt_consec_read_fail >= _wt_consec_read_fail_max:
                    logger.error(
                        f"_wait_T: iTC unreachable for {_wt_consec_read_fail} "
                        f"consecutive reads — returning last known T."
                    )
                    self._publish(LiveData(
                        phase=f"_wait_T: iTC unreachable, returning last T={self._last_T_now:.3f}K",
                        T_K=self._last_T_now, B_T=self._last_B_now, t_s=time.time()-t0))
                    return float(self._last_T_now) if self._last_T_now else float(target)
            # ── HEARTBEAT publish even when read returned 0 or failed ─────
            # Without this, the UI shows a frozen T value during slow
            # warm-up / cooldown phases when the iTC takes a while to
            # report a new reading. Publishing the last-known T at the
            # PUBLISH_INTERVAL rate keeps the live plot alive and shows
            # the user the sweep is still working.
            if tK <= 0:
                _now_hb = time.time()
                if _now_hb - last_publish >= PUBLISH_INTERVAL:
                    self._publish(LiveData(
                        phase=f"_wait_T polling: target={target:.3f}K (waiting for iTC read)",
                        T_K=self._last_T_now, B_T=self._last_B_now, t_s=_now_hb - t0))
                    last_publish = _now_hb
            if tK > 0:
                readings.append(tK)
                if len(readings) > 20: readings.pop(0)
                ft = self.temp_filter.filter(tK)
                self._last_T_now = ft
                now = time.time()

                # ── Live stability score + drift rate ─────────────────────
                T_stability = None
                T_drift_mKmin = None
                window = readings[-min(len(readings), 10):]
                if len(window) >= 4:
                    rms_dev = float(np.std(window))
                    T_stability = max(0.0, min(1.0,
                        1.0 - rms_dev / max(self.config.tol_T, 1e-9)))
                    if len(window) >= 3:
                        t_pts = np.arange(len(window), dtype=float)
                        slope_Ks = float(np.polyfit(t_pts, window, 1)[0])
                        T_drift_mKmin = slope_Ks / max(self.config.settle_s, 0.01) * 60_000

                if now - last_publish >= PUBLISH_INTERVAL:
                    self._publish(LiveData(
                        T_K=ft, B_T=self._last_B_now, t_s=now - t0,
                        T_stability=T_stability, T_drift_mKmin=T_drift_mKmin))
                    last_publish = now

                # ── Stability gate (tol + score) ──────────────────────────
                min_score = float(getattr(self.config, 'min_stability_score', 0.75))
                in_tol  = abs(tK - target) <= self.config.tol_T
                score_ok = (T_stability is None) or (min_score <= 0) or (T_stability >= min_score)
                if in_tol and score_ok:
                    stable_count += 1
                else:
                    stable_count = 0

                if stable_count >= self.config.nstable_T:
                    # ── Optional extra dwell after reaching stability ────────────
                    # Important for TCSCAN: the thermometer reading is not
                    # always representative of the sample temperature; dwelling
                    # for `extra_wait` seconds allows the sample to thermalise.
                    last_ft = ft
                    if extra_wait and extra_wait > 0:
                        self._publish(LiveData(
                            phase=f"_wait_T: dwelling {extra_wait:.0f}s for sample thermalisation",
                            T_K=ft, B_T=self._last_B_now, t_s=time.time() - t0))
                        dwell_start = time.time()
                        while time.time() - dwell_start < extra_wait:
                            self._check_stop()
                            try:
                                tK_dwell = self.itc.read_temperature(self.config.temp_device) if self.itc else 0.0
                            except Exception as _dwell_e:
                                logger.warning(f"_wait_T dwell: iTC read failed: {_dwell_e}")
                                tK_dwell = 0.0
                            if tK_dwell > 0:
                                ft_dwell = self.temp_filter.filter(tK_dwell)
                                self._last_T_now = ft_dwell
                                last_ft = ft_dwell
                                readings.append(tK_dwell)
                                if len(readings) > 20: readings.pop(0)
                                if time.time() - last_publish >= PUBLISH_INTERVAL:
                                    self._publish(LiveData(
                                        T_K=ft_dwell, B_T=self._last_B_now, t_s=time.time() - t0))
                                    last_publish = time.time()
                            time.sleep(min(self.config.settle_s, 1.0))
                    self._publish(LiveData(
                        T_K=last_ft, B_T=self._last_B_now, t_s=time.time() - t0,
                        T_stability=T_stability, T_drift_mKmin=T_drift_mKmin))
                    return float(np.mean(readings[-3:])) if len(readings) >= 3 else tK
                if time.time() - start > self.config.timeout_T:
                    logger.warning(
                        f"_wait_T timeout at {tK:.3f} K  target={target:.3f} K  "
                        f"score={(T_stability if T_stability is not None else float('nan')):.2f}"
                        f"  drift={(T_drift_mKmin if T_drift_mKmin else 0.0):.1f} mK/min")
                    self._publish(LiveData(
                        T_K=ft, B_T=self._last_B_now, t_s=time.time() - t0,
                        T_stability=T_stability, T_drift_mKmin=T_drift_mKmin))
                    return tK
            time.sleep(self.config.settle_s)

    def _wait_B(self, target, t0):
        # ── Passive-mode short-circuit ────────────────────────────────────
        # If self.ips is None (IPS was unreachable at connect time), there's
        # no point waiting for the field to reach the target — the magnet
        # can't be commanded. Return immediately with NaN field so the data
        # file honestly records "B unknown" rather than the requested target
        # (which the magnet never actually reached).
        # Filename strings that use B_fixed/B_set are unaffected — those
        # use the cfg.tcscan_B_fixed value directly, not B_now.
        if self.ips is None:
            self._last_B_now = float('nan')
            self._publish(LiveData(
                phase=f"_wait_B (passive): no IPS, B remains uncontrolled "
                      f"(target was {target:+.4f} T)",
                T_K=self._last_T_now, B_T=float('nan'), t_s=time.time()-t0))
            return float('nan'), False
        start = time.time()
        stable_count = 0
        readings = []
        last_publish = 0.0          # rate-limit: publish at most 4 Hz
        PUBLISH_INTERVAL = 0.25     # seconds between T/B status publishes
        # Track for pause/resume restore
        self._active_B_target = target
        # ── DYNAMIC TIMEOUT ─────────────────────────────────────────────────
        # The static timeout_B (default 120 s) is far too short for large
        # ramps. At 0.1 T/min, a 0 → 3.82 T ramp takes 38 min = 2292 s, but
        # _wait_B would time out at 120 s with B ≈ 0.2 T — silently corrupting
        # any subsequent recording. Compute timeout from the actual ramp
        # distance and rate, with a generous margin for settling at the end.
        try:
            B_now_for_calc = self._last_B_now if (self._last_B_now is not None) else (
                self.ips.read_field(self.config.field_group)[0] if self.ips else 0.0)
        except Exception:
            B_now_for_calc = 0.0
        ramp_rate = max(0.001, float(self.config.ramp_rate_B))   # T/min, guard against 0
        ramp_time_s = (abs(float(target) - float(B_now_for_calc)) / ramp_rate) * 60.0
        # Required timeout: ramp time + 30% margin + 60 s settle floor + the
        # configured timeout_B (typically 120 s, used as the settle budget).
        dynamic_timeout = ramp_time_s * 1.3 + 60.0 + float(self.config.timeout_B)
        logger.info(
            "wait_B: target=%+.4f T  current=%+.4f T  ramp_rate=%.3f T/min  "
            "ramp_time=%.0fs  timeout=%.0fs",
            float(target), float(B_now_for_calc), ramp_rate,
            ramp_time_s, dynamic_timeout
        )

        if self.ips:
            s = self.ips.read_detailed_status(self.config.field_group)
            if s.get("catch_enable") == "OFF":
                self.ips.set_catch_enable(True, self.config.field_group); time.sleep(2)
            self.ips.set_switch_heater(True, self.config.field_group); time.sleep(3)
            rr = float(self.config.ramp_rate_B)
            if rr > 0: self.ips.set_ramp_rate_field(rr, self.config.field_group); time.sleep(0.5)
            self.ips.set_target_field(target, self.config.field_group); time.sleep(0.5)
            self.ips.set_to_setpoint(self.config.field_group)
        while True:
            self._check_stop()
            field, valid = self.ips.read_field(self.config.field_group) if self.ips else (0.0, False)
            self._last_B_now = field
            readings.append(field)
            if len(readings) > 10: readings.pop(0)
            now = time.time()
            if now - last_publish >= PUBLISH_INTERVAL:
                self._publish(LiveData(B_T=field, T_K=self._last_T_now, t_s=now-t0))
                last_publish = now
            if abs(field-target) <= self.config.tol_B:
                stable_count += 1
                if stable_count >= self.config.nstable_B:
                    if self.ips: self.ips.set_hold(self.config.field_group)
                    # Always publish final settled value
                    self._publish(LiveData(B_T=field, T_K=self._last_T_now, t_s=time.time()-t0))
                    return float(np.mean(readings[-3:])) if len(readings) >= 3 else field, valid
            else:
                stable_count = 0
            if time.time()-start > dynamic_timeout:
                if self.ips: self.ips.set_hold(self.config.field_group)
                logger.error(
                    "wait_B: TIMEOUT at %.0fs — target=%+.4f T, actual field=%+.4f T, "
                    "|ΔB|=%.4f T. Increase ramp_rate_B or timeout_B if the ramp "
                    "is genuinely this slow.",
                    time.time()-start, float(target), float(field), abs(field-float(target))
                )
                self._publish(LiveData(B_T=field, T_K=self._last_T_now, t_s=time.time()-t0))
                return field, valid
            time.sleep(self.config.settle_s)

    def _configure_gate(self):
        """Configure the gate-bias SMU channel (voltage source, current measure)."""
        if not self.gate_smu: return
        g = self._gate_ch
        # Voltage source, compliance = gate_leakage_max × 1000 (current compliance)
        # We drive V and read back I_leak.
        lim_i = max(abs(self.config.gate_leakage_max) * 100, 1e-6)   # headroom
        self.gate_smu.write(f"""
{g}.reset()
{g}.source.func = {g}.OUTPUT_DCVOLTS
{g}.source.autorangev = {g}.AUTORANGE_OFF
{g}.source.rangev = {max(abs(self.config.gate_v_limit), 1.0):.1f}
{g}.source.limitv = {abs(self.config.gate_v_limit):.3f}
{g}.source.limiti = {lim_i:.3e}
{g}.source.leveli = 0
{g}.source.levelv = 0
{g}.measure.autorangei = {g}.AUTORANGE_ON
{g}.source.output = {g}.OUTPUT_ON
""")
        time.sleep(0.3)
        logger.info(f"Gate SMU {g} configured: ±{self.config.gate_v_limit:.1f} V")

    def _apply_gate(self, V_g: float) -> float:
        """
        Ramp gate voltage to V_g, wait gate_settle_s, return leakage current.
        Aborts the sweep if |I_leak| > gate_leakage_max.
        Returns I_leak in Amps.
        """
        cfg = self.config
        g   = self._gate_ch
        V_g = float(np.clip(V_g, -abs(cfg.gate_v_limit), abs(cfg.gate_v_limit)))
        self._V_gate_now = V_g

        if not self.gate_smu:
            return 0.0

        # Ramp in 0.5 V steps to avoid displacement currents
        V_now_str = self.gate_smu.query(f"print({g}.source.levelv)").strip()
        try:
            V_now = float(V_now_str)
        except ValueError:
            V_now = 0.0

        step = 0.5 * (1.0 if V_g > V_now else -1.0)
        steps = np.arange(V_now, V_g, step).tolist() + [V_g]
        for v in steps:
            self._check_stop()
            self.gate_smu.write(f"{g}.source.levelv = {v:.6f}")
            time.sleep(0.05)

        # Settle
        self._publish(LiveData(
            phase=f"GATE: V_gate = {V_g:+.3f} V  (settling {cfg.gate_settle_s:.1f} s)",
            V_gate=V_g))
        t_settle = time.time()
        while time.time() - t_settle < cfg.gate_settle_s:
            self._check_stop()
            time.sleep(0.2)

        # Read leakage
        I_leak = 0.0
        try:
            raw = self.gate_smu.query(f"print({g}.measure.i())").strip()
            I_leak = float(raw)
        except Exception:
            pass

        # Safety: abort if leakage too high
        if abs(I_leak) > abs(cfg.gate_leakage_max):
            self._publish(LiveData(
                phase=f"GATE: LEAKAGE FAULT  I={I_leak:.2e} A  (limit {cfg.gate_leakage_max:.1e} A)",
                V_gate=V_g, I_leak=I_leak))
            logger.error(f"Gate leakage fault: {I_leak:.2e} A at Vg={V_g:.3f} V")
            self.stop_event.set()   # triggers _check_stop → clean shutdown

        logger.info(f"Gate: Vg={V_g:+.3f} V  I_leak={I_leak:.2e} A")
        return I_leak

    def _gate_off(self):
        """Ramp gate back to 0 V and disable output safely."""
        if not self.gate_smu: return
        try:
            self._apply_gate(0.0)
            self.gate_smu.write(f"{self._gate_ch}.source.output = {self._gate_ch}.OUTPUT_OFF")
        except Exception as e:
            logger.warning(f"Gate off error: {e}")


    def _configure_nvm(self, nvm):
        if not nvm: return
        nvm.clear_status()
        try: nvm.write("*RST"); time.sleep(0.2); nvm.clear_status()
        except: pass
        nvm.write('SENS:FUNC "VOLT:DC"')
        cfg = self.config
        if cfg.nvm_range > 0:
            nvm.write(f"SENS:VOLT:DC:RANG {cfg.nvm_range}")
            nvm.write("SENS:VOLT:DC:RANG:AUTO OFF")
        else:
            nvm.write("SENS:VOLT:DC:RANG:AUTO ON")
        nvm.write(f"SENS:VOLT:DC:NPLC {cfg.nplc}")
        nvm.write("SYST:AZER ON")
        nvm.write("INIT:CONT OFF")
        nvm.write("TRIG:COUN 1")
        nvm.write("SAMP:COUN 1")
        nvm.write("FORM:DATA ASC")
        nvm.write("FORM:ELEM READ")
        nvm.drain_errors(10)
        # Clear any REL state left over from a previous app.py session.
        # Without this, the first sweep of a new session could inherit
        # yesterday's captured reference (the probe found COM6 still had
        # REL=ON with REF=2.38 µV from a prior run).
        # Confirmed-working command on firmware C08/B01 (probe_2182a output):
        #   SENS:VOLT:DC:REF:STAT OFF   ← deactivates subtraction
        # DO NOT add `SENS:VOLT:DC:REF 0` here — that value-write form was
        # the likely source of the original error -113 ("Undefined header").
        # Disabling STAT is sufficient: the stored REF value is harmless
        # when STAT is OFF.
        try:
            nvm.write("SENS:VOLT:DC:REF:STAT OFF")
            time.sleep(0.1)
            nvm.drain_errors(5)
        except Exception:
            pass

    def _zero_nvm_rel(self):
        """Capture the current NVM reading on both 2182As as a REL reference
        and enable REL subtraction. After this, every subsequent NVM read
        returns V_raw − V_reference, which zeros out the thermal-EMF offset
        present at sweep start.

        Uses the SCPI dialect confirmed by probe_2182a.py on firmware
        C08/B01:
          SENS:VOLT:DC:REF:ACQ        captures next reading as reference
          SENS:VOLT:DC:REF?           reads back the stored reference
          SENS:VOLT:DC:REF:STAT ON    enables REL subtraction
          SENS:VOLT:DC:REF:STAT OFF   disables it (cleanup path)

        Notes on what we deliberately do NOT send:
          - SYST:AZER:ONCE — unnecessary, AZER is always running (SYST:AZER:STAT? = 1)
          - SENS:VOLT:DC:REF <value> — value-write form, untested by the probe,
            and was the likely source of the original error -113. STAT OFF
            is sufficient to deactivate REL; we don't need to reset REF.

        Sequence (run after CONNECTED, before any sweep mode dispatches):
          1. SMU output → I = 0 A
          2. Wait auto_zero_rel_settle_s for thermal EMF to settle
          3. For each NVM:
             a. STAT OFF                     (ensure a clean starting state)
             b. *CLS                         (clear any leftover error queue)
             c. INIT + FETCh? (read_voltage) (forces a measurement we capture)
             d. REF:ACQ                      (mark that reading as the reference)
             e. Brief wait                   (let ACQ settle the stored REF)
             f. REF? readback                (verify the reference was stored)
             g. STAT ON                      (enable subtraction)
             h. Optional read-after-on       (verify post-REL Vxx is ~0)

        Failures inside the per-NVM loop are caught and logged but don't
        abort the sweep — the worst case is that REL stays off for that
        channel and the measurement proceeds with raw readings.
        """
        cfg = self.config
        if not bool(getattr(cfg, 'auto_zero_rel', True)):
            logger.info("NVM auto-zero (REL) disabled in config — skipping")
            return
        if not (self.nvm1 or self.nvm2):
            return
        if not self.smu:
            logger.info("NVM auto-zero (REL): no SMU connected — skipping "
                        "(can't guarantee I = 0 A without SMU)")
            return

        settle_s = float(getattr(cfg, 'auto_zero_rel_settle_s', 3.0))
        max_uV   = float(getattr(cfg, 'auto_zero_rel_max_uV',   500.0))
        ch = self._ch

        self._publish(LiveData(
            phase=f"NVM auto-zero (REL): settling {settle_s:.1f} s at I = 0 A …"))

        # 1. Force SMU current to exactly 0 A so any reading is pure offset
        try:
            self.smu.write(f"{ch}.source.leveli = 0")
        except Exception as e:
            logger.warning(f"NVM REL: could not set SMU to 0 A ({e}); proceeding anyway")

        # 2. Settle wait — interruptible via _check_stop so a user STOP
        # doesn't leave us hanging.
        t_settle_end = time.time() + settle_s
        while time.time() < t_settle_end:
            self._check_stop()
            time.sleep(0.1)

        captured = {}
        for label, nvm in (('Vxx', self.nvm1), ('Vxy', self.nvm2)):
            if not nvm:
                continue
            try:
                # 3a. Ensure REL is OFF before we start (idempotent)
                nvm.write("SENS:VOLT:DC:REF:STAT OFF")
                time.sleep(0.1)

                # 3b. Clear any residual errors
                try:
                    nvm.write("*CLS")
                    time.sleep(0.05)
                    nvm.drain_errors(5)
                except Exception:
                    pass

                # 3c. Take one reading (forces INIT + FETCh? cycle) — this
                # is the reading that REF:ACQ will capture.
                v_ref = nvm.read_voltage(nplc=cfg.nplc)
                captured[label] = v_ref

                # 3d. Mark that reading as the reference
                nvm.write("SENS:VOLT:DC:REF:ACQ")
                time.sleep(0.2)

                # 3f. Read back the stored reference to verify
                try:
                    ref_resp = nvm.query("SENS:VOLT:DC:REF?").strip()
                    v_stored = float(ref_resp.replace('V', '').replace('v', ''))
                except Exception as _re:
                    v_stored = float('nan')
                    logger.debug(f"NVM REL: {label} REF? readback failed ({_re})")

                # 3g. Enable REL subtraction
                nvm.write("SENS:VOLT:DC:REF:STAT ON")
                time.sleep(0.1)
                nvm.drain_errors(5)

                # Diagnostic logging
                v_ref_uV   = v_ref   * 1e6 if math.isfinite(v_ref)   else float('nan')
                v_stored_uV = v_stored * 1e6 if math.isfinite(v_stored) else float('nan')

                if (math.isfinite(v_ref_uV) and abs(v_ref_uV) > 5.0
                    and math.isfinite(v_stored_uV) and abs(v_stored_uV) < 0.1):
                    logger.warning(
                        f"NVM REL: {label} ACQ verification FAILED — "
                        f"measured {v_ref_uV:+.2f} µV but stored REF is "
                        f"{v_stored_uV:+.4f} µV. REL is ON but subtracting "
                        f"~0; raw thermal-EMF will show through. Try "
                        f"increasing auto_zero_rel_settle_s.")
                else:
                    logger.info(
                        f"NVM REL: {label} reference captured = {v_ref_uV:+.2f} µV "
                        f"(readback {v_stored_uV:+.2f} µV) — subtracted from "
                        f"all subsequent {label} readings")

                if math.isfinite(v_ref_uV) and abs(v_ref_uV) > max_uV:
                    logger.warning(
                        f"NVM REL: {label} offset {v_ref_uV:+.2f} µV exceeds "
                        f"{max_uV:.0f} µV threshold — check for stray signal "
                        f"or grounding issue. The offset is still subtracted.")
            except Exception as e:
                logger.warning(f"NVM REL: {label} zero failed ({e}); "
                                f"leaving REL OFF for this channel")
                try:
                    nvm.write("SENS:VOLT:DC:REF:STAT OFF")
                except Exception:
                    pass

        # Publish to dashboard
        v_xx = captured.get('Vxx')
        v_xy = captured.get('Vxy')
        try:
            self._publish(LiveData(
                phase=(f"NVM REL ready: "
                       f"Vxx offset = {v_xx*1e6:+.2f} µV, " if v_xx is not None and math.isfinite(v_xx) else "NVM REL ready: ")
                      + (f"Vxy offset = {v_xy*1e6:+.2f} µV" if v_xy is not None and math.isfinite(v_xy) else ""),
                rel_offset_vxx_uV=(v_xx * 1e6) if v_xx is not None and math.isfinite(v_xx) else None,
                rel_offset_vxy_uV=(v_xy * 1e6) if v_xy is not None and math.isfinite(v_xy) else None,
            ))
        except Exception:
            pass

    def _clear_nvm_rel(self):
        """Disable REL on both NVMs so the next sweep starts with a clean
        state rather than inheriting this sweep's reference. Uses only the
        confirmed-working STAT OFF command — we deliberately do NOT touch
        the stored REF value (which can be left non-zero; it's harmless
        when STAT is OFF, and the value-write form was the original
        source of error -113).
        """
        for nvm in (self.nvm1, self.nvm2):
            if not nvm: continue
            try:
                nvm.write("SENS:VOLT:DC:REF:STAT OFF")
                time.sleep(0.05)
                nvm.drain_errors(3)
            except Exception:
                pass

    def _configure_smu(self):
        if not self.smu: return
        ch = self._ch
        # ── Clear any leftover TSP state from a previous (possibly aborted) run.
        # A previous sweep that was Ctrl-C'd or crashed mid-script leaves
        # the TSP engine with an abandoned script. When the new sweep tries
        # to send any command, the engine surfaces the leftover state as
        # error -286 "TSP Runtime error: Script Aborted by User".
        # `<ch>.abort()` cancels any pending source/measure operation.
        # `errorqueue.clear()` wipes accumulated errors so we start fresh.
        # Both are no-ops if the engine is already idle.
        #
        # TSP/Lua gotcha: every statement must be an assignment, function call,
        # or control structure — bare expressions are NOT valid statements.
        # `{ch}.abort` (no parens) is a function reference, which parses as a
        # syntax error (-285 "Program syntax"). MUST write `{ch}.abort()` with
        # parens to make it a function call.
        try:
            self.smu.write(f"{ch}.abort()\nerrorqueue.clear()")
            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"SMU TSP state clear: {e}")
        i_range = 1e-3 if abs(self.config.I_const) <= 1e-3 else 1e-2
        self.smu.write(f"""
{ch}.reset()
{ch}.source.func = {ch}.OUTPUT_DCAMPS
{ch}.source.autorangei = {ch}.AUTORANGE_OFF
{ch}.source.rangei = {i_range}
{ch}.source.limitv = {self.config.v_limit}
{ch}.source.leveli = {self.config.I_const}
{ch}.measure.autorangev = {ch}.AUTORANGE_ON
{ch}.source.output = {ch}.OUTPUT_ON
""")
        time.sleep(0.5)
        # ── Drain any errors that the reset/config sequence may have raised.
        # Stops a stale error code from leaking into the next operation's
        # error-queue read.
        try:
            err = self.smu.query("print(errorqueue.next())").strip()
            if err and not err.startswith("0\t") and "0.00000e+00" not in err:
                logger.info(f"SMU config: cleared residual error: {err}")
        except Exception:
            pass

    def _open_data_file(self, group_key, group_val):
        """Open a new per-sweep data file, closing the previous one if needed."""
        if self._file_group == group_key and self._data_file:
            return  # already open for this group
        # Close previous file
        if self._data_file:
            try:
                self._data_file.flush()
                self._data_file.close()
            except Exception:
                pass
            self._data_file = None

        cfg = self.config
        folder = cfg.save_folder.strip() or "."
        import os
        os.makedirs(folder, exist_ok=True)

        # Source description for file header
        if getattr(cfg, 'source_mode', 'DC') in ('MFLI', 'MFLI_SINGLE', 'MFLI_DUAL'):
            I_ac    = cfg.mfli_output_amplitude / cfg.mfli_series_resistance
            src_str = (f"AC Lock-in | f={cfg.mfli_frequency:.2f} Hz | "
                       f"V_out={cfg.mfli_output_amplitude} V | "
                       f"Rs={cfg.mfli_series_resistance:.0f} Ohm | "
                       f"I_ac={I_ac:.3e} A")
            if getattr(cfg, 'source_mode', 'DC') == 'MFLI_DUAL':
                col1, col2 = "X_Vxx(V)", "X_Vxy(V)"   # in-phase Vxx, in-phase Vxy (Hall)
            else:
                col1, col2 = "X_Vxx(V)", "Y_Vxx(V)"   # in-phase / quadrature (single)
        else:
            src_str = f"DC | I={cfg.I_const} A"
            col1, col2 = "Vxx(V)", "Vxy(V)"

        if cfg.mode in ("STEP", "STEP2", "STEP3", "HYSTERESIS", "ANGLE_HYST"):
            vg_tag = ("_Vg%+.3fV" % self._V_gate_now) if self._V_gate_now is not None else ""
            mode_tag = "HYSTERESIS" if cfg.mode == "HYSTERESIS" else cfg.mode
            if cfg.mode == "ANGLE_HYST":
                # ANGLE_HYST groups by (T, θ) — group_val is the temperature; θ
                # and φ come from the active per-waypoint state set in the
                # _run_angle_hyst_mode loop.
                th = float(getattr(self, '_angle_theta_now', 0.0))
                ph = float(getattr(self, '_angle_phi_now',   0.0))
                fname = (cfg.sample_name + f"_{mode_tag}_" +
                         ("%.3f" % group_val) + "K" +
                         f"_th{th:+07.3f}deg" + f"_phi{ph:+07.3f}deg" +
                         vg_tag + ".txt")
                vg_hdr = f"  |  Vgate={self._V_gate_now:+.3f} V" if self._V_gate_now is not None else ""
                h1 = (f"# Mode={cfg.mode}  |  {src_str}  |  "
                      f"Temperature={group_val:.3f} K  |  theta={th:+.3f}deg  phi={ph:+.3f}deg"
                      f"  |  axis_limits Bx_max={cfg.Bx_max} T By_max={cfg.By_max} T Bz_max={cfg.Bz_max} T"
                      f"{vg_hdr}\n")
                h2 = (f"# B(T)\t{col1}\t{col2}\tRxx(Ohm)\tRxy(Ohm)\t"
                      f"Mobility(cm2/Vs)\tCarrierDensity(cm-2)\ttimestamp(s)\tVgate(V)\t"
                      f"Bx(T)\tBy(T)\tBz(T)\n")
            else:
                fname = cfg.sample_name + f"_{mode_tag}_" + ("%.3f" % group_val) + "K" + vg_tag + ".txt"
                vg_hdr = f"  |  Vgate={self._V_gate_now:+.3f} V" if self._V_gate_now is not None else ""
                h1 = f"# Mode={cfg.mode}  |  {src_str}  |  Temperature={group_val:.3f} K{vg_hdr}\n"
                h2 = f"# B(T)\t{col1}\t{col2}\tRxx(Ohm)\tRxy(Ohm)\tMobility(cm2/Vs)\tCarrierDensity(cm-2)\ttimestamp(s)\tVgate(V)\n"
        else:
            vg_tag = ("_Vg%+.3fV" % self._V_gate_now) if self._V_gate_now is not None else ""
            fname = cfg.sample_name + "_RAMP_" + ("%+.5f" % group_val) + "T" + vg_tag + ".txt"
            vg_hdr = f"  |  Vgate={self._V_gate_now:+.3f} V" if self._V_gate_now is not None else ""
            h1 = f"# Mode=RAMP  |  {src_str}  |  Field={group_val:+.5f} T{vg_hdr}\n"
            h2 = f"# T(K)\t{col1}\t{col2}\tRxx(Ohm)\tRxy(Ohm)\tMobility(cm2/Vs)\tCarrierDensity(cm-2)\ttimestamp(s)\tVgate(V)\n"

        notes = getattr(cfg, 'sweep_notes', '').strip()
        h_notes = f"# Notes: {notes}\n" if notes else ""

        fpath = os.path.join(folder, fname)
        # Anti-overwrite: if the file already exists, find the next free name
        # by appending (1), (2), ... before the extension. Logs a notice so the
        # user can see in the system log that auto-renaming happened.
        original_fpath = fpath
        fpath = _unique_path(fpath)
        if fpath != original_fpath:
            logger.info(
                f"Output file already exists. Auto-renamed to avoid overwrite:\n"
                f"  Wanted:  {os.path.basename(original_fpath)}\n"
                f"  Using:   {os.path.basename(fpath)}"
            )
            self._publish(LiveData(phase=
                f"File exists — saving as {os.path.basename(fpath)} (auto-renamed)"))
        self._data_file  = open(fpath, "w", buffering=1, encoding="utf-8")
        self._file_group = group_key
        self._data_file.write(h1)
        if h_notes:
            self._data_file.write(h_notes)
        self._data_file.write(h2)
        logger.info("Data file opened: " + fpath)
        self._publish(LiveData(progress="Saving to " + fname))

    def _add_point(self, t0, T_set, T_now, B_set, B_now, meas):
        if not self.armed:
            return   # silently drop any point before initial conditions are met

        # ── FUNDAMENTAL GUARD: reject points where B hasn't reached target ──
        # If the magnet timed out during _wait_B, B_now can be far from B_set.
        # Logging such points pollutes the data file with return-sweep artefacts.
        if self.config.mode in ("STEP", "STEP2", "STEP3", "HYSTERESIS", "ANGLE_HYST"):
            B_tolerance = max(abs(self.config.B_step) * 3, self.config.tol_B * 5, 0.05)
            if abs(B_now - B_set) > B_tolerance:
                logger.debug(
                    f"_add_point REJECTED: B_set={B_set:.4f} but B_now={B_now:.4f} "
                    f"(|err|={abs(B_now-B_set):.4f} > tol={B_tolerance:.4f})")
                return  # skip this point — magnet hasn't settled
        self._n_pts = getattr(self, '_n_pts', 0) + 1
        Ip    = meas["Ip_m"]
        I_eff = meas["I_eff"]
        Rxx   = meas["Rxx"]
        Rxy   = meas["Rxy"]
        # Voltage computation is mode-specific:
        #   DC  — positive current only; V = Vxxp_m directly (no reversal)
        #         (Vxxm_m is set to −Vxxp_m internally for formula compatibility)
        #   AC  — use in-phase demodulator output directly; phase-sensitive detection
        #         already rejects DC offsets; current reversal is not applicable.
        _ac = getattr(self.config, 'source_mode', 'DC') in ('MFLI', 'MFLI_DUAL', 'MFLI_SINGLE')
        if _ac:
            Vxx = meas["Vxxp_m"]   # X_master in-phase longitudinal voltage
            Vxy = meas["Vxyp_m"]   # X_slave  in-phase Hall voltage (NaN in single mode)
        else:
            # DC positive-current measurement — (Vp − (−Vp))/2 = Vp
            Vxx = (meas["Vxxp_m"] - meas["Vxxm_m"]) / 2.0
            Vxy = (meas["Vxyp_m"] - meas["Vxym_m"]) / 2.0
        # Cache the actual T/B at measurement time
        if T_now and T_now > 0: self._last_T_now = T_now
        if B_now is not None:   self._last_B_now = B_now
        ts = time.time() - t0

        # ── Real-time physics metrics (gated by config flag) ──────────────────
        mobility = carrier_density = hall_coefficient = anomaly = None
        if getattr(self.config, 'enable_anomaly_detection', True):
            # Maintain rolling history (100 pts max)
            self._B_hist.append(B_now);   self._Rxx_hist.append(Rxx);   self._Rxy_hist.append(Rxy)
            if len(self._B_hist) > 100:
                self._B_hist.pop(0); self._Rxx_hist.pop(0); self._Rxy_hist.pop(0)

            # Hall mobility + carrier density — only meaningful away from B=0
            if abs(B_now) >= 0.01:
                result = self.mobility_calc.compute(Rxx, Rxy, B_now)
                if result:
                    mobility        = result['mobility_cm2']
                    carrier_density = result['carrier_density_cm2']
                    hall_coefficient = result['hall_coefficient']

            # Spike detection on Rxx — flags sudden jumps (contact issues, etc.)
            if self.peak_detector.detect(Rxx):
                anomaly = f"Rxx spike: {Rxx:.4g} Ω at {'B' if self.config.mode in ('STEP','STEP2','STEP3','HYSTERESIS','ANGLE_HYST') else 'T'}={B_now if self.config.mode in ('STEP','STEP2','STEP3','HYSTERESIS','ANGLE_HYST') else T_now:.4g}"
                logger.warning("Anomaly — " + anomaly)

        # ── Compute sweep progress and ETA ────────────────────────────────────
        total_pts    = getattr(self, '_total_pts', 0)
        n            = self._n_pts
        elapsed      = time.time() - getattr(self, '_sweep_t0', time.time())
        if total_pts > 0 and n > 0:
            frac     = min(1.0, n / total_pts)
            t_per_pt = elapsed / n
            eta      = t_per_pt * (total_pts - n)
        else:
            frac = eta = None

        # ── Single combined LiveData publish per measurement point ─────────────
        # Merging the readings and main_x into one message reduces queue traffic
        # and ensures the frontend sticky T/B values are always up-to-date when
        # the trace key is computed.
        x_axis = B_now if self.config.mode in ("STEP", "STEP2", "STEP3", "HYSTERESIS", "ANGLE_HYST") else T_now
        self._publish(LiveData(
            I_mA=I_eff*1000 if np.isfinite(I_eff) else None,
            Vxx_V=Vxx, Vxy_V=Vxy,
            Rxx_Ohm=Rxx, Rxy_Ohm=Rxy,
            T_K=T_now, B_T=B_now, t_s=ts,
            main_x=x_axis, main_Vxx=Vxx, main_Vxy=Vxy,
            main_Rxx=Rxx, main_Rxy=Rxy,
            sweep_mode=self.config.mode,
            mobility=clean(mobility),
            carrier_density=clean(carrier_density),
            hall_coefficient=clean(hall_coefficient),
            anomaly=anomaly,
            progress_frac=frac,
            n_pts=n,
            total_pts=total_pts if total_pts > 0 else None,
            eta_s=clean(eta),
            V_gate=self._V_gate_now,
            rms_noise_mOhm=clean(meas.get('rms_noise_mOhm')),
        ))

        # ── Data file write ────────────────────────────────────────────────────
        mu_str = ("%.4e" % mobility)        if mobility        is not None else "nan"
        ns_str = ("%.4e" % carrier_density) if carrier_density is not None else "nan"
        if self.config.mode in ("STEP", "STEP2", "STEP3", "HYSTERESIS", "ANGLE_HYST"):
            if self.config.mode == "ANGLE_HYST":
                # Group by (T, θ, φ) so each angular waypoint gets its own file
                _th = round(float(getattr(self, '_angle_theta_now', 0.0)), 4)
                _ph = round(float(getattr(self, '_angle_phi_now',   0.0)), 4)
                self._open_data_file((round(T_set, 6), _th, _ph), T_set)
            else:
                self._open_data_file(round(T_set, 6), T_set)
            if self._data_file:
                vg_str = ("%.4f" % self._V_gate_now) if self._V_gate_now is not None else "nan"
                if self.config.mode == "ANGLE_HYST":
                    # Append per-axis readback columns (calibration analysis needs
                    # the Cartesian components, not just the projected scalar)
                    bx = float(getattr(self, '_angle_Bx_now', float('nan')))
                    by = float(getattr(self, '_angle_By_now', float('nan')))
                    bz = float(getattr(self, '_angle_Bz_now', float('nan')))
                    row = "%.6f\t%.9f\t%.9f\t%.6f\t%.6f\t%s\t%s\t%.3f\t%s\t%.6f\t%.6f\t%.6f\n" % (
                        B_now, Vxx, Vxy, Rxx, Rxy, mu_str, ns_str, ts, vg_str, bx, by, bz)
                else:
                    row = "%.6f\t%.9f\t%.9f\t%.6f\t%.6f\t%s\t%s\t%.3f\t%s\n" % (
                        B_now, Vxx, Vxy, Rxx, Rxy, mu_str, ns_str, ts, vg_str)
                self._data_file.write(row)
        else:
            self._open_data_file(round(B_set, 9), B_set)
            if self._data_file:
                vg_str = ("%.4f" % self._V_gate_now) if self._V_gate_now is not None else "nan"
                row = "%.6f\t%.9f\t%.9f\t%.6f\t%.6f\t%s\t%s\t%.3f\t%s\n" % (
                    T_now, Vxx, Vxy, Rxx, Rxy, mu_str, ns_str, ts, vg_str)
                self._data_file.write(row)

    def _run_step_mode(self, t0):
        # ── Build T_points safely (handles single-T case T_start==T_end) ──
        T_start = float(self.config.T_start)
        T_end   = float(self.config.T_end)
        T_step  = float(self.config.T_step)
        if abs(T_end - T_start) < 1e-9:
            # Single-temperature sweep — protocol's "queued at one T" pattern
            T_points = np.array([T_start])
        elif abs(T_step) < 1e-9:
            # User asked for a range but step is 0 → fall back to single point
            logger.warning("STEP: T_step is 0 but T_start != T_end — running single point at T_start")
            T_points = np.array([T_start])
        else:
            T_points = np.arange(T_start, T_end + T_step / 2, T_step)
            if len(T_points) == 0:
                T_points = np.array([T_start])
        # ── B sweep: 0 → +Bmax only (no ±B hysteresis loop) ──────────────
        B_loop      = self._build_B_step_sequence(0, abs(self.config.B_max), abs(self.config.B_step))
        B_step_fine = float(getattr(self.config, 'B_step_fine', 0.0))
        adaptive    = B_step_fine > 0

        # Gate voltage points (single point [0.0] when gate disabled)
        gate_on  = bool(getattr(self.config, 'gate_enable', False))
        if gate_on:
            Vg_points = list(np.arange(
                self.config.gate_start,
                self.config.gate_end + self.config.gate_step / 2 * np.sign(self.config.gate_step),
                self.config.gate_step))
            if not Vg_points or abs(Vg_points[-1] - self.config.gate_end) > abs(self.config.gate_step) / 2:
                Vg_points.append(round(self.config.gate_end, 9))
        else:
            Vg_points = [None]

        self._total_pts = len(T_points) * len(Vg_points) * len(B_loop)
        self._sweep_t0  = t0

        self._publish(LiveData(phase="STEP: initial field reset → B = 0 T", sweep_mode="STEP"))
        self._wait_B(0.0, t0)
        self._publish(LiveData(phase=f"STEP: waiting for T_start = {self.config.T_start:.3f} K"))
        T_now = self._wait_T(self.config.T_start, t0)
        self._publish(LiveData(
            phase=f"STEP: initial conditions met — T={T_now:.3f}K, B=0 T. Starting sweep."))
        self.armed = True

        for T_set in T_points:
            self._check_stop()
            if abs(T_set - self.config.T_start) > 1e-9:
                self._publish(LiveData(phase=f"STEP: T → {T_set:.3f}K"))
                T_now = self._wait_T(T_set, t0)

            # ── Gate voltage outer loop ────────────────────────────────────
            for Vg in Vg_points:
                self._check_stop()
                I_leak = 0.0
                if gate_on and Vg is not None:
                    I_leak = self._apply_gate(Vg)
                    self._V_gate_now = Vg
                else:
                    self._V_gate_now = None

                self._publish(LiveData(
                    phase=f"STEP: B sweep 0 → +{abs(self.config.B_max):.3f}T"
                          + (f"  Vg={Vg:+.3f}V" if gate_on else ""),
                    V_gate=self._V_gate_now, I_leak=I_leak if gate_on else None))

                # ── Verify B is actually at 0 before starting forward sweep ──
                # If the previous return-to-zero timed out, B might still be
                # at a high value. Wait here until B reaches 0 for real.
                if self._last_B_now is not None and abs(self._last_B_now) > 0.1:
                    self._publish(LiveData(
                        phase=f"STEP: waiting for B to reach 0 (currently {self._last_B_now:+.3f} T)"))
                    logger.warning(f"STEP: B={self._last_B_now:+.4f}T at sweep start — re-waiting for B=0")
                    self.armed = False
                    self._wait_B(0.0, t0)
                    self.armed = True

                if not adaptive:
                    # ── Standard fixed-step B sweep: 0 → Bmax ─────────────
                    for B_set in B_loop:
                        self._check_stop()
                        B_now, _ = self._wait_B(B_set, t0)
                        meas = self._measure()
                        self._add_point(t0, T_set, T_now, B_set, B_now, meas)
                else:
                    # ── Adaptive-step B sweep: 0 → Bmax ────────────────────
                    B_coarse = abs(self.config.B_step)
                    B_fine   = abs(B_step_fine)
                    B_current = 0.0
                    B_end_val = abs(self.config.B_max)

                    # First point at B = 0
                    B_now, _ = self._wait_B(B_current, t0)
                    meas = self._measure()
                    self._add_point(t0, T_set, T_now, B_current, B_now, meas)
                    rxx_buf  = [meas['Rxx']]
                    state_ab = 'COARSE'
                    mono_cnt = 0

                    while True:
                        self._check_stop()
                        step      = B_fine if state_ab == 'FINE' else B_coarse
                        B_next    = round(B_current + step, 9)
                        if B_next > B_end_val:
                            B_next = B_end_val

                        B_now, _ = self._wait_B(B_next, t0)
                        meas = self._measure()
                        self._add_point(t0, T_set, T_now, B_next, B_now, meas)

                        rxx_buf.append(meas['Rxx'])
                        if len(rxx_buf) > 6: rxx_buf.pop(0)
                        if len(rxx_buf) >= 3:
                            d1, d2 = rxx_buf[-1]-rxx_buf[-2], rxx_buf[-2]-rxx_buf[-3]
                            if state_ab == 'COARSE' and d1*d2 < 0:
                                state_ab = 'FINE'; mono_cnt = 0
                            elif state_ab == 'FINE':
                                mono_cnt = mono_cnt+1 if d1*d2 >= 0 else 0
                                if mono_cnt >= 3:
                                    state_ab = 'COARSE'
                        B_current = B_next
                        if abs(B_current - B_end_val) < 1e-9:
                            break

                # ── Return B to 0 before next gate/temp step ──────────────
                # CRITICAL: disable logging so no data is recorded during
                # the downward ramp from Bmax → 0
                self.armed = False
                self._publish(LiveData(
                    phase=f"STEP: returning B → 0 (no logging)"))
                self._wait_B(0.0, t0)
                self.armed = True

        self._publish(LiveData(phase="STEP completed"))


    def _run_step2_mode(self, t0):
        """STEP2: B sweep 0 → Bmax at the current (manually-set) temperature.

        Identical to STEP mode but with NO temperature control.
        The ITC temperature is read for logging/file naming only.
        """
        # ── B sweep: 0 → +Bmax only ──────────────────────────────────────
        B_loop      = self._build_B_step_sequence(0, abs(self.config.B_max), abs(self.config.B_step))
        B_step_fine = float(getattr(self.config, 'B_step_fine', 0.0))
        adaptive    = B_step_fine > 0

        # Gate voltage points (single point [None] when gate disabled)
        gate_on  = bool(getattr(self.config, 'gate_enable', False))
        if gate_on:
            Vg_points = list(np.arange(
                self.config.gate_start,
                self.config.gate_end + self.config.gate_step / 2 * np.sign(self.config.gate_step),
                self.config.gate_step))
            if not Vg_points or abs(Vg_points[-1] - self.config.gate_end) > abs(self.config.gate_step) / 2:
                Vg_points.append(round(self.config.gate_end, 9))
        else:
            Vg_points = [None]

        self._total_pts = len(Vg_points) * len(B_loop)
        self._sweep_t0  = t0

        self._publish(LiveData(phase="STEP2: initial field reset → B = 0 T", sweep_mode="STEP2"))
        self._wait_B(0.0, t0)

        # Read current temperature (no control — user sets this manually)
        T_now = None
        if self.itc:
            try:
                T_now = self.itc.read_temperature(self.config.temp_device)
            except Exception:
                pass
        T_now = T_now or 0.0
        T_label = round(T_now, 3)

        self._publish(LiveData(
            phase=f"STEP2: T = {T_now:.3f} K (manual) — starting B sweep",
            T_K=T_now))
        self.armed = True

        # ── Gate voltage loop ──────────────────────────────────────────────
        for Vg in Vg_points:
            self._check_stop()
            I_leak = 0.0
            if gate_on and Vg is not None:
                I_leak = self._apply_gate(Vg)
                self._V_gate_now = Vg
            else:
                self._V_gate_now = None

            self._publish(LiveData(
                phase=f"STEP2: B sweep 0 → +{abs(self.config.B_max):.3f}T"
                      + (f"  Vg={Vg:+.3f}V" if gate_on else ""),
                V_gate=self._V_gate_now, I_leak=I_leak if gate_on else None))

            if not adaptive:
                # ── Standard fixed-step B sweep: 0 → Bmax ─────────────
                for B_set in B_loop:
                    self._check_stop()
                    # Re-read T (just for logging, not controlling)
                    if self.itc:
                        try:
                            T_now = self.itc.read_temperature(self.config.temp_device) or T_now
                        except Exception:
                            pass
                    B_now, _ = self._wait_B(B_set, t0)
                    meas = self._measure()
                    self._add_point(t0, T_label, T_now, B_set, B_now, meas)
            else:
                # ── Adaptive-step B sweep: 0 → Bmax ────────────────────
                B_coarse = abs(self.config.B_step)
                B_fine   = abs(B_step_fine)
                B_current = 0.0
                B_end_val = abs(self.config.B_max)

                # First point at B = 0
                if self.itc:
                    try:
                        T_now = self.itc.read_temperature(self.config.temp_device) or T_now
                    except Exception:
                        pass
                B_now, _ = self._wait_B(B_current, t0)
                meas = self._measure()
                self._add_point(t0, T_label, T_now, B_current, B_now, meas)
                rxx_buf  = [meas['Rxx']]
                state_ab = 'COARSE'
                mono_cnt = 0

                while True:
                    self._check_stop()
                    step      = B_fine if state_ab == 'FINE' else B_coarse
                    B_next    = round(B_current + step, 9)
                    if B_next > B_end_val:
                        B_next = B_end_val

                    if self.itc:
                        try:
                            T_now = self.itc.read_temperature(self.config.temp_device) or T_now
                        except Exception:
                            pass
                    B_now, _ = self._wait_B(B_next, t0)
                    meas = self._measure()
                    self._add_point(t0, T_label, T_now, B_next, B_now, meas)

                    rxx_buf.append(meas['Rxx'])
                    if len(rxx_buf) > 6: rxx_buf.pop(0)
                    if len(rxx_buf) >= 3:
                        d1, d2 = rxx_buf[-1]-rxx_buf[-2], rxx_buf[-2]-rxx_buf[-3]
                        if state_ab == 'COARSE' and d1*d2 < 0:
                            state_ab = 'FINE'; mono_cnt = 0
                        elif state_ab == 'FINE':
                            mono_cnt = mono_cnt+1 if d1*d2 >= 0 else 0
                            if mono_cnt >= 3:
                                state_ab = 'COARSE'
                    B_current = B_next
                    if abs(B_current - B_end_val) < 1e-9:
                        break

            # ── Return B to 0 before next gate step ───────────────────
            self.armed = False
            self._wait_B(0.0, t0)
            self.armed = True

        self._publish(LiveData(phase="STEP2 completed"))


    def _verify_B_at_start(self, B_start_cfg, t0, context=""):
        """Verify that B has actually reached B_start. Returns True if OK.

        If the field did not settle within tolerance after _wait_B, this
        method logs a warning, publishes an error phase, and returns False.
        The caller can then decide whether to retry or skip.
        """
        B_actual = self._last_B_now or 0.0
        tol = self.config.tol_B * 3  # allow 3× normal tolerance for the initial ramp
        if abs(B_actual - B_start_cfg) <= tol:
            return True
        # Field did NOT reach B_start
        msg = (f"STEP3 {context}: B failed to reach B_start = {B_start_cfg:+.4f} T  "
               f"(actual = {B_actual:+.4f} T, "
               f"error = {abs(B_actual - B_start_cfg):.4f} T, "
               f"tol = {tol:.4f} T)")
        self.logger.error(msg)
        self._publish(LiveData(
            phase=f"⚠ {msg}",
            progress=msg,
            B_T=B_actual))
        return False

    def _run_step3_mode(self, t0):
        """STEP3: B sweep from B_start → B_max at each temperature.

        Like STEP mode but with a configurable B_start (can be negative).
        Temperature loop is present. B_step is rebuilt identically for every
        temperature to guarantee consistent field coverage.

        CRITICAL: Data logging begins ONLY after B is verified at B_start.
        If B fails to reach B_start (timeout, magnet trip, etc.), the sweep
        for that temperature is skipped and an error is logged.
        """
        # ── Build T_points safely (handles single-T case T_start==T_end) ──
        T_start_cfg = float(self.config.T_start)
        T_end_cfg   = float(self.config.T_end)
        T_step_cfg  = float(self.config.T_step)
        if abs(T_end_cfg - T_start_cfg) < 1e-9:
            T_points = np.array([T_start_cfg])
        elif abs(T_step_cfg) < 1e-9:
            logger.warning("STEP3: T_step is 0 but T_start != T_end — running single point at T_start")
            T_points = np.array([T_start_cfg])
        else:
            T_points = np.arange(T_start_cfg, T_end_cfg + T_step_cfg / 2, T_step_cfg)
            if len(T_points) == 0:
                T_points = np.array([T_start_cfg])
        # ── B parameters — captured ONCE, used for every T ────────────────
        B_start_cfg = float(self.config.B_start)
        B_max_cfg   = float(self.config.B_max)
        B_step_cfg  = float(self.config.B_step)
        B_step_fine = float(getattr(self.config, 'B_step_fine', 0.0))
        adaptive    = B_step_fine > 0

        # Build the B sequence once — reused identically at every temperature
        B_loop = self._build_B_step_sequence(B_start_cfg, B_max_cfg, B_step_cfg)

        # Gate voltage points
        gate_on = bool(getattr(self.config, 'gate_enable', False))
        if gate_on:
            Vg_points = list(np.arange(
                self.config.gate_start,
                self.config.gate_end + self.config.gate_step / 2 * np.sign(self.config.gate_step),
                self.config.gate_step))
            if not Vg_points or abs(Vg_points[-1] - self.config.gate_end) > abs(self.config.gate_step) / 2:
                Vg_points.append(round(self.config.gate_end, 9))
        else:
            Vg_points = [None]

        self._total_pts = len(T_points) * len(Vg_points) * len(B_loop)
        self._sweep_t0  = t0

        # ── Initial ramp to B_start ───────────────────────────────────────
        self._publish(LiveData(
            phase=f"STEP3: ramping to B_start = {B_start_cfg:+.3f} T",
            sweep_mode="STEP3"))
        self._wait_B(B_start_cfg, t0)

        # Verify B actually reached B_start before doing anything else
        if not self._verify_B_at_start(B_start_cfg, t0, context="initial ramp"):
            # Retry once
            self._publish(LiveData(
                phase=f"STEP3: retrying ramp to B_start = {B_start_cfg:+.3f} T"))
            self.logger.warning("STEP3: first attempt to reach B_start failed — retrying")
            self._wait_B(B_start_cfg, t0)
            if not self._verify_B_at_start(B_start_cfg, t0, context="retry"):
                self._publish(LiveData(
                    phase=f"STEP3: ABORTED — cannot reach B_start = {B_start_cfg:+.3f} T "
                          f"(actual = {self._last_B_now:+.4f} T)",
                    progress=f"STEP3 aborted: B stuck at {self._last_B_now:+.4f} T"))
                self.logger.error(
                    f"STEP3 ABORTED: B_start={B_start_cfg:+.4f} T unreachable "
                    f"(actual={self._last_B_now:+.4f} T after 2 attempts)")
                return

        self._publish(LiveData(
            phase=f"STEP3: B confirmed at {self._last_B_now:+.4f} T. "
                  f"Waiting for T_start = {self.config.T_start:.3f} K"))
        T_now = self._wait_T(self.config.T_start, t0)
        self._publish(LiveData(
            phase=f"STEP3: T={T_now:.3f}K, B={self._last_B_now:+.4f}T. Starting sweep."))
        self.armed = True

        for T_idx, T_set in enumerate(T_points):
            self._check_stop()
            if abs(T_set - self.config.T_start) > 1e-9:
                self._publish(LiveData(phase=f"STEP3: T → {T_set:.3f}K"))
                T_now = self._wait_T(T_set, t0)

            for Vg in Vg_points:
                self._check_stop()
                I_leak = 0.0
                if gate_on and Vg is not None:
                    I_leak = self._apply_gate(Vg)
                    self._V_gate_now = Vg
                else:
                    self._V_gate_now = None

                # ── Verify B is at B_start before this sweep ──────────────
                # (either from initial ramp or return-to-B_start at end of
                #  the previous gate/temp iteration)
                if not self._verify_B_at_start(B_start_cfg, t0,
                        context=f"T={T_set:.3f}K pre-sweep"):
                    # Try to ramp there
                    self._publish(LiveData(
                        phase=f"STEP3: T={T_set:.3f}K — re-ramping to "
                              f"B_start = {B_start_cfg:+.3f} T"))
                    self.logger.warning(
                        f"STEP3 T={T_set:.3f}K: B not at B_start, re-ramping")
                    self._wait_B(B_start_cfg, t0)
                    if not self._verify_B_at_start(B_start_cfg, t0,
                            context=f"T={T_set:.3f}K re-ramp"):
                        self._publish(LiveData(
                            phase=f"⚠ STEP3: SKIPPING T={T_set:.3f}K — "
                                  f"B stuck at {self._last_B_now:+.4f} T",
                            progress=f"STEP3: skipped T={T_set:.3f}K "
                                     f"(B={self._last_B_now:+.4f}T)"))
                        self.logger.error(
                            f"STEP3: SKIPPING T={T_set:.3f}K sweep — "
                            f"B={self._last_B_now:+.4f}T, "
                            f"target B_start={B_start_cfg:+.4f}T")
                        continue  # skip this T, move to the next

                self._publish(LiveData(
                    phase=f"STEP3: T={T_set:.3f}K  B sweep "
                          f"{B_start_cfg:+.3f} → {B_max_cfg:+.3f}T  "
                          f"step={B_step_cfg:.4f}T  ({len(B_loop)} pts)"
                          + (f"  Vg={Vg:+.3f}V" if gate_on else ""),
                    V_gate=self._V_gate_now,
                    I_leak=I_leak if gate_on else None))

                if not adaptive:
                    # ── Standard fixed-step: B_start → B_max ──────────────
                    for B_set in B_loop:
                        self._check_stop()
                        B_now, _ = self._wait_B(B_set, t0)
                        meas = self._measure()
                        self._add_point(t0, T_set, T_now, B_set, B_now, meas)
                else:
                    # ── Adaptive-step: B_start → B_max ────────────────────
                    B_coarse  = abs(B_step_cfg)
                    B_fine    = abs(B_step_fine)
                    B_current = B_start_cfg
                    B_end_val = B_max_cfg
                    direction = 1.0 if B_end_val >= B_start_cfg else -1.0

                    # First point
                    B_now, _ = self._wait_B(B_current, t0)
                    meas = self._measure()
                    self._add_point(t0, T_set, T_now, B_current, B_now, meas)
                    rxx_buf  = [meas['Rxx']]
                    state_ab = 'COARSE'
                    mono_cnt = 0

                    while True:
                        self._check_stop()
                        step   = B_fine if state_ab == 'FINE' else B_coarse
                        B_next = round(B_current + direction * step, 9)
                        if direction > 0 and B_next > B_end_val:
                            B_next = B_end_val
                        elif direction < 0 and B_next < B_end_val:
                            B_next = B_end_val

                        B_now, _ = self._wait_B(B_next, t0)
                        meas = self._measure()
                        self._add_point(t0, T_set, T_now, B_next, B_now, meas)

                        rxx_buf.append(meas['Rxx'])
                        if len(rxx_buf) > 6: rxx_buf.pop(0)
                        if len(rxx_buf) >= 3:
                            d1, d2 = rxx_buf[-1]-rxx_buf[-2], rxx_buf[-2]-rxx_buf[-3]
                            if state_ab == 'COARSE' and d1*d2 < 0:
                                state_ab = 'FINE'; mono_cnt = 0
                            elif state_ab == 'FINE':
                                mono_cnt = mono_cnt+1 if d1*d2 >= 0 else 0
                                if mono_cnt >= 3:
                                    state_ab = 'COARSE'
                        B_current = B_next
                        if abs(B_current - B_end_val) < 1e-9:
                            break

                # ── Return to B_start before next gate/temp step ──────────
                self.armed = False
                self._publish(LiveData(
                    phase=f"STEP3: T={T_set:.3f}K sweep done — "
                          f"returning to B_start = {B_start_cfg:+.3f} T (no logging)"))
                self._wait_B(B_start_cfg, t0)
                self.armed = True

        self._publish(LiveData(phase="STEP3 completed"))


    def _run_ramp_mode(self, t0):
        # ── Hard requirement: RAMP cannot work without iTC ────────────────
        # RAMP's contract is "T rises at a constant rate controlled by iTC".
        # Without iTC, the polling loop would spin forever waiting for T to
        # rise (since T_now reads as 0). Fail fast with a clear message.
        # The IPS can still be offline — that's the passive case we DO support
        # (data file will record B as NaN).
        if self.itc is None:
            msg = ("RAMP cannot run without iTC — it needs the controller to "
                   "ramp T at constant rate. iTC is offline. If you just want "
                   "to test the workflow, use TCSCAN passive mode instead.")
            logger.error(msg)
            self._publish(LiveData(phase=msg, sweep_mode="RAMP"))
            return

        # ════════════════════════════════════════════════════════════════════
        # SAFETY VALIDATION — refuse to start if requested parameters could
        # drive the cryostat to dangerous temperatures.
        #
        # A prior incident: with T_end accidentally set high and T_ramp_rate
        # high, RAMP commanded the iTC to ramp probe + VTI to ~75 K in a few
        # minutes (VTI tracked the probe at the same rate). The app's job is
        # to refuse such commands, not pass them straight to the iTC.
        # ════════════════════════════════════════════════════════════════════
        cfg = self.config
        T_max_cap  = float(getattr(cfg, 'ramp_T_max_K', 30.0))
        rate_cap   = float(getattr(cfg, 'ramp_rate_max_K_per_min', 5.0))
        vti_T_cap  = float(getattr(cfg, 'vti_T_max_K', 50.0))
        vti_rate   = float(getattr(cfg, 'vti_rate_max_K_per_min', 1.0))
        arm_delay  = float(getattr(cfg, 'ramp_pre_arm_delay_s', 5.0))
        overshoot_K= float(getattr(cfg, 'ramp_overshoot_abort_K', 2.0))

        violations = []
        if cfg.T_end > T_max_cap:
            violations.append(
                f"T_end={cfg.T_end:.3f}K exceeds safety cap T_max_cap={T_max_cap:.1f}K "
                f"(field name: ramp_T_max_K)")
        if cfg.T_end < 0:
            violations.append(f"T_end={cfg.T_end:.3f}K is negative")
        if cfg.T_ramp_rate > rate_cap:
            violations.append(
                f"T_ramp_rate={cfg.T_ramp_rate:.3f}K/min exceeds safety cap "
                f"rate_cap={rate_cap:.2f}K/min (field name: ramp_rate_max_K_per_min)")
        if cfg.T_ramp_rate <= 0:
            violations.append(f"T_ramp_rate={cfg.T_ramp_rate:.3f}K/min must be > 0")
        if cfg.T_start < 0:
            violations.append(f"T_start={cfg.T_start:.3f}K is negative")
        # ── VTI offset must keep VTI below probe (per spec). A non-positive
        # offset would let VTI track the probe at the same setpoint or above,
        # which defeats the purpose of having a VTI heater loop.
        _vti_off_cfg = float(getattr(cfg, 'vti_offset', 1.0))
        if _vti_off_cfg < 0.1:
            violations.append(
                f"vti_offset={_vti_off_cfg:.3f}K is below 0.1K — VTI must stay "
                f"below the probe setpoint by a real margin. Set vti_offset>=0.5K."
            )
        if violations:
            msg = ("RAMP REFUSED TO START — safety check failed:\n  - "
                   + "\n  - ".join(violations)
                   + "\n\nTo override a cap intentionally, raise the corresponding "
                   "field in your config (e.g. ramp_T_max_K). These caps exist to "
                   "prevent runaway iTC commands.")
            logger.error(msg)
            self._publish(LiveData(phase=("RAMP REFUSED: " + violations[0]),
                                   sweep_mode="RAMP"))
            return

        # ── Stash safety values on self so the polling loop can access them ──
        self._ramp_safety_overshoot_K = overshoot_K
        self._ramp_safety_vti_T_cap   = vti_T_cap
        self._ramp_safety_vti_rate    = vti_rate

        # ── Concise pre-flight log (no big banner) + short 3 s pause ──────
        # The pre-flight refusal above already caught dangerous configs.
        # We just log one line summarising the trajectory and give a tiny
        # window in case the user spots a typo. The polling loop's overshoot
        # watchdog and VTI rate decoupling are the real safety net at runtime.
        _vti_planned = min(vti_T_cap, max(1.5, cfg.T_end - float(getattr(cfg, 'vti_offset', 1.0))))
        _est_min = abs(cfg.T_end - cfg.T_start) / max(1e-6, cfg.T_ramp_rate)
        logger.info(
            f"RAMP starting: probe {cfg.T_start:.2f}K -> {cfg.T_end:.2f}K @ "
            f"{cfg.T_ramp_rate:.3f}K/min, VTI -> {_vti_planned:.2f}K @ "
            f"{vti_rate:.3f}K/min (independent), dT={abs(cfg.T_delta):.3f}K, "
            f"est. {_est_min:.1f} min. Starting in 3 s — click STOP to abort."
        )
        self._publish(LiveData(
            phase=(f"RAMP: probe {cfg.T_start:.2f}->{cfg.T_end:.2f}K @ "
                   f"{cfg.T_ramp_rate:.3f}K/min, dT={abs(cfg.T_delta):.3f}K, "
                   f"est. {_est_min:.1f} min"),
            sweep_mode="RAMP"))
        _arm_start = time.time()
        while time.time() - _arm_start < 3.0:
            self._check_stop()
            time.sleep(0.5)

        B_points = self._build_B_step_sequence(
            self.config.B_start, self.config.B_end, self.config.B_step)
        n_T_pts = max(1, int(abs(self.config.T_end - self.config.T_start)
                              / max(1e-12, abs(self.config.T_delta))) + 1)

        # ── Pre-sweep log: announce the active fine-tuning and the expected
        # T-drift per measurement, so the user can decide if their ramp rate
        # is appropriate. With current_reverse=ON + avg_n=N, each measurement
        # takes ~2·rev_settle·N + (NPLC/50)·2·N seconds (settle + NVM reads).
        # During that window, T continues to rise; the drift = rate × time.
        _avg_n = max(1, int(getattr(self.config, 'avg_n', 1)))
        _rev_settle = float(getattr(self.config, 'reverse_settle_s', 0.1))
        _nplc = float(getattr(self.config, 'nplc', 10.0))
        _curr_rev = bool(getattr(self.config, 'current_reverse', False))
        if _curr_rev:
            _meas_time_s = 2.0 * _rev_settle * _avg_n + (_nplc / 50.0) * 2.0 * _avg_n
        else:
            _meas_time_s = (_nplc / 50.0) * _avg_n
        _expected_drift_K = float(self.config.T_ramp_rate) / 60.0 * _meas_time_s
        _dT_log = abs(float(self.config.T_delta))
        _drift_frac = _expected_drift_K / max(_dT_log, 1e-9)
        logger.info(
            f"RAMP precision config: rate={float(self.config.T_ramp_rate):.3f} K/min, "
            f"dT={_dT_log:.4f} K, avg_n={_avg_n}, current_reverse={'ON' if _curr_rev else 'OFF'}, "
            f"NPLC={_nplc:.1f} -> expected meas time ~{_meas_time_s:.2f} s, "
            f"T-drift per point ~{_expected_drift_K:.4f} K ({_drift_frac*100:.1f}% of dT). "
            f"T_now logged = midpoint of measurement window (T-drift fix active). "
            f"REL auto-zero + interleaved current reversal apply through shared _measure()."
        )
        if _drift_frac > 0.25:
            logger.warning(
                f"RAMP: expected T-drift ({_expected_drift_K:.4f} K) exceeds 25% of dT "
                f"({_dT_log:.4f} K). For best results lower T_ramp_rate to "
                f"~{0.25 * _dT_log * 60.0 / max(_meas_time_s, 0.1):.3f} K/min "
                f"or reduce avg_n."
            )

        # Gate voltage points (single [None] when gate disabled)
        gate_on = bool(getattr(self.config, 'gate_enable', False))
        if gate_on:
            Vg_points = list(np.arange(
                self.config.gate_start,
                self.config.gate_end + self.config.gate_step / 2 * np.sign(self.config.gate_step),
                self.config.gate_step))
            if not Vg_points or abs(Vg_points[-1]-self.config.gate_end) > abs(self.config.gate_step)/2:
                Vg_points.append(round(self.config.gate_end, 9))
        else:
            Vg_points = [None]

        self._total_pts = len(B_points) * n_T_pts * len(Vg_points)
        self._sweep_t0  = t0

        self._publish(LiveData(phase=f"RAMP: initial conditions — B → 0 T, T → {self.config.T_start:.3f} K", sweep_mode="RAMP"))
        self._wait_B(0.0, t0)
        self._wait_T(self.config.T_start, t0)

        for Vg in Vg_points:
            self._check_stop()
            I_leak = 0.0
            if gate_on and Vg is not None:
                I_leak = self._apply_gate(Vg)
                self._V_gate_now = Vg
            else:
                self._V_gate_now = None

            self._publish(LiveData(
                phase=f"RAMP: initial conditions met. Setting B_start = {self.config.B_start:+.5f} T"
                      + (f"  Vg={Vg:+.3f}V" if gate_on else ""),
                V_gate=self._V_gate_now, I_leak=I_leak if gate_on else None))

            for B_set in B_points:
                self._check_stop()
                self._publish(LiveData(
                    phase=f"RAMP: set B={B_set:+.5f}T"
                          + (f"  Vg={Vg:+.3f}V" if gate_on else ""),
                    V_gate=self._V_gate_now))
                B_now, _ = self._wait_B(B_set, t0)
                self._publish(LiveData(
                    phase=f"RAMP: stabilise T_start={self.config.T_start:.3f}K at B={B_now:+.5f}T",
                    V_gate=self._V_gate_now))
                T_now = self._wait_T(self.config.T_start, t0)
                self._publish(LiveData(
                    phase=f"RAMP: conditions met — T={T_now:.3f}K, B={B_now:+.5f}T. Logging starts.",
                    V_gate=self._V_gate_now))
                self.armed = True
                # ── First point (at T_start, before ramp begins) ──────────
                # T is stable here (just stabilised by _wait_T), so the
                # before/after average reduces to T_now. No T-drift correction
                # is needed for this point; we use T_now directly.
                meas = self._measure()
                self._add_point(t0, self.config.T_start, T_now, B_set, B_now, meas)
                _n_points_logged = 1
                logger.info(
                    f"RAMP point #{_n_points_logged}: LOGGED at T={T_now:.4f} K "
                    f"(target T_start={self.config.T_start:.4f} K), "
                    f"Vxx={meas.get('Vxx_V', meas.get('Vxx', 0))*1e6:.4f} uV, "
                    f"Vxy={meas.get('Vxy_V', meas.get('Vxy', 0))*1e6:.4f} uV, "
                    f"Rxx={meas.get('Rxx', 0):.6f} Ohm, Rxy={meas.get('Rxy', 0):.6f} Ohm. "
                    f"Next target = "
                    f"{self.config.T_start + (abs(float(self.config.T_delta)) if self.config.T_end >= self.config.T_start else -abs(float(self.config.T_delta))):.4f} K."
                )
                self._publish(LiveData(
                    phase=f"RAMP: T ramp {self.config.T_start:.3f}->{self.config.T_end:.3f}K",
                    V_gate=self._V_gate_now))
                # ── Issue iTC ramp commands, wrapped in try/except ────────
                # A failure here MUST be loud — the ramp will never start
                # without these commands. We log the error and abort cleanly.
                try:
                    if self.itc:
                        _probe_rate = float(self.config.T_ramp_rate)
                        self.itc.set_ramp_rate(_probe_rate, self.config.temp_device)
                        self.itc.set_ramp_mode(True, self.config.temp_device)
                        self.itc.set_control_mode("AUTO", self.config.temp_device)
                        self.itc.set_temperature_setpoint(self.config.T_end, self.config.temp_device)
                        # ── VTI: SAME rate as probe (lock-step) + offset below ──
                        # Spec: VTI rate == probe rate, ALWAYS. VTI setpoint
                        # = T_end - vti_offset (capped at vti_T_max_K, floored
                        # at 1.5 K). _set_vti uses ramp_mode=ON in both dirs,
                        # so no heater spike is possible.
                        _vti_offset = float(getattr(self.config, 'vti_offset', 1.0))
                        _vti_target = min(self._ramp_safety_vti_T_cap,
                                          max(1.5, float(self.config.T_end) - _vti_offset))
                        self._set_vti(_vti_target, enable_ramp=True,
                                      ramp_rate=_probe_rate)
                        logger.info(
                            f"RAMP: iTC commanded successfully — "
                            f"probe rate={_probe_rate:.4f} K/min, "
                            f"ramp_mode=ON, setpoint={self.config.T_end:.4f} K. "
                            f"VTI: target={_vti_target:.4f} K (= T_end - {_vti_offset:.2f}K, "
                            f"capped at {self._ramp_safety_vti_T_cap:.1f}K), "
                            f"rate={_probe_rate:.3f} K/min (LOCK-STEP with probe). "
                            f"Now polling T every {self.config.settle_s:.2f} s for threshold crossings."
                        )
                except Exception as _itc_e:
                    logger.error(
                        f"RAMP: iTC command failed — {_itc_e}. The ramp may not start. "
                        f"Aborting this B-slice."
                    )
                    self._publish(LiveData(
                        phase=f"RAMP iTC error: {_itc_e}", sweep_mode="RAMP"))
                    continue  # skip this B point, try next
                dT = abs(float(self.config.T_delta))
                ramp_up = self.config.T_end >= self.config.T_start
                T_prev, last_thr, ramp_done = T_now, T_now, False
                self._active_T_target = self.config.T_end
                self._active_T_ramp   = True
                last_publish_ramp = 0.0
                RAMP_PUBLISH_INTERVAL = 0.25
                # ── T-drift tracking for quality awareness ────────────────
                self._ramp_max_T_drift = 0.0
                self._ramp_drift_warned_runtime = False
                # ── Diagnostic / watchdog state ───────────────────────────
                _ramp_start_time = time.time()
                _ramp_last_diag_log = _ramp_start_time
                _ramp_T_at_start    = T_now
                _ramp_stuck_warned  = False
                _ramp_consec_read_fail = 0   # count consecutive iTC read failures
                _ramp_consec_read_fail_max = 30  # at settle_s=0.5s, ~15s of failures before giving up
                while not ramp_done:
                    self._check_stop()
                    # ── iTC read wrapped in try/except ────────────────────
                    # A single transient serial hiccup must NOT kill the sweep.
                    # We log the error, count consecutive failures, and only
                    # abort the sweep if iTC stays unreachable for ~15 s.
                    try:
                        T_now = self.itc.read_temperature(self.config.temp_device) if self.itc else 0.0
                        _ramp_consec_read_fail = 0  # reset on success
                    except Exception as _read_e:
                        _ramp_consec_read_fail += 1
                        if _ramp_consec_read_fail <= 3 or _ramp_consec_read_fail % 10 == 0:
                            logger.warning(
                                f"RAMP: iTC read failed ({_ramp_consec_read_fail}x): {_read_e}. "
                                f"Retrying — will abort if it stays bad for "
                                f"~{_ramp_consec_read_fail_max * self.config.settle_s:.1f}s."
                            )
                        if _ramp_consec_read_fail >= _ramp_consec_read_fail_max:
                            logger.error(
                                f"RAMP: iTC unreachable for {_ramp_consec_read_fail} "
                                f"consecutive reads — aborting this B-slice and moving on."
                            )
                            break  # exit while loop, let outer loop continue
                        # ── Heartbeat publish so live T isn't frozen ──
                        _now_hb = time.time()
                        if _now_hb - last_publish_ramp >= RAMP_PUBLISH_INTERVAL:
                            self._publish(LiveData(
                                phase=f"RAMP: waiting for iTC (read failed {_ramp_consec_read_fail}x)",
                                T_K=self._last_T_now, t_s=_now_hb-t0, B_T=B_now,
                                V_gate=self._V_gate_now,
                                I_leak=I_leak if gate_on else None))
                            last_publish_ramp = _now_hb
                        time.sleep(self.config.settle_s)
                        continue
                    if T_now <= 0:
                        # iTC returned 0.0 (read returned but garbled or sensor
                        # not reporting yet). Don't silently freeze the UI —
                        # publish a heartbeat using the last known good T.
                        _now_hb = time.time()
                        if _now_hb - last_publish_ramp >= RAMP_PUBLISH_INTERVAL:
                            self._publish(LiveData(
                                phase=f"RAMP: waiting for valid iTC reading",
                                T_K=self._last_T_now, t_s=_now_hb-t0, B_T=B_now,
                                V_gate=self._V_gate_now,
                                I_leak=I_leak if gate_on else None))
                            last_publish_ramp = _now_hb
                        time.sleep(self.config.settle_s)
                        continue
                    # ── SAFETY: overshoot abort ──────────────────────────
                    # If T has gone significantly beyond T_end (PID overshoot,
                    # iTC misconfiguration, or any other surprise), STOP THE
                    # RAMP IMMEDIATELY. We try to command the iTC to hold at
                    # the current T (which prevents further heating) and
                    # abort the sweep with a loud error.
                    _T_safe_max = float(self.config.T_end) + self._ramp_safety_overshoot_K
                    if T_now > _T_safe_max:
                        crit_msg = (
                            f"RAMP SAFETY ABORT: T_now={T_now:.3f}K exceeded "
                            f"T_end+{self._ramp_safety_overshoot_K:.2f}K = {_T_safe_max:.3f}K. "
                            f"Halting iTC ramp and aborting sweep."
                        )
                        logger.error(crit_msg)
                        self._publish(LiveData(phase=crit_msg, sweep_mode="RAMP"))
                        # Try to halt the iTC ramp safely
                        try:
                            self.itc.set_ramp_mode(False, self.config.temp_device)
                            self.itc.set_temperature_setpoint(T_now, self.config.temp_device)
                            _vti_dev = getattr(self.config, 'vti_device', 'MB1.T1')
                            self.itc.set_ramp_mode(False, _vti_dev)
                            # Read current VTI T if possible so we hold there
                            try:
                                _vti_now = self.itc.read_temperature(_vti_dev)
                            except Exception:
                                _vti_now = 1.5  # safe low value if read fails
                            self.itc.set_temperature_setpoint(_vti_now, _vti_dev)
                        except Exception as _safety_e:
                            logger.error(f"RAMP safety: failed to halt iTC: {_safety_e}")
                        return  # exit the entire mode
                    ft = self.temp_filter.filter(T_now)
                    self._last_T_now = ft
                    now_t = time.time()
                    if now_t - last_publish_ramp >= RAMP_PUBLISH_INTERVAL:
                        self._publish(LiveData(
                            T_K=ft, t_s=now_t-t0, B_T=B_now,
                            V_gate=self._V_gate_now,
                            I_leak=I_leak if gate_on else None))
                        last_publish_ramp = now_t
                    T_target = last_thr + (dT if ramp_up else -dT)
                    T_target = min(T_target, self.config.T_end) if ramp_up                                else max(T_target, self.config.T_end)
                    # ── Heartbeat log every 10 s — shows T is rising & next target ──
                    # Without this the system log is silent for 30+ s between
                    # threshold crossings, making the run feel frozen.
                    if now_t - _ramp_last_diag_log >= 10.0:
                        logger.info(
                            f"RAMP heartbeat: T_now={T_now:.4f} K, next_target={T_target:.4f} K, "
                            f"distance={abs(T_target-T_now):.4f} K, ramp_up={ramp_up}, "
                            f"points_logged={_n_points_logged}"
                        )
                        _ramp_last_diag_log = now_t
                    # ── Stuck-ramp watchdog: if T hasn't moved by 50 mK after 60 s,
                    # the iTC may not be ramping (control mode wrong, heater off,
                    # setpoint not honored, etc). Log a warning once.
                    if (not _ramp_stuck_warned
                        and now_t - _ramp_start_time > 60.0
                        and abs(T_now - _ramp_T_at_start) < 0.05):
                        logger.warning(
                            f"RAMP watchdog: T has not moved meaningfully in 60 s "
                            f"(T_start={_ramp_T_at_start:.4f} K, T_now={T_now:.4f} K). "
                            f"The iTC may not be ramping. Check: (1) heater enabled, "
                            f"(2) AUTO control on the correct loop, (3) ramp rate non-zero, "
                            f"(4) setpoint = T_end correctly applied. Sweep will keep "
                            f"polling but if T stays flat no further points will log."
                        )
                        _ramp_stuck_warned = True
                    if self._crossed_threshold(T_prev, T_now, T_target):
                        # ── T-drift correction ────────────────────────────
                        # Read T BEFORE and AFTER the measurement, use the
                        # average as the recorded T. This makes the logged
                        # T_now the EFFECTIVE temperature (midpoint of the
                        # measurement window) rather than the start.
                        # During the ~few-second measurement, T continues to
                        # rise; the midpoint is the physically correct value
                        # for the average ±I voltage measured at this point.
                        T_before = T_now
                        meas = self._measure()
                        try:
                            T_after = self.itc.read_temperature(self.config.temp_device)
                        except Exception as _e:
                            # If iTC read fails (briefly unresponsive), fall back
                            # to T_before — we don't want one bad read to fail
                            # the entire point.
                            T_after = T_before
                        # Both T_before and T_after must be positive to trust
                        # the average; otherwise fall back to T_before
                        if T_after and T_after > 0:
                            T_logged = (T_before + T_after) / 2.0
                            T_drift  = abs(T_after - T_before)
                        else:
                            T_logged = T_before
                            T_drift  = 0.0
                        self._add_point(t0, T_target, T_logged, B_set, B_now, meas)
                        _n_points_logged += 1
                        # Per-point log so user sees progress in the system log
                        _next_target = last_thr + (dT if ramp_up else -dT) + (dT if ramp_up else -dT)
                        _next_target_clamped = (min(_next_target, self.config.T_end) if ramp_up
                                                else max(_next_target, self.config.T_end))
                        logger.info(
                            f"RAMP point #{_n_points_logged}: logged at T={T_logged:.4f} K "
                            f"(target={T_target:.4f} K, drift={T_drift*1000:.1f} mK during measurement). "
                            f"Next target = {_next_target_clamped:.4f} K."
                        )
                        # Track max drift, warn ONCE if it gets bad
                        if T_drift > self._ramp_max_T_drift:
                            self._ramp_max_T_drift = T_drift
                        if (T_drift > 0.5 * dT
                            and not self._ramp_drift_warned_runtime
                            and dT > 0):
                            logger.warning(
                                f"RAMP runtime: T-drift {T_drift:.4f} K during "
                                f"measurement at T~{T_logged:.3f} K exceeds 50% "
                                f"of dT={dT:.4f} K. Data quality degraded for "
                                f"this and subsequent points until ramp rate "
                                f"is lowered. (This warning fires once per scan.)"
                            )
                            self._ramp_drift_warned_runtime = True
                        last_thr = T_target
                    ramp_done = (T_now >= self.config.T_end - self.config.tol_T) if ramp_up                                 else (T_now <= self.config.T_end + self.config.tol_T)
                    T_prev = T_now
                    time.sleep(self.config.settle_s)

                # End of B-loop iteration: log summary so user sees how many
                # points were logged (always, regardless of drift level).
                logger.info(
                    f"RAMP B={B_set:+.5f}T finished: {_n_points_logged} point(s) "
                    f"logged, max T-drift during any single measurement = "
                    f"{self._ramp_max_T_drift:.4f} K."
                )

        # ════════════════════════════════════════════════════════════════════
        # END-OF-RAMP CLEANUP: stop the iTC's ramp mode and hold at current T
        # so we don't leave the controller commanding a continued ramp.
        # Without this, the iTC would continue trying to reach T_end forever
        # if the sweep ended early or got into a weird state.
        # ════════════════════════════════════════════════════════════════════
        try:
            if self.itc:
                _T_now_final = self.itc.read_temperature(self.config.temp_device)
                self.itc.set_ramp_mode(False, self.config.temp_device)
                self.itc.set_temperature_setpoint(_T_now_final, self.config.temp_device)
                # VTI too
                _vti_dev = getattr(self.config, 'vti_device', 'MB1.T1')
                try:
                    _vti_T_final = self.itc.read_temperature(_vti_dev)
                except Exception:
                    _vti_T_final = max(1.5, _T_now_final - float(getattr(self.config, 'vti_offset', 1.0)))
                self.itc.set_ramp_mode(False, _vti_dev)
                self.itc.set_temperature_setpoint(_vti_T_final, _vti_dev)
                logger.info(
                    f"RAMP cleanup: iTC ramp stopped. Probe held at "
                    f"{_T_now_final:.3f}K, VTI held at {_vti_T_final:.3f}K."
                )
        except Exception as _cleanup_e:
            logger.warning(f"RAMP cleanup failed (manual iTC reset may be needed): {_cleanup_e}")

        self._publish(LiveData(phase="RAMP completed"))


    # ═══════════════════════ RELAX MODE ══════════════════════════════════════
    def _run_relax_mode(self, t0):
        """Creep / Relaxation: monitor R(t) at fixed T and B after a field step."""
        cfg = self.config
        B_target = float(cfg.relax_B_step)
        dur      = float(cfg.relax_duration_s)
        dt       = max(0.5, float(cfg.relax_interval_s))

        # ── DEFENCE 2a: log received targets at INFO before doing anything ──
        # If recording later starts at the wrong B, this line in the backend
        # log file is the audit trail showing what the backend received.
        logger.info(
            "RELAX received: T_target=%.3f K, B_target=%.4f T, "
            "duration=%.0f s, dt=%.2f s, sample=%s",
            float(cfg.T_start), B_target, dur, dt, cfg.sample_name
        )

        self._publish(LiveData(phase="RELAX: waiting for T={:.3f}K".format(cfg.T_start)))
        T_now = self._wait_T(cfg.T_start, t0)

        # ── DEFENCE 3a (T-settle): abort if temperature didn't reach target ──
        tol_T = float(getattr(cfg, 'tol_T', 0.02))           # default 20 mK
        T_settle_window = max(5.0 * tol_T, 0.10)             # 100 mK floor
        if abs(T_now - float(cfg.T_start)) > T_settle_window:
            err = (
                "RELAX ABORT: temperature did not settle at target. "
                "Requested T = {:.3f} K, actual = {:.3f} K (|ΔT| = {:.3f} K > "
                "{:.3f} K tolerance). No file written. Check ITC setpoint "
                "and stability before retrying."
            ).format(float(cfg.T_start), T_now, abs(T_now - float(cfg.T_start)), T_settle_window)
            logger.error(err)
            self._publish(LiveData(phase=err))
            return

        self._publish(LiveData(phase="RELAX: ramping B → {:+.4f}T".format(B_target)))
        B_now, _b_valid = self._wait_B(B_target, t0)

        # ── DEFENCE 3b (B-settle): abort if magnet did not settle at target ──
        # _wait_B can return early on a stop-request or a settle-timeout. If
        # the actual field is far from target, opening a file and recording
        # at the wrong B silently corrupts the entire run. Abort instead.
        # Note: this check runs BEFORE armed=True so an abort leaves the
        # system in a clean disarmed state.
        tol_B = float(getattr(cfg, 'tol_B', 0.0005))   # default 0.5 mT
        settle_window = max(5.0 * tol_B, 0.01)         # max 10 mT or 5×tol
        if abs(B_now - B_target) > settle_window:
            err = (
                "RELAX ABORT: magnet did not settle at target. "
                "Requested B_target = {:+.4f} T, actual settled B = {:+.4f} T "
                "(|ΔB| = {:.4f} T > {:.4f} T tolerance). No file written. "
                "Check IPS persistent-mode lock, ramp parameters, and config "
                "payload sent to /api/start."
            ).format(B_target, B_now, abs(B_now - B_target), settle_window)
            logger.error(err)
            self._publish(LiveData(phase=err))
            return

        # Magnet has settled — arm the system for recording.
        self.armed = True

        # ── DEFENCE 2b: log the settled field, confirming we're at the target
        logger.info(
            "RELAX confirmed: settled at B=%.4f T (target %.4f T, |ΔB|=%.4f T)",
            B_now, B_target, abs(B_now - B_target)
        )

        import os as _os
        # Filename uses B_target (the requested value, for predictable naming).
        # The header inside the file uses B_now (the actual measured value).
        fname = "{}_RELAX_{:.3f}K_{:+.4f}T.txt".format(cfg.sample_name, cfg.T_start, B_target)
        save_folder = cfg.save_folder.strip() if cfg.save_folder else '.'
        try:
            _os.makedirs(save_folder, exist_ok=True)
        except Exception as e:
            logger.warning(f"RELAX: could not create save_folder '{save_folder}': {e}")
            save_folder = '.'
        fpath = _os.path.join(save_folder, fname)
        # Anti-overwrite
        original_fpath = fpath
        fpath = _unique_path(fpath)
        if fpath != original_fpath:
            logger.info(f"RELAX: file exists, auto-renamed to {_os.path.basename(fpath)}")
            self._publish(LiveData(phase=
                f"File exists — saving as {_os.path.basename(fpath)} (auto-renamed)"))
        self._total_pts = int(dur / dt)
        self._sweep_t0  = t0
        self._publish(LiveData(phase="RELAX: monitoring R(t) for {:.0f}s  |  {}".format(dur, fname)))

        with open(fpath, 'w', encoding='utf-8') as f:
            # ── DEFENCE 4: header reports the ACTUAL settled field, not the
            # requested target. If the two differ in a future bug recurrence,
            # the file header itself becomes self-documenting evidence.
            f.write("# RELAX mode  T={:.3f}K  B_target={:+.4f}T  B_actual={:+.4f}T\n".format(
                cfg.T_start, B_target, B_now))
            f.write("# Sample: {}\n".format(cfg.sample_name))
            f.write("# t(s)\tVxx(V)\tVxy(V)\tRxx(Ohm)\tRxy(Ohm)\tT_K\tB_T\n")
            t_start = time.time()
            n = 0
            while True:
                self._check_stop()
                elapsed = time.time() - t_start
                if elapsed > dur:
                    break
                meas  = self._measure()
                T_now = self.itc.read_temperature(cfg.temp_device) if self.itc else cfg.T_start
                if self.ips:
                    B_now2, _b_valid = self.ips.read_field(cfg.field_group)
                else:
                    B_now2 = B_target
                _ac = getattr(cfg, 'source_mode', 'DC') in ('MFLI', 'MFLI_DUAL', 'MFLI_SINGLE')
                Vxx = meas["Vxxp_m"] if _ac else (meas["Vxxp_m"] - meas["Vxxm_m"]) / 2
                Vxy = meas["Vxyp_m"] if _ac else (meas["Vxyp_m"] - meas["Vxym_m"]) / 2
                Rxx = meas["Rxx"];  Rxy = meas["Rxy"]
                n  += 1
                frac = min(1.0, elapsed / dur)
                self._publish(LiveData(
                    T_K=T_now, B_T=B_now2, t_s=elapsed,
                    Vxx_V=Vxx, Vxy_V=Vxy, Rxx_Ohm=Rxx, Rxy_Ohm=Rxy,
                    main_x=elapsed, main_Vxx=Vxx, main_Vxy=Vxy,
                    main_Rxx=Rxx,   main_Rxy=Rxy,
                    sweep_mode="RELAX",
                    progress_frac=frac, n_pts=n,
                    total_pts=self._total_pts, eta_s=max(0, dur - elapsed),
                ))
                f.write("{:.3f}\t{:.9f}\t{:.9f}\t{:.6f}\t{:.6f}\t{:.4f}\t{:.6f}\n".format(
                    elapsed, Vxx, Vxy, Rxx, Rxy, T_now, B_now2))
                f.flush()
                time.sleep(max(0.1, dt - 0.5))
        self._publish(LiveData(phase="RELAX completed  ({} points, {:.0f}s)".format(n, elapsed)))

    # ═══════════════════════ RELAX_SCAN MODE ═════════════════════════════════
    def _run_relax_scan_mode(self, t0):
        """Relaxation spectroscopy: RELAX measurement at each B in a list.

        For each B value in relaxscan_B_list:
          1. Ramp B to target (with armed=False — no logging during ramp)
          2. Verify B has settled
          3. Record R_xx(t), R_xy(t) for relaxscan_duration_s
          4. Save one file per B value
          5. Move to next B value
        """
        cfg = self.config
        import os as _os

        # ── Parse B list ──────────────────────────────────────────────────
        B_list_str = cfg.relaxscan_B_list.strip()
        if not B_list_str:
            raise ValueError("RELAX_SCAN: no B values specified (relaxscan_B_list is empty)")

        B_values = []
        for token in B_list_str.replace(';', ',').split(','):
            token = token.strip()
            if not token:
                continue
            try:
                B_values.append(float(token))
            except ValueError:
                logger.warning(f"RELAX_SCAN: skipping invalid B value '{token}'")

        if not B_values:
            raise ValueError("RELAX_SCAN: no valid B values parsed from '{}'".format(B_list_str))

        dur = float(cfg.relaxscan_duration_s)
        dt  = max(0.5, float(cfg.relaxscan_interval_s))
        T_fixed = float(cfg.T_start)
        n_B = len(B_values)

        self._publish(LiveData(
            phase=f"RELAX_SCAN: {n_B} B values, {dur:.0f}s each, T={T_fixed:.3f}K",
            sweep_mode="RELAX_SCAN"))
        logger.info(f"RELAX_SCAN: B_list = {B_values}, dur={dur}s, dt={dt}s, T={T_fixed}K")

        # ── Validate and prepare save folder ──────────────────────────────
        save_folder = cfg.save_folder.strip() if cfg.save_folder else '.'
        try:
            _os.makedirs(save_folder, exist_ok=True)
            # Test write permission with a temporary marker file
            _test_marker = _os.path.join(save_folder, '.qtms_write_test')
            with open(_test_marker, 'w', encoding='utf-8') as _tf:
                _tf.write('test')
            _os.remove(_test_marker)
        except Exception as e:
            logger.warning(f"RELAX_SCAN: cannot use save_folder '{save_folder}' ({e}); falling back to '.'")
            save_folder = '.'

        # ── Wait for temperature ──────────────────────────────────────────
        self._publish(LiveData(phase=f"RELAX_SCAN: stabilising T = {T_fixed:.3f} K"))
        T_now = self._wait_T(T_fixed, t0)

        # ── Total points for progress tracking ────────────────────────────
        pts_per_B = int(dur / dt)
        self._total_pts = pts_per_B * n_B

        # ── Loop over B values ────────────────────────────────────────────
        for i_B, B_target in enumerate(B_values):
            self._check_stop()

            # ── Ramp to target B (no logging) ─────────────────────────────
            self.armed = False
            self._publish(LiveData(
                phase=f"RELAX_SCAN [{i_B+1}/{n_B}]: ramping B → {B_target:+.4f} T (no logging)"))
            logger.info(f"RELAX_SCAN [{i_B+1}/{n_B}]: requested B_target={B_target:+.4f} T")
            B_now, settled = self._wait_B(B_target, t0)

            # ── DEFENCE 3 (RELAX_SCAN variant): verify settle, retry once,
            # then SKIP this B point if still not settled. Don't open the file.
            settle_window = max(cfg.tol_B * 5.0, 0.01)
            if abs(B_now - B_target) > settle_window:
                logger.warning(
                    f"RELAX_SCAN: B did not settle at {B_target:+.4f}T "
                    f"(actual={B_now:+.4f}T). Re-waiting once...")
                B_now, _ = self._wait_B(B_target, t0)
                if abs(B_now - B_target) > settle_window:
                    err = (
                        f"RELAX_SCAN [{i_B+1}/{n_B}]: SKIP — magnet did not settle. "
                        f"Requested B={B_target:+.4f} T, actual={B_now:+.4f} T "
                        f"(|ΔB|={abs(B_now - B_target):.4f} T > {settle_window:.4f} T tol). "
                        f"No file written for this point."
                    )
                    logger.error(err)
                    self._publish(LiveData(phase=err))
                    continue   # move to next B in list

            logger.info(f"RELAX_SCAN [{i_B+1}/{n_B}]: settled at B={B_now:+.4f} T (target {B_target:+.4f})")
            self.armed = True

            # ── Open file for this B value ────────────────────────────────
            fname = "{}_RELAX_{:.3f}K_{:+.4f}T.txt".format(
                cfg.sample_name, T_fixed, B_target)
            fpath = _os.path.join(save_folder, fname)
            # Anti-overwrite
            original_fpath = fpath
            fpath = _unique_path(fpath)
            if fpath != original_fpath:
                fname = _os.path.basename(fpath)
                logger.info(f"RELAX_SCAN: file exists, auto-renamed to {fname}")

            self._publish(LiveData(
                phase=f"RELAX_SCAN [{i_B+1}/{n_B}]: recording at B={B_target:+.4f}T "
                      f"for {dur:.0f}s → {fname}"))

            # ── Record R(t) ───────────────────────────────────────────────
            with open(fpath, 'w', encoding='utf-8') as f:
                # ── DEFENCE 4 (RELAX_SCAN variant): header reports actual B ──
                f.write(f"# Mode=RELAX_SCAN  |  {getattr(cfg,'source_mode','DC')}"
                        f" | I={cfg.I_const:.6g} A"
                        f"  |  Temperature={T_fixed:.3f} K"
                        f"  |  B_target={B_target:+.4f}T  |  B_actual={B_now:+.4f}T\n")
                f.write(f"# Sample: {cfg.sample_name}\n")
                f.write(f"# Point {i_B+1} of {n_B}  |  Duration: {dur:.0f} s\n")
                f.write("# t(s)\tVxx(V)\tVxy(V)\tRxx(Ohm)\tRxy(Ohm)\tT_K\tB_T\n")
                t_start = time.time()
                n = 0

                while True:
                    self._check_stop()
                    elapsed = time.time() - t_start
                    if elapsed > dur:
                        break

                    meas = self._measure()
                    T_now = self.itc.read_temperature(cfg.temp_device) if self.itc else T_fixed
                    if self.ips:
                        B_now2, _b_valid = self.ips.read_field(cfg.field_group)
                    else:
                        B_now2 = B_target
                    if hasattr(self, '_last_B_now'):
                        self._last_B_now = B_now2

                    _ac = getattr(cfg, 'source_mode', 'DC') in ('MFLI', 'MFLI_DUAL', 'MFLI_SINGLE')
                    Vxx = meas["Vxxp_m"] if _ac else (meas["Vxxp_m"] - meas["Vxxm_m"]) / 2
                    Vxy = meas["Vxyp_m"] if _ac else (meas["Vxyp_m"] - meas["Vxym_m"]) / 2
                    Rxx = meas["Rxx"]
                    Rxy = meas["Rxy"]
                    n += 1

                    # Progress across entire RELAX_SCAN
                    total_elapsed_pts = i_B * pts_per_B + n
                    frac = min(1.0, total_elapsed_pts / self._total_pts)
                    remaining_this = max(0, dur - elapsed)
                    remaining_future = (n_B - i_B - 1) * dur
                    eta = remaining_this + remaining_future

                    self._publish(LiveData(
                        T_K=T_now, B_T=B_now2, t_s=elapsed,
                        Vxx_V=Vxx, Vxy_V=Vxy, Rxx_Ohm=Rxx, Rxy_Ohm=Rxy,
                        main_x=elapsed, main_Vxx=Vxx, main_Vxy=Vxy,
                        main_Rxx=Rxx, main_Rxy=Rxy,
                        sweep_mode="RELAX_SCAN",
                        progress_frac=frac, n_pts=total_elapsed_pts,
                        total_pts=self._total_pts, eta_s=eta,
                    ))
                    f.write("{:.3f}\t{:.9f}\t{:.9f}\t{:.6f}\t{:.6f}\t{:.4f}\t{:.6f}\n".format(
                        elapsed, Vxx, Vxy, Rxx, Rxy, T_now, B_now2))
                    f.flush()
                    time.sleep(max(0.1, dt - 0.5))

            self._publish(LiveData(
                progress=f"RELAX_SCAN [{i_B+1}/{n_B}]: saved {fname} ({n} pts, {elapsed:.0f}s)"))
            logger.info(f"RELAX_SCAN: completed B={B_target:+.4f}T → {fname}")

        # ── Return B to 0 after all points ────────────────────────────────
        self.armed = False
        self._publish(LiveData(phase="RELAX_SCAN: returning B → 0"))
        self._wait_B(0.0, t0)
        self._publish(LiveData(
            phase=f"RELAX_SCAN completed: {n_B} B values, {n_B * dur / 3600:.1f} hours total"))

    # ═══════════════════════ TCSCAN MODE ═════════════════════════════════════
    def _run_tcscan_mode(self, t0):
        """Tc scan: fine T ramp at fixed B for transition finding."""
        cfg = self.config
        B_fixed  = float(cfg.tcscan_B_fixed)
        T_start2 = float(cfg.tcscan_T_start)
        T_end2   = float(cfg.tcscan_T_end)
        dT       = abs(float(cfg.tcscan_dT))
        wait_s   = max(5.0, float(cfg.tcscan_wait_s))
        sign     = 1.0 if T_end2 >= T_start2 else -1.0

        T_points = []
        T = T_start2
        while (sign > 0 and T <= T_end2 + dT * 0.01) or (sign < 0 and T >= T_end2 - dT * 0.01):
            T_points.append(round(T, 6))
            T += sign * dT
        self._total_pts = len(T_points)
        self._sweep_t0  = t0

        import os as _os
        fname  = "{}_TCSCAN_{:+.4f}T.txt".format(cfg.sample_name, B_fixed)
        save_folder = cfg.save_folder.strip() if cfg.save_folder else '.'
        try:
            _os.makedirs(save_folder, exist_ok=True)
        except Exception as e:
            logger.warning(f"TCSCAN: could not create save_folder '{save_folder}': {e}")
            save_folder = '.'
        fpath  = _os.path.join(save_folder, fname)
        # Anti-overwrite
        original_fpath = fpath
        fpath = _unique_path(fpath)
        if fpath != original_fpath:
            fname = _os.path.basename(fpath)
            logger.info(f"TCSCAN: file exists, auto-renamed to {fname}")
        self._publish(LiveData(phase="TCSCAN: ramping B → {:+.4f}T".format(B_fixed)))
        B_now, _ = self._wait_B(B_fixed, t0)
        self._publish(LiveData(phase="TCSCAN: {:.3f}→{:.3f}K in {:.3f}K steps  |  {}".format(
            T_start2, T_end2, dT, fname)))
        self.armed = True

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write("# TCSCAN  B={:+.4f}T  T: {:.3f}->{:.3f}K  dT={:.3f}K\n".format(
                B_fixed, T_start2, T_end2, dT))
            f.write("# Sample: {}\n".format(cfg.sample_name))
            f.write("# T_set(K)\tT_now(K)\tVxx(V)\tVxy(V)\tRxx(Ohm)\tRxy(Ohm)\tB(T)\tt(s)\n")
            for i, T_set in enumerate(T_points):
                self._check_stop()
                self._publish(LiveData(phase="TCSCAN: T → {:.3f}K  ({}/{})".format(
                    T_set, i+1, len(T_points))))
                T_now2 = self._wait_T(T_set, t0, extra_wait=wait_s)
                meas = self._measure()
                _ac  = getattr(cfg, 'source_mode', 'DC') in ('MFLI', 'MFLI_DUAL', 'MFLI_SINGLE')
                Vxx  = meas["Vxxp_m"] if _ac else (meas["Vxxp_m"] - meas["Vxxm_m"]) / 2
                Vxy  = meas["Vxyp_m"] if _ac else (meas["Vxyp_m"] - meas["Vxym_m"]) / 2
                Rxx  = meas["Rxx"];  Rxy = meas["Rxy"]
                ts   = time.time() - t0
                frac = (i + 1) / len(T_points)
                self._publish(LiveData(
                    T_K=T_now2, B_T=B_now, t_s=ts,
                    Vxx_V=Vxx, Vxy_V=Vxy, Rxx_Ohm=Rxx, Rxy_Ohm=Rxy,
                    main_x=T_now2, main_Vxx=Vxx, main_Vxy=Vxy,
                    main_Rxx=Rxx,  main_Rxy=Rxy,
                    sweep_mode="TCSCAN",
                    progress_frac=frac, n_pts=i+1,
                    total_pts=self._total_pts, eta_s=None,
                ))
                f.write("{:.4f}\t{:.4f}\t{:.9f}\t{:.9f}\t{:.6f}\t{:.6f}\t{:.6f}\t{:.2f}\n".format(
                    T_set, T_now2, Vxx, Vxy, Rxx, Rxy, B_now, ts))
                f.flush()
        self._publish(LiveData(phase="TCSCAN completed  ({} steps)".format(len(T_points))))


    # ═══════════════════════ TCSCAN MULTI-B MODE ═════════════════════════════
    def _run_tcscan_multi_b_mode(self, t0):
        """Multi-B variant of TCSCAN: runs the existing _run_tcscan_mode once
        per B value in the comma-separated tcscan_B_list_csv field.

        Implementation is strictly additive — _run_tcscan_mode is unchanged.
        For each B value, we temporarily overwrite cfg.tcscan_B_fixed, call
        the existing method (which produces its own data file with that B
        in the filename), then continue. The original tcscan_B_fixed is
        restored on exit, even if the user clicks STOP mid-scan.

        Each TCSCAN produces its own file named:
            <sample>_TCSCAN_<+/-X.XXXX>T.txt
        so the files for different B values don't collide.

        Failure modes:
          - Empty / unparseable B list → log error, exit without running anything
          - User STOP during a scan → propagates via _check_stop(), finally
            block still restores tcscan_B_fixed
          - One scan crashes → exception propagates up, remaining scans are
            skipped (matches behavior of other multi-iteration modes)
        """
        cfg = self.config
        B_list_csv = str(getattr(cfg, 'tcscan_B_list_csv', '0.0'))

        # Parse the CSV defensively — bad tokens are skipped with a warning,
        # not a hard error, so a typo doesn't kill the whole multi-B scan.
        B_list = []
        for tok in B_list_csv.split(','):
            tok = tok.strip()
            if not tok:
                continue
            try:
                B_list.append(float(tok))
            except ValueError:
                logger.warning(f"TCSCAN_MULTI_B: skipping unparseable B value '{tok}'")
        if not B_list:
            logger.error(f"TCSCAN_MULTI_B: no usable B values in '{B_list_csv}' — "
                         f"set tcscan_B_list_csv in the configure tab. Nothing to do.")
            self._publish(LiveData(
                phase="TCSCAN_MULTI_B: empty/invalid B list — aborting",
                sweep_mode="TCSCAN_MULTI_B"))
            return

        logger.info(f"TCSCAN_MULTI_B: will scan {len(B_list)} B value(s): {B_list}")
        self._publish(LiveData(
            phase=f"TCSCAN_MULTI_B: planning {len(B_list)} scan(s) at B = {B_list}",
            sweep_mode="TCSCAN_MULTI_B"))

        # Save state so we restore it even on STOP / exception
        saved_B_fixed = cfg.tcscan_B_fixed
        try:
            for i, B in enumerate(B_list):
                self._check_stop()
                cfg.tcscan_B_fixed = B
                self._publish(LiveData(
                    phase=f"TCSCAN_MULTI_B: starting scan {i+1}/{len(B_list)}  "
                          f"at B = {B:+.4f} T",
                    sweep_mode="TCSCAN_MULTI_B"))
                # Call the existing (unmodified) TCSCAN method — it does all
                # the heavy lifting, including file creation, T stabilisation,
                # and per-point measurement using whatever current-reversal /
                # REL settings are configured.
                self._run_tcscan_mode(t0)
            self._publish(LiveData(
                phase=f"TCSCAN_MULTI_B completed  ({len(B_list)} scan(s))",
                sweep_mode="TCSCAN_MULTI_B"))
        finally:
            # Always restore the original tcscan_B_fixed, even if STOP or
            # an exception aborted us partway through.
            cfg.tcscan_B_fixed = saved_B_fixed


    # ═══════════════════════ HYSTERESIS MODE ═════════════════════════════════
    def _run_hysteresis_mode(self, t0):
        """Full hysteresis loop in one file: 0 → +B_max → −B_max → 0.

        At each temperature in T_points, the magnet executes a closed loop
        producing ±B paired data. Standard symmetrisation (Vxx_sym, Vxy_anti)
        is applied automatically afterward via _auto_symmetrise_hysteresis.

        Single-T runs use T_start == T_end (set by the UI's "Single fixed T"
        radio). Multi-T runs use T_start, T_end, T_step like STEP mode.
        """
        cfg = self.config

        # ── Build T_points safely (handles single-T case T_start == T_end) ──
        T_start = float(cfg.T_start)
        T_end   = float(cfg.T_end)
        T_step  = float(cfg.T_step)
        if abs(T_end - T_start) < 1e-9:
            T_points = np.array([T_start])
        elif abs(T_step) < 1e-9:
            logger.warning("HYSTERESIS: T_step is 0 but T_start != T_end — running single point at T_start")
            T_points = np.array([T_start])
        else:
            T_points = np.arange(T_start, T_end + T_step / 2, T_step)
            if len(T_points) == 0:
                T_points = np.array([T_start])

        # ── Build the closed-loop B sequence: 0 → +Bmax → −Bmax → 0 ─────────
        # Three consecutive linear branches, each using B_step resolution.
        Bmax  = abs(float(cfg.B_max))
        Bstep = abs(float(cfg.B_step))
        if Bmax < 1e-9 or Bstep < 1e-9:
            logger.error("HYSTERESIS: B_max and B_step must be positive and non-zero.")
            self._publish(LiveData(phase="HYSTERESIS ABORT: B_max or B_step is zero"))
            return
        branch_up    = self._build_B_step_sequence(0.0,    +Bmax, Bstep)   # 0  → +Bmax
        branch_down  = self._build_B_step_sequence(+Bmax, -Bmax, Bstep)    # +Bmax → −Bmax
        branch_back  = self._build_B_step_sequence(-Bmax,  0.0,  Bstep)    # −Bmax → 0
        # Avoid duplicating the junction points (+Bmax appears at end of branch_up
        # and start of branch_down; same for −Bmax).
        B_loop = list(branch_up) + list(branch_down)[1:] + list(branch_back)[1:]

        self._total_pts = len(T_points) * len(B_loop)
        self._sweep_t0  = t0

        # ── Initial conditions ─────────────────────────────────────────────
        self._publish(LiveData(phase="HYSTERESIS: initial field reset → B = 0 T", sweep_mode="HYSTERESIS"))
        self._wait_B(0.0, t0)
        self._publish(LiveData(phase=f"HYSTERESIS: waiting for T_start = {T_start:.3f} K"))
        T_now = self._wait_T(T_start, t0)
        self._publish(LiveData(
            phase=f"HYSTERESIS: initial conditions met — T={T_now:.3f}K, B=0 T."))
        self.armed = True

        for T_set in T_points:
            self._check_stop()
            if abs(T_set - T_start) > 1e-9:
                self._publish(LiveData(phase=f"HYSTERESIS: T → {T_set:.3f}K"))
                T_now = self._wait_T(T_set, t0)

            self._publish(LiveData(
                phase=(f"HYSTERESIS: T={T_set:.3f}K  loop 0 → +{Bmax:.3f} → "
                       f"−{Bmax:.3f} → 0 T  ({len(B_loop)} points)")))

            # ── Verify B is at 0 before starting forward branch ─────────────
            if self._last_B_now is not None and abs(self._last_B_now) > 0.1:
                self._publish(LiveData(
                    phase=f"HYSTERESIS: waiting for B → 0 (currently {self._last_B_now:+.3f} T)"))
                logger.warning(f"HYSTERESIS: B={self._last_B_now:+.4f}T at sweep start — re-waiting for B=0")
                self.armed = False
                self._wait_B(0.0, t0)
                self.armed = True

            # ── Walk the closed loop, logging at every point ───────────────
            for B_set in B_loop:
                self._check_stop()
                B_now, _ = self._wait_B(B_set, t0)
                meas = self._measure()
                self._add_point(t0, T_set, T_now, B_set, B_now, meas)

        # ── Final return to B = 0 ──────────────────────────────────────────
        self.armed = False
        self._publish(LiveData(phase="HYSTERESIS: returning to B = 0 T (no logging)"))
        self._wait_B(0.0, t0)
        self._publish(LiveData(phase="HYSTERESIS completed"))


    # ═══════════════════════ ANGLE_HYST MODE ═════════════════════════════════
    def _run_angle_hyst_mode(self, t0):
        """Vector-magnet hysteresis loop along a (θ, φ) direction.

        Two sub-modes:
          (a) Single θ: one closed loop at the given (theta_deg, phi_deg)
          (b) θ list:   loop repeated at every θ in [theta_start, theta_end]
                        with φ held fixed.

        Each (θ, φ) point produces one file containing the full ±B loop
        along that direction. T can be single or swept independently.
        """
        cfg = self.config

        # ── Build T_points (single or sweep) ────────────────────────────────
        T_start = float(cfg.T_start)
        T_end   = float(cfg.T_end)
        T_step  = float(cfg.T_step)
        if abs(T_end - T_start) < 1e-9 or abs(T_step) < 1e-9:
            T_points = np.array([T_start])
        else:
            T_points = np.arange(T_start, T_end + T_step / 2, T_step)
            if len(T_points) == 0:
                T_points = np.array([T_start])

        # ── Build θ list (single or sweep) ──────────────────────────────────
        phi = float(cfg.angle_phi_deg)
        if bool(getattr(cfg, 'angle_use_theta_list', False)):
            t_s = float(cfg.angle_theta_start)
            t_e = float(cfg.angle_theta_end)
            t_d = float(cfg.angle_theta_step)
            if abs(t_d) < 1e-9:
                theta_points = [t_s]
            else:
                theta_points = list(np.arange(t_s, t_e + t_d / 2, t_d))
                if not theta_points:
                    theta_points = [t_s]
        else:
            theta_points = [float(cfg.angle_theta_deg)]

        # ── Build B-loop sequence: 0 → +Bmax → −Bmax → 0 ────────────────────
        Bmax  = abs(float(cfg.angle_B_max))
        Bstep = abs(float(cfg.angle_B_step))
        if Bmax < 1e-9 or Bstep < 1e-9:
            logger.error("ANGLE_HYST: angle_B_max and angle_B_step must be positive non-zero.")
            self._publish(LiveData(phase="ANGLE_HYST ABORT: B params zero"))
            return
        branch_up   = self._build_B_step_sequence(0.0,  +Bmax, Bstep)
        branch_down = self._build_B_step_sequence(+Bmax, -Bmax, Bstep)
        branch_back = self._build_B_step_sequence(-Bmax,  0.0, Bstep)
        B_loop = list(branch_up) + list(branch_down)[1:] + list(branch_back)[1:]

        # ── Pre-flight: validate every (θ, ±Bmax) point against per-axis limits
        Bx_max = float(cfg.Bx_max); By_max = float(cfg.By_max); Bz_max = float(cfg.Bz_max)
        for th in theta_points:
            mB, axis = max_B_at_angle(th, phi, Bx_max, By_max, Bz_max)
            if Bmax > mB + 1e-9:
                err = (f"ANGLE_HYST ABORT: at θ={th:.3f}° φ={phi:.3f}°, max achievable "
                       f"|B| = {mB:.4f} T (limited by axis {axis}); requested {Bmax:.4f} T.")
                logger.error(err)
                self._publish(LiveData(phase=err))
                return

        # ── Construct VectorMagnet on top of the existing IPS connection ────
        vmag = VectorMagnet(self.ips, Bx_max=Bx_max, By_max=By_max, Bz_max=Bz_max)
        transit_s = float(cfg.angle_transit_s)
        max_rate  = float(cfg.angle_max_rate)

        self._total_pts = len(T_points) * len(theta_points) * len(B_loop)
        self._sweep_t0  = t0

        # ── Initial: zero all axes and wait for T_start ─────────────────────
        self._publish(LiveData(phase="ANGLE_HYST: zeroing all axes", sweep_mode="ANGLE_HYST"))
        vmag.zero_all()
        vmag.wait_at_target(0.0, 0.0, 0.0, tol=cfg.tol_B, timeout_s=120)
        T_now = self._wait_T(T_start, t0)
        self.armed = True

        for T_set in T_points:
            self._check_stop()
            if abs(T_set - T_start) > 1e-9:
                self._publish(LiveData(phase=f"ANGLE_HYST: T → {T_set:.3f}K"))
                T_now = self._wait_T(T_set, t0)

            for th in theta_points:
                self._check_stop()
                # Cache for _open_data_file / file naming
                self._angle_theta_now = float(th)
                self._angle_phi_now   = float(phi)
                self._publish(LiveData(
                    phase=(f"ANGLE_HYST: T={T_set:.3f}K  θ={th:+.3f}°  φ={phi:+.3f}°  "
                           f"loop ±{Bmax:.3f}T  ({len(B_loop)} pts)")))

                # Walk the closed loop, with each scalar B mapped to (Bx,By,Bz)
                for B_set in B_loop:
                    self._check_stop()
                    Bx_t, By_t, Bz_t = spherical_to_cartesian(B_set, th, phi)
                    try:
                        vmag.set_field_xyz(Bx_t, By_t, Bz_t,
                                           total_time_s=transit_s,
                                           max_rate_T_per_min=max_rate)
                    except ValueError as e:
                        logger.error(f"ANGLE_HYST: {e}")
                        continue
                    Bx_now, By_now, Bz_now, settled = vmag.wait_at_target(
                        Bx_t, By_t, Bz_t,
                        tol=cfg.tol_B, timeout_s=cfg.timeout_B,
                        settle_s=cfg.settle_s, n_stable=cfg.nstable_B)
                    if not settled:
                        logger.warning(
                            f"ANGLE_HYST: vector-target not settled at "
                            f"(B={B_set:+.3f}T θ={th:.3f}° φ={phi:.3f}°) — skipping point")
                        continue

                    # Compute the actual scalar B and (θ, φ) from readback
                    B_actual, th_actual, ph_actual = cartesian_to_spherical(
                        Bx_now, By_now, Bz_now)
                    # Store for live display (signed by sign of B_set so the live
                    # plot correctly shows the loop)
                    B_signed = math.copysign(B_actual, B_set) if abs(B_set) > 1e-9 else 0.0

                    meas = self._measure()
                    # Cache the per-axis readback so _add_point can write them
                    # into the ANGLE_HYST data file (calibration analysis needs
                    # the Cartesian components, not just the projected scalar).
                    self._angle_Bx_now = float(Bx_now)
                    self._angle_By_now = float(By_now)
                    self._angle_Bz_now = float(Bz_now)
                    # Publish vector readback in the LiveData stream — both as
                    # a human-readable phase string AND as structured fields
                    # for the 3D Vector tab.
                    self._publish(LiveData(
                        phase=f"ANGLE_HYST  Bx={Bx_now:+.3f} By={By_now:+.3f} Bz={Bz_now:+.3f}  "
                              f"|B|={B_actual:.3f}T  θ={th_actual:.2f}°",
                        Bx_T=float(Bx_now), By_T=float(By_now), Bz_T=float(Bz_now),
                        theta_deg=float(th_actual), phi_deg=float(ph_actual)))
                    self._add_point(t0, T_set, T_now, B_set, B_signed, meas)

        # ── Return all axes to zero ─────────────────────────────────────────
        self.armed = False
        self._publish(LiveData(phase="ANGLE_HYST: zeroing all axes (no logging)"))
        vmag.zero_all()
        vmag.wait_at_target(0.0, 0.0, 0.0, tol=cfg.tol_B, timeout_s=120)
        self._publish(LiveData(phase="ANGLE_HYST completed"))


    # ═══════════════════════ CURRENT_OPT MODE ═════════════════════════════════
    def _run_current_opt_mode(self, t0):
        """Pre-test current optimizer.

        Sweeps current geometrically from copt_I_start_mA up to copt_I_max_mA,
        monitoring probe temperature and resistance at each step. Stops at the
        largest current that satisfies all three checks:
          1. Probe T rise above baseline ≤ copt_dT_tol_K
          2. Rxx deviation from low-current baseline ≤ copt_R_drift_pct
          3. |Vxx| within compliance (V_limit × 0.9)

        Note: probe T is a necessary-but-not-sufficient indicator of sample
        heating. The R-drift check provides the second line of defence by
        watching for sample-internal heating that the probe doesn't see.

        Output: a single text file in the configured save folder, plus an
        on-screen verdict line. No magnetic-field or temperature sweep.
        """
        cfg = self.config

        # ── Settings ────────────────────────────────────────────────────────
        I_start  = float(cfg.copt_I_start_mA) * 1e-3   # convert mA → A
        I_max    = float(cfg.copt_I_max_mA)   * 1e-3
        I_mult   = float(cfg.copt_I_mult)
        dwell_s  = float(cfg.copt_dwell_s)
        n_samp   = int(cfg.copt_n_samples)
        dT_tol   = float(cfg.copt_dT_tol_K)
        R_pct    = float(cfg.copt_R_drift_pct)
        B_target = float(cfg.copt_B_T)
        T_target = float(cfg.copt_T_K)
        V_lim    = float(cfg.v_limit)

        if I_start <= 0 or I_max <= I_start or I_mult <= 1.0:
            err = (f"CURRENT_OPT ABORT: bad parameters "
                   f"(I_start={I_start*1e3:.3f}mA, I_max={I_max*1e3:.3f}mA, mult={I_mult})")
            logger.error(err)
            self._publish(LiveData(phase=err))
            return

        # ── Build geometric current list ────────────────────────────────────
        I_list = []
        I = I_start
        while I <= I_max + 1e-12:
            I_list.append(I)
            I = I * I_mult
        # Always include the ceiling exactly so the user knows whether I_max passed
        if I_list[-1] < I_max - 1e-12:
            I_list.append(I_max)

        n_steps = len(I_list)
        self._total_pts = n_steps
        self._sweep_t0  = t0

        # ── Set magnet to test field, ramp temperature to test T ────────────
        self._publish(LiveData(phase=f"CURRENT_OPT: magnet → {B_target:+.3f} T"))
        try:
            self._wait_B(B_target, t0)
        except Exception as e:
            logger.error(f"CURRENT_OPT: magnet move failed: {e}")
            self._publish(LiveData(phase=f"CURRENT_OPT ABORT: magnet → {B_target} T failed"))
            return

        self._publish(LiveData(phase=f"CURRENT_OPT: temperature → {T_target:.3f} K"))
        T_baseline = self._wait_T(T_target, t0)
        self.armed = True

        # ── Open output file ────────────────────────────────────────────────
        import os
        folder = (cfg.save_folder or '.').strip()
        try: os.makedirs(folder, exist_ok=True)
        except: pass
        fname = f"{cfg.sample_name}_CURRENT_OPT_{T_target:.3f}K_{B_target:+.4f}T.txt"
        fpath = os.path.join(folder, fname)
        # Anti-overwrite
        original_fpath = fpath
        fpath = _unique_path(fpath)
        if fpath != original_fpath:
            logger.info(f"CURRENT_OPT: file exists, auto-renamed to {os.path.basename(fpath)}")
            self._publish(LiveData(phase=
                f"File exists — saving as {os.path.basename(fpath)} (auto-renamed)"))
        try:
            f = open(fpath, 'w', encoding='utf-8')
        except Exception as e:
            logger.error(f"CURRENT_OPT: cannot open {fpath}: {e}")
            f = None

        if f:
            f.write(f"# Mode=CURRENT_OPT  |  Sample={cfg.sample_name}  |  "
                    f"T_target={T_target:.3f}K  |  B={B_target:+.4f}T  |  "
                    f"baseline T={T_baseline:.4f}K\n")
            f.write(f"# Stop criteria: dT_tol={dT_tol*1e3:.1f}mK  "
                    f"R_drift_max={R_pct:.2f}%  V_limit={V_lim:.2f}V\n")
            f.write(f"# Step\tI(mA)\tT_probe(K)\tdT(mK)\tVxx(V)\tVxy(V)\t"
                    f"Rxx(Ohm)\tRxy(Ohm)\tRxx_drift(%)\tSNR_Vxx\tStatus\n")
            f.flush()

        # ── Walk the current ladder ─────────────────────────────────────────
        results = []           # list of dicts, one per step
        Rxx_baseline = None    # set after the first step (lowest I)
        last_safe_I = None     # the largest I that passed all checks
        stop_reason = None

        for step_idx, I in enumerate(I_list):
            self._check_stop()

            self._publish(LiveData(
                phase=f"CURRENT_OPT step {step_idx+1}/{n_steps}: I = {I*1e3:.3f} mA "
                      f"(dwelling {dwell_s:.0f} s)"))

            # Set the SMU current. _measure_dc takes I_const from cfg, so
            # mutate cfg.I_const for this step. Save and restore at the end.
            cfg.I_const = I

            # Dwell at this current to allow thermal equilibration
            t_dwell_start = time.time()
            while time.time() - t_dwell_start < dwell_s:
                self._check_stop()
                time.sleep(0.5)

            # Take n_samp readings; average. Override cfg.avg_n locally.
            saved_avg_n = cfg.avg_n
            cfg.avg_n = max(1, n_samp)
            try:
                meas = self._measure(settle=0.05)
            finally:
                cfg.avg_n = saved_avg_n

            # Read probe temperature at the moment of measurement
            try:
                T_probe = float(self.itc.read_temperature(cfg.temp_device)[0]) if self.itc else float('nan')
            except Exception:
                T_probe = float('nan')

            Vxx  = float(meas.get('Vxxp_m', float('nan')))
            Vxy  = float(meas.get('Vxyp_m', float('nan')))
            Rxx  = float(meas.get('Rxx',    float('nan')))
            Rxy  = float(meas.get('Rxy',    float('nan')))
            rms_mO = float(meas.get('rms_noise_mOhm', float('nan')))

            dT = T_probe - T_baseline if (np.isfinite(T_probe) and np.isfinite(T_baseline)) else float('nan')

            # SNR estimate: mean Vxx / RMS noise (converted to V via Rxx)
            # rms_noise is in mΩ; convert: V_noise ≈ rms_noise_mOhm * 1e-3 * I
            V_noise = rms_mO * 1e-3 * I if np.isfinite(rms_mO) else float('nan')
            snr = abs(Vxx) / V_noise if (np.isfinite(V_noise) and V_noise > 0) else float('nan')

            # Establish baseline on the first valid Rxx reading
            if Rxx_baseline is None and np.isfinite(Rxx):
                Rxx_baseline = Rxx
                R_drift = 0.0
            elif Rxx_baseline is not None and np.isfinite(Rxx) and abs(Rxx_baseline) > 1e-12:
                R_drift = (Rxx - Rxx_baseline) / abs(Rxx_baseline) * 100.0
            else:
                R_drift = float('nan')

            # ── Apply stop criteria ────────────────────────────────────────
            this_status = "PASS"
            this_stop_reason = None
            if np.isfinite(dT) and dT > dT_tol:
                this_status = "FAIL"
                this_stop_reason = f"probe T rose by {dT*1e3:.1f} mK > {dT_tol*1e3:.1f} mK"
            elif np.isfinite(R_drift) and abs(R_drift) > R_pct:
                this_status = "FAIL"
                this_stop_reason = f"Rxx drifted by {R_drift:+.2f}% > ±{R_pct:.2f}%"
            elif np.isfinite(Vxx) and abs(Vxx) > 0.9 * V_lim:
                this_status = "FAIL"
                this_stop_reason = f"|Vxx|={abs(Vxx):.4f} V near compliance ({V_lim:.2f} V)"

            results.append({
                'step': step_idx+1, 'I': I, 'T_probe': T_probe, 'dT': dT,
                'Vxx': Vxx, 'Vxy': Vxy, 'Rxx': Rxx, 'Rxy': Rxy,
                'R_drift_pct': R_drift, 'snr': snr, 'status': this_status,
            })

            # Log + publish
            log_msg = (f"  I={I*1e3:7.3f} mA  T={T_probe:.4f} K (dT={dT*1e3:+5.1f} mK)  "
                       f"Vxx={Vxx:+.3e} V  Rxx={Rxx:.4f} Ω  drift={R_drift:+5.2f}%  "
                       f"SNR={snr:.0f}  → {this_status}")
            logger.info(log_msg)
            self._publish(LiveData(phase=log_msg))

            if f:
                f.write(f"{step_idx+1}\t{I*1e3:.4f}\t{T_probe:.4f}\t{dT*1e3:+.2f}\t"
                        f"{Vxx:+.6e}\t{Vxy:+.6e}\t{Rxx:.6f}\t{Rxy:.6f}\t"
                        f"{R_drift:+.3f}\t{snr:.2f}\t{this_status}\n")
                f.flush()

            if this_status == "PASS":
                last_safe_I = I
            else:
                stop_reason = this_stop_reason
                break

        self.armed = False

        # ── Restore SMU to a safe small current ─────────────────────────────
        cfg.I_const = max(I_start, last_safe_I) if last_safe_I else I_start
        try:
            ch = getattr(self, '_ch', 'smua')
            if self.smu:
                self.smu.write(f"{ch}.source.leveli = {cfg.I_const}")
        except Exception:
            pass

        # ── Build verdict ───────────────────────────────────────────────────
        if last_safe_I is None:
            verdict = ("CURRENT_OPT ABORT: no current passed all checks. "
                       f"Even I_start={I_start*1e3:.3f} mA failed. "
                       "Check: instruments connected, temperature stable, sample contacts ohmic.")
            verdict_kind = "ABORT"
        elif stop_reason is None:
            verdict = (f"CURRENT_OPT COMPLETE: all {n_steps} currents up to I={I_max*1e3:.3f} mA "
                       f"passed all checks. Recommended I = {last_safe_I*1e3:.3f} mA "
                       "(the ceiling — consider raising I_max if you need more signal).")
            verdict_kind = "OK"
        else:
            verdict = (f"CURRENT_OPT COMPLETE: stopped at step "
                       f"because {stop_reason}. "
                       f"Recommended I = {last_safe_I*1e3:.3f} mA "
                       "(the largest current that passed all checks).")
            verdict_kind = "OK"

        # Write summary footer to file
        if f:
            f.write(f"#\n# ─── VERDICT ────────────────────────────────────────────\n")
            f.write(f"# {verdict}\n")
            f.write(f"# Baseline T = {T_baseline:.4f} K\n")
            if Rxx_baseline is not None:
                f.write(f"# Baseline Rxx = {Rxx_baseline:.6f} Ω\n")
            f.close()

        logger.info("─" * 60)
        logger.info(verdict)
        logger.info("─" * 60)
        self._publish(LiveData(phase=verdict))


    def _run_iv_mode(self, t0):
        """IV (V-I) sweep mode.

        Steps current from −Imax to +Imax (and optionally back) in steps of
        Istep, measuring Vxx and Vxy at each point. Two sub-modes:

          * Passive (iv_active_bt = False): no IPS/iTC commands issued.
            User holds B and T externally. We read B and T for logging only.
            Tolerates iTC/IPS being unreachable; passive mode does not
            require them to be online.

          * Active (iv_active_bt = True): app sets IPS to iv_B_fixed_T and
            iTC to iv_T_fixed_K, waits for stability, then sweeps.

        After the sweep (success or abort) the SMU current is returned to 0
        before the standard shutdown path runs. The standard shutdown still
        ramps B → 0 and T → 1.5 K; in active mode this is the expected
        finishing position. In passive mode, the user may want to keep B
        and T as-is — they should manually disable the safe-shutdown if so,
        or simply tolerate the post-sweep zeroing.

        IV mode ignores cfg.I_const (the sweep generates its own current
        values from iv_Imax_A / iv_Istep_A) and forces source_mode = "DC"
        (MFLI continuous-AC sourcing is incompatible with stepped DC IV).

        Output: one file per sweep with the full Vxx, Vxy, I curve.
        Filename pattern: {sample}_IV_{T:.3f}K_{B:+.4f}T_{timestamp}.txt
        Columns: t(s), I_set(A), I_actual(A), Vxx(V), Vxy(V), Rxx(Ω), Rxy(Ω),
                 T_K, B_T, branch, point_idx
        """
        cfg = self.config

        # Defensive: ignore stale I_const and any non-DC source mode that may
        # have leaked in from a previous sweep's config. The frontend already
        # does this in getConfig(), but a programmatic /api/start caller
        # might not.
        cfg.I_const     = 0.0
        cfg.source_mode = "DC"

        # ── Sweep parameters ───────────────────────────────────────────────
        Imax    = float(cfg.iv_Imax_A)
        Istep   = float(cfg.iv_Istep_A)
        bidir   = bool(cfg.iv_bidirectional)
        active  = bool(cfg.iv_active_bt)
        B_set   = float(cfg.iv_B_fixed_T)
        T_set   = float(cfg.iv_T_fixed_K)
        settle  = float(cfg.iv_settle_s)
        show_as = bool(cfg.iv_show_antisymm)
        V_lim   = float(cfg.v_limit)

        # ── Parameter validation ───────────────────────────────────────────
        if Imax <= 0 or Istep <= 0 or Istep > Imax:
            err = (f"IV ABORT: invalid parameters "
                   f"(Imax={Imax*1e3:.4f}mA, Istep={Istep*1e3:.4f}mA). "
                   f"Need Imax > 0 and 0 < Istep ≤ Imax.")
            logger.error(err)
            self._publish(LiveData(phase=err))
            return

        # Compliance / range check. The NVM range bounds the |Vxx| we can read.
        # If the user's expected resistance × Imax would exceed the range, warn.
        # We don't have R a-priori, so use a conservative estimate: if there's
        # an NVM range set, V_max = nvm_range * 0.9 (NVM headroom).
        try:
            V_lim_nvm = float(cfg.nvm_range) if cfg.nvm_range and cfg.nvm_range > 0 else V_lim
            # Estimate dissipation at full current with 1 kΩ guess (typical 2D sample)
            R_guess = 1000.0
            P_max_mW = (Imax ** 2) * R_guess * 1000.0
            if P_max_mW > 1.0:
                msg = (f"IV WARN: at Imax={Imax*1e3:.3g}mA with assumed R≈{R_guess}Ω, "
                       f"max dissipation ≈ {P_max_mW:.2f} mW — risk of sample self-heating "
                       f"for small/poorly-anchored samples. Consider reducing Imax.")
                logger.warning(msg)
                self._publish(LiveData(phase=msg, sweep_mode="IV"))
        except Exception:
            pass

        # Build current list: −Imax, −Imax+Istep, ..., 0, ..., +Imax
        # We include 0 by construction if (2·Imax/Istep) is an even integer.
        # For generic Istep we still include 0 by hand for cleanliness.
        n_half = int(math.ceil(Imax / Istep))
        I_pos  = [i * Istep for i in range(n_half + 1) if i * Istep <= Imax + 1e-15]
        # Ensure exact endpoint
        if not I_pos or I_pos[-1] < Imax - 1e-15:
            I_pos.append(Imax)
        I_neg = [-x for x in I_pos[1:]]   # 0 excluded to avoid duplication
        I_forward = sorted(I_neg + I_pos)  # −Imax → +Imax, includes 0
        I_return  = list(reversed(I_forward))[1:] if bidir else []  # drop +Imax (already done)

        sweep_legs = [("forward", I_forward)]
        if bidir:
            sweep_legs.append(("return", I_return))

        n_steps = sum(len(leg) for _, leg in sweep_legs)
        self._total_pts = n_steps
        self._sweep_t0  = t0

        logger.info(f"IV sweep: Imax={Imax*1e3:.4g} mA, Istep={Istep*1e3:.4g} mA, "
                    f"bidirectional={bidir}, active_bt={active}, n_points={n_steps}")

        # ── Configure SMU current range for IV sweep ─────────────────────────
        # _configure_smu set the range based on cfg.I_const which is 0 in IV
        # mode → range gets set to the lowest. We need to override it for
        # the IV sweep range. Pick the smallest standard Keithley range that
        # contains Imax — gives best resolution.
        #
        # Standard Keithley 2600-series source-current ranges (A):
        #   1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1, 1.5, 3
        # Without an explicit range setting the SMU rejects with error 5005
        # ("Value too big for range") when leveli > rangei.
        if self.smu:
            try:
                ch = self._ch
                # Find smallest range that contains Imax.
                # Use a small margin (1%) so we're not sitting at the absolute
                # edge of the range — that protects against floating-point
                # boundary nudges but doesn't push every measurement up by
                # a full decade.
                standard_ranges = [1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2,
                                    1e-1, 1.0, 1.5, 3.0]
                Imax_padded = Imax * 1.01
                target_range = None
                for r in standard_ranges:
                    if r >= Imax_padded:
                        target_range = r
                        break
                if target_range is None:
                    # Imax exceeds even 3 A — clearly wrong for our setup
                    err = (f"IV ABORT: Imax = {Imax*1e3:.4g} mA exceeds the "
                           f"largest standard SMU range (3 A). Check Imax value.")
                    logger.error(err)
                    self._publish(LiveData(phase=err, sweep_mode="IV"))
                    return

                # Set the SMU's source-current range and turn output ON.
                # Disable autoranging — we want the range fixed for the whole
                # sweep so noise characteristics are uniform across all I.
                # measure.rangev (voltage measurement) stays on autorange.
                self.smu.write(f"""
{ch}.source.func = {ch}.OUTPUT_DCAMPS
{ch}.source.autorangei = {ch}.AUTORANGE_OFF
{ch}.source.rangei = {target_range}
{ch}.source.limitv = {V_lim}
{ch}.source.leveli = 0
{ch}.measure.autorangev = {ch}.AUTORANGE_ON
{ch}.source.output = {ch}.OUTPUT_ON
""")
                time.sleep(0.3)
                # Drain the SMU error queue. With the new _configure_smu
                # already clearing TSP state at the top, any error here is
                # genuinely from THIS configuration sequence (most likely
                # 5005 if Imax doesn't fit the chosen range, or -286 if
                # something else is wrong with the script engine).
                try:
                    for _i in range(5):
                        err_str = self.smu.query("print(errorqueue.next())").strip()
                        if not err_str or err_str.startswith("0\t") \
                           or "0.00000e+00" in err_str:
                            break
                        if "-286" in err_str or "Script Aborted" in err_str:
                            logger.warning(
                                f"IV: residual TSP error -286 after config — "
                                f"this is left over from a previous aborted "
                                f"sweep and has now been cleared. The current "
                                f"sweep should proceed normally.")
                            # Continue draining, don't surface as a hard error
                            continue
                        # Other errors (5005, etc.) — surface and abort
                        logger.error(f"IV: SMU error after range setup: {err_str}")
                        self._publish(LiveData(
                            phase=f"IV: SMU error {err_str}", sweep_mode="IV"))
                        break
                except Exception:
                    pass

                logger.info(f"IV: SMU source range set to {target_range:.0e} A "
                            f"(Imax = {Imax:.3e} A, V_limit = {V_lim:.2f} V)")
                self._publish(LiveData(
                    phase=f"IV: SMU range = {target_range:.0e} A, V_limit = {V_lim:.2f} V",
                    sweep_mode="IV"))
            except Exception as e:
                err = f"IV ABORT: SMU range configuration failed: {e}"
                logger.error(err)
                self._publish(LiveData(phase=err, sweep_mode="IV"))
                return
        else:
            logger.warning("IV: no SMU connection — sweep will run but cannot source current")
            self._publish(LiveData(
                phase="IV WARN: no SMU connection — no current will flow",
                sweep_mode="IV"))

        # ── Active mode: set magnet and temperature ────────────────────────
        if active:
            # Active mode requires both iTC and IPS. The run() prelude only
            # tolerates failures in passive mode, so reaching here with one
            # of them None means the user enabled active mode but instrument
            # comms broke between connection and here — fail with a clear
            # message rather than the AttributeError that would otherwise hit.
            if self.itc is None or self.ips is None:
                missing = []
                if self.itc is None: missing.append("iTC")
                if self.ips is None: missing.append("IPS")
                err = (f"IV ABORT: active mode requires {', '.join(missing)} "
                       f"but they are not connected. Either switch off 'Active "
                       f"B/T control' to run in passive mode, or fix the "
                       f"instrument connection and retry.")
                logger.error(err)
                self._publish(LiveData(phase=err, sweep_mode="IV"))
                return
            self._publish(LiveData(
                phase=f"IV (active): waiting for B → {B_set:+.4f} T", sweep_mode="IV"))
            try:
                self._wait_B(B_set, t0)
            except Exception as e:
                logger.error(f"IV: magnet move failed: {e}")
                self._publish(LiveData(phase=f"IV ABORT: magnet → {B_set} T failed",
                                       sweep_mode="IV"))
                return

            self._publish(LiveData(
                phase=f"IV (active): waiting for T → {T_set:.3f} K", sweep_mode="IV"))
            try:
                T_stable = self._wait_T(T_set, t0)
            except Exception as e:
                logger.error(f"IV: temperature stabilisation failed: {e}")
                self._publish(LiveData(phase=f"IV ABORT: T → {T_set} K failed",
                                       sweep_mode="IV"))
                return
        else:
            # Passive mode: just read current B and T for the file header
            self._publish(LiveData(phase="IV (passive): reading current B, T",
                                   sweep_mode="IV"))
            try:
                T_stable = float(self.itc.read_temperature(cfg.temp_device)) \
                           if self.itc else float('nan')
            except Exception:
                T_stable = float('nan')
            try:
                if self.ips:
                    bval, _ok = self.ips.read_field(cfg.field_group)
                    B_set = float(bval)
                else:
                    # IPS unavailable in passive mode — flag B as unknown, not zero.
                    # The user is holding the field externally; we can't infer it.
                    B_set = float('nan')
            except Exception:
                B_set = float('nan')
            T_set = T_stable

        self.armed = True

        # ── Open output file ───────────────────────────────────────────────
        import os
        folder = (cfg.save_folder or '.').strip()
        try: os.makedirs(folder, exist_ok=True)
        except: pass
        ts_str = time.strftime("%Y%m%d-%H%M%S")
        # Build filename components defensively — passive mode may have nan
        # for T or B when the iTC/IPS are offline.
        import math as _math
        T_part = f"{T_set:.3f}K" if _math.isfinite(T_set) else "Tunknown"
        B_part = f"{B_set:+.4f}T" if _math.isfinite(B_set) else "Bunknown"
        fname = f"{cfg.sample_name}_IV_{T_part}_{B_part}_{ts_str}.txt"
        fpath = os.path.join(folder, fname)
        # Anti-overwrite (consistent with other modes)
        original_fpath = fpath
        fpath = _unique_path(fpath)
        if fpath != original_fpath:
            logger.info(f"IV: file exists, auto-renamed to {os.path.basename(fpath)}")
            self._publish(LiveData(
                phase=f"File exists — saving as {os.path.basename(fpath)} (auto-renamed)",
                sweep_mode="IV"))
        try:
            f = open(fpath, 'w', encoding='utf-8')
        except Exception as e:
            logger.error(f"IV: cannot open {fpath}: {e}")
            f = None

        if f:
            mode_str = "active" if active else "passive"
            B_held_str = f"{B_set:+.5f} T" if _math.isfinite(B_set) else "unknown (passive, IPS offline)"
            T_held_str = f"{T_set:.4f} K" if _math.isfinite(T_set) else "unknown (passive, iTC offline)"
            f.write(f"# Mode=IV ({mode_str})  |  Sample={cfg.sample_name}\n")
            f.write(f"# B_held={B_held_str}  |  T_held={T_held_str}  "
                    f"|  Imax={Imax*1e3:.5g} mA  |  Istep={Istep*1e3:.5g} mA\n")
            f.write(f"# Bidirectional={bidir}  |  Settle={settle:.3f} s  "
                    f"|  V_limit={V_lim:.2f} V  |  NPLC={cfg.nplc}\n")
            if cfg.sweep_notes:
                f.write(f"# Notes: {cfg.sweep_notes}\n")
            f.write("# t(s)\tI_set(A)\tI_actual(A)\tVxx(V)\tVxy(V)\t"
                    "Rxx(Ohm)\tRxy(Ohm)\tT(K)\tB(T)\tbranch\tpoint_idx\n")
            f.flush()

        # ── Save initial cfg.I_const so we can restore at the end ─────────
        saved_I_const = cfg.I_const
        saved_current_reverse = bool(getattr(cfg, 'current_reverse', False))
        # For IV mode we don't want current reversal — each point is its own I
        cfg.current_reverse = False

        # ── Walk every leg ─────────────────────────────────────────────────
        all_I  = []   # list[float]   — for fit
        all_Vx = []   # list[float]
        point_idx = 0
        try:
            for branch_name, I_list in sweep_legs:
                for I_target in I_list:
                    self._check_stop()
                    point_idx += 1

                    # Set the SMU to this I, dwell for settle
                    cfg.I_const = I_target
                    # _measure_dc will set leveli to I_target inside its
                    # set_I helper, then read after the settle_s passed in.
                    # We use the IV-specific settle.
                    polarity = +1 if I_target >= 0 else -1

                    self._publish(LiveData(
                        phase=(f"IV {branch_name} {point_idx}/{n_steps}: "
                               f"I = {I_target*1e3:+.4f} mA"),
                        sweep_mode="IV",
                        progress_frac=point_idx / max(1, n_steps),
                        n_pts=point_idx, total_pts=n_steps))

                    try:
                        meas = self._measure(settle=settle)
                    except Exception as e:
                        logger.warning(f"IV point {point_idx}: measurement failed: {e}")
                        continue

                    # meas dict in non-reverse path returns Ip_m, Vxxp_m, Vxyp_m, Rxx, Rxy
                    I_act  = float(meas.get('Ip_m',   float('nan')))
                    Vxx    = float(meas.get('Vxxp_m', float('nan')))
                    Vxy    = float(meas.get('Vxyp_m', float('nan')))
                    Rxx    = float(meas.get('Rxx',    float('nan')))
                    Rxy    = float(meas.get('Rxy',    float('nan')))

                    # Read T, B for per-point logging (low cost compared to settle)
                    try:
                        T_now = float(self.itc.read_temperature(cfg.temp_device)) \
                                if self.itc else float('nan')
                    except Exception:
                        T_now = float('nan')
                    try:
                        if self.ips:
                            bval, _ok = self.ips.read_field(cfg.field_group)
                            B_now = float(bval)
                        else:
                            B_now = float('nan')
                    except Exception:
                        B_now = float('nan')

                    t_now = time.time() - t0
                    all_I.append(I_target)
                    all_Vx.append(Vxx)

                    # Running linear fit (only on points with finite Vxx)
                    fit_R = None
                    fit_R2 = None
                    if len(all_I) >= 4:
                        try:
                            arr_I  = np.array(all_I,  dtype=float)
                            arr_Vx = np.array(all_Vx, dtype=float)
                            ok = np.isfinite(arr_I) & np.isfinite(arr_Vx)
                            if int(ok.sum()) >= 4:
                                p = np.polyfit(arr_I[ok], arr_Vx[ok], 1)
                                fit_R = float(p[0])      # slope = R (Ω)
                                v_fit = np.polyval(p, arr_I[ok])
                                ss_res = float(np.sum((arr_Vx[ok] - v_fit) ** 2))
                                ss_tot = float(np.sum((arr_Vx[ok] - np.mean(arr_Vx[ok])) ** 2))
                                fit_R2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0
                        except Exception:
                            pass

                    # Stream the point to the live plot
                    self._publish(LiveData(
                        sweep_mode="IV",
                        I_mA=I_target * 1e3,
                        I_set_A=I_target,
                        Vxx_V=Vxx, Vxy_V=Vxy,
                        Rxx_Ohm=Rxx, Rxy_Ohm=Rxy,
                        T_K=T_now, B_T=B_now,
                        main_x=I_target, main_Vxx=Vxx, main_Vxy=Vxy,
                        iv_branch=branch_name,
                        iv_polarity=polarity,
                        iv_fit_R=fit_R, iv_fit_R2=fit_R2,
                        t_s=t_now,
                        progress_frac=point_idx / max(1, n_steps),
                        n_pts=point_idx, total_pts=n_steps))

                    # Per-point file write
                    if f:
                        try:
                            f.write(f"{t_now:.3f}\t{I_target:.9g}\t{I_act:.9g}\t"
                                    f"{Vxx:.9g}\t{Vxy:.9g}\t"
                                    f"{Rxx:.9g}\t{Rxy:.9g}\t"
                                    f"{T_now:.4f}\t{B_now:+.5f}\t"
                                    f"{branch_name}\t{point_idx}\n")
                            f.flush()
                        except Exception as e:
                            logger.warning(f"IV: log write failed at point {point_idx}: {e}")

                    self._n_pts = point_idx

        finally:
            # ── Restore config and return SMU to I = 0 ─────────────────────
            cfg.I_const = saved_I_const
            cfg.current_reverse = saved_current_reverse
            try:
                if self.smu:
                    ch = self._ch
                    self.smu.write(f"{ch}.source.leveli = 0")
                    # Don't switch the output OFF here — the run() finally
                    # block does that as part of the standard shutdown.
                    self._publish(LiveData(phase="IV: returning SMU current to 0 A",
                                           sweep_mode="IV"))
            except Exception as e:
                logger.warning(f"IV: could not zero SMU current: {e}")

            if f:
                # Final summary line at the end of the file
                if all_I and all_Vx:
                    try:
                        arr_I  = np.array(all_I,  dtype=float)
                        arr_Vx = np.array(all_Vx, dtype=float)
                        ok = np.isfinite(arr_I) & np.isfinite(arr_Vx)
                        if int(ok.sum()) >= 4:
                            p = np.polyfit(arr_I[ok], arr_Vx[ok], 1)
                            R_fit = float(p[0])
                            offset = float(p[1])
                            v_fit = np.polyval(p, arr_I[ok])
                            ss_res = float(np.sum((arr_Vx[ok] - v_fit) ** 2))
                            ss_tot = float(np.sum((arr_Vx[ok] - np.mean(arr_Vx[ok])) ** 2))
                            R2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0
                            f.write(f"# Linear fit (all {int(ok.sum())} valid points): "
                                    f"R = {R_fit:.6g} Ω  ·  V_offset = {offset:.6g} V  ·  "
                                    f"R² = {R2:.5f}\n")
                            verdict = (f"IV COMPLETE — R = {R_fit:.4g} Ω, "
                                       f"R² = {R2:.4f}, n = {int(ok.sum())} points, "
                                       f"file = {os.path.basename(fpath)}")
                            logger.info(verdict)
                            self._publish(LiveData(phase=verdict, sweep_mode="IV"))
                    except Exception as e:
                        logger.warning(f"IV: final fit failed: {e}")
                try: f.close()
                except: pass


    def run(self):
        t0 = time.time()
        # ── Sample log ────────────────────────────────────────────────────
        self._log_id  = _append_sample_log(self.config, "STARTED",
                                             notes=getattr(self.config, 'sweep_notes', ''))
        self._n_pts   = 0    # incremented in _add_point
        try:
            self._publish(LiveData(phase="CONNECTING", sweep_mode=self.config.mode))

            mode = getattr(self.config, 'source_mode', 'DC')
            if mode in ('MFLI', 'MFLI_SINGLE', 'MFLI_DUAL'):
                # ── MFLI lock-in path ─────────────────────────────────────────
                if zi is None:
                    raise ImportError("zhinst not installed — pip install zhinst")
                cfg = self.config
                I_ac = cfg.mfli_output_amplitude / cfg.mfli_series_resistance

                # Master (DEV6568) — excitation + Vxx
                self.mfli = MFLI(
                    device_id         = cfg.mfli_device_id,
                    host              = cfg.mfli_host,
                    port              = cfg.mfli_port,
                    frequency         = cfg.mfli_frequency,
                    output_amplitude  = cfg.mfli_output_amplitude,
                    series_resistance = cfg.mfli_series_resistance,
                    time_constant     = cfg.mfli_time_constant,
                    filter_order      = cfg.mfli_filter_order,
                    input_range       = cfg.mfli_input_range,
                    output_range      = cfg.mfli_output_range,
                    settle_tc         = cfg.mfli_settle_tc,
                    role              = "master",
                    logger            = self.logger,
                )
                self.mfli.open()
                self.mfli.configure()

                if mode == 'MFLI_DUAL':
                    # Slave (DEV6597) — Vxy, locked to master 10 MHz clock
                    self.mfli_slave = MFLI(
                        device_id         = cfg.mfli_slave_device_id,
                        host              = cfg.mfli_host,    # same LabOne server
                        port              = cfg.mfli_port,
                        frequency         = cfg.mfli_frequency,
                        output_amplitude  = cfg.mfli_output_amplitude,
                        series_resistance = cfg.mfli_series_resistance,
                        time_constant     = cfg.mfli_time_constant,
                        filter_order      = cfg.mfli_filter_order,
                        input_range       = cfg.mfli_slave_input_range,
                        output_range      = cfg.mfli_output_range,
                        settle_tc         = cfg.mfli_settle_tc,
                        role              = "slave",
                        logger            = self.logger,
                    )
                    self.mfli_slave.open()
                    self.mfli_slave.configure()
                    self._publish(LiveData(
                        phase="MFLI DUAL connected",
                        progress=f"Master={cfg.mfli_device_id} (Vxx) | "
                                 f"Slave={cfg.mfli_slave_device_id} (Vxy) | "
                                 f"f={cfg.mfli_frequency} Hz | "
                                 f"I_ac={I_ac*1e9:.2f} nA"
                    ))
                else:
                    self._publish(LiveData(
                        phase="MFLI SINGLE connected",
                        progress=f"{cfg.mfli_device_id} | "
                                 f"f={cfg.mfli_frequency} Hz | "
                                 f"I_ac={I_ac*1e9:.2f} nA"
                    ))
            else:
                # ── DC path: Keithley SMU + 2× 2182A NVM ─────────────────────
                if pyvisa is None:
                    raise ImportError("pyvisa not installed")
                rm = pyvisa.ResourceManager()
                self.smu = rm.open_resource(self.config.smu_resource)
                self.smu.write_termination = "\n"
                self.smu.read_termination = "\n"
                self.smu.timeout = 30000
                self.nvm1 = Serial2182A(self.config.com_port_1)
                self.nvm2 = Serial2182A(self.config.com_port_2)
                self._configure_nvm(self.nvm1)
                self._configure_nvm(self.nvm2)
                self._configure_smu()
                # ── Gate bias (second SMU channel) ────────────────────────
                if getattr(self.config, 'gate_enable', False):
                    g_ch = getattr(self.config, 'gate_channel', 'A').upper()
                    self._gate_ch  = "smua" if g_ch == "A" else "smub"
                    # Gate shares the same VISA resource as the current SMU
                    self.gate_smu = self.smu
                    self._configure_gate()
                    logger.info(f"Gate channel {self._gate_ch} ready on shared SMU")

            # ── Cryostat ──────────────────────────────────────────────────────
            # For IV passive mode (mode == "IV" and iv_active_bt == False) we
            # treat the iTC and IPS as OPTIONAL — passive means "user holds
            # B and T externally", so the app should not depend on those
            # instruments being reachable. If they connect, great: we read
            # B and T for logging. If they don't, we proceed anyway and the
            # per-point reads return NaN.
            # For every other mode the iTC and IPS are required.
            # ── Optional passive-mode tolerance for cryostat instruments ──
            # When iTC and/or IPS are offline, normally we hard-fail at the
            # connection step. But for some modes the sweep is still useful
            # without active T/B control:
            #
            #   IV passive       — user explicitly ticked the passive box,
            #                      meaning they accept reading-only behaviour
            #   TCSCAN           — user wants to run the T scan; if IPS is
            #                      offline, B is uncontrolled and the file
            #                      records actual B (or NaN). The T scan
            #                      itself still works as long as iTC is OK.
            #   TCSCAN_MULTI_B   — same: each scan proceeds with whatever B
            #                      actually is, instead of failing entirely.
            #
            # The data file in passive mode honestly records what was
            # measured rather than what was requested — no false claims of
            # field/temperature accuracy.
            cryostat_passive_ok = (
                (self.config.mode == "IV"
                 and not bool(getattr(self.config, 'iv_active_bt', False)))
                or self.config.mode in ("TCSCAN", "TCSCAN_MULTI_B", "RAMP")
            )
            self.itc = None
            self.ips = None
            try:
                self.itc = MercuryITC(self.config.itc_ip, port=self.config.itc_port)
                self.itc.open()
            except Exception as e:
                if cryostat_passive_ok:
                    msg = (f"{self.config.mode}: iTC unavailable ({e}); "
                           f"continuing without T control — recorded T will be NaN")
                    logger.info(msg)
                    self._publish(LiveData(progress=msg, sweep_mode=self.config.mode))
                    self.itc = None
                else:
                    raise
            try:
                self.ips = MercuryIPS(self.config.ips_ip, port=self.config.ips_port,
                                       group=self.config.field_group)
                self.ips.open()
            except Exception as e:
                if cryostat_passive_ok:
                    msg = (f"{self.config.mode}: IPS unavailable ({e}); "
                           f"continuing without B control — recorded B will be NaN "
                           f"(magnet stays at whatever field it currently has)")
                    logger.info(msg)
                    self._publish(LiveData(progress=msg, sweep_mode=self.config.mode))
                    self.ips = None
                else:
                    raise
            self._publish(LiveData(phase="CONNECTED"))

            # Reset the one-shot debug log sentinel so the proof-of-flip message
            # fires on this sweep (it's set after the first measurement).
            self._logged_reversal_proof = False

            # ── Log the thermal-EMF cancellation scheme for transparency ──
            if bool(getattr(self.config, 'current_reverse', False)):
                _rs = float(getattr(self.config, 'reverse_settle_s', 0.2))
                logger.info(
                    f"Current reversal: ON (interleaved per-pair scheme). "
                    f"Each measurement point takes {self.config.avg_n} ±I pairs "
                    f"with {_rs:.3f} s settle per polarity flip. Drift slower "
                    f"than ~{2*_rs:.2f} s cancels in the per-pair difference."
                )

            # ── NVM REL auto-zero (thermal-EMF offset removal) ──────────────
            # Runs AFTER the cryostat connection block so the long iTC/IPS
            # connect timeout doesn't interrupt the 2182A REF:ACQ sequence.
            # By this point all blocking network I/O is finished, so the NVMs
            # can complete their acquire-and-store cycle without preemption.
            #
            # Uses the SCPI dialect verified by probe_2182a.py on firmware
            # C08/B01: SENS:VOLT:DC:REF:ACQ / :STAT ON / :STAT OFF / :REF?.
            # Skips silently if auto_zero_rel = False, or if the SMU isn't
            # connected.
            try:
                self._zero_nvm_rel()
            except Exception as _e:
                logger.warning(f"NVM auto-zero failed (continuing without REL): {_e}")

            if self.config.mode == "STEP":
                self._run_step_mode(t0)
                # ── Auto-symmetrise STEP data files if enabled ────────────
                if getattr(self.config, 'auto_symmetrise', True):
                    try:
                        n_sym = _auto_symmetrise_step(self.config)
                        if n_sym > 0:
                            self._publish(LiveData(
                                progress=f"Auto-symmetrised {n_sym} temperature file(s) → *_sym.txt"))
                    except Exception as _e:
                        logger.warning(f"Auto-symmetrise failed: {_e}")
            elif self.config.mode == "STEP2":
                self._run_step2_mode(t0)
            elif self.config.mode == "STEP3":
                self._run_step3_mode(t0)
            elif self.config.mode == "RELAX":
                self._run_relax_mode(t0)
            elif self.config.mode == "RELAX_SCAN":
                self._run_relax_scan_mode(t0)
            elif self.config.mode == "TCSCAN":
                self._run_tcscan_mode(t0)
            elif self.config.mode == "TCSCAN_MULTI_B":
                self._run_tcscan_multi_b_mode(t0)
            elif self.config.mode == "HYSTERESIS":
                self._run_hysteresis_mode(t0)
                # Auto-symmetrise the per-T files (each contains ±B paired data)
                if getattr(self.config, 'auto_symmetrise', True):
                    try:
                        n_sym = _auto_symmetrise_hysteresis(self.config)
                        if n_sym > 0:
                            self._publish(LiveData(
                                progress=f"Auto-symmetrised {n_sym} hysteresis file(s) → *_sym.txt"))
                    except Exception as _e:
                        logger.warning(f"Auto-symmetrise failed: {_e}")
            elif self.config.mode == "ANGLE_HYST":
                self._run_angle_hyst_mode(t0)
                if getattr(self.config, 'auto_symmetrise', True):
                    try:
                        n_sym = _auto_symmetrise_angle(self.config)
                        if n_sym > 0:
                            self._publish(LiveData(
                                progress=f"Auto-symmetrised {n_sym} angle-loop file(s) → *_sym.txt"))
                    except Exception as _e:
                        logger.warning(f"Auto-symmetrise failed: {_e}")
            elif self.config.mode == "CURRENT_OPT":
                self._run_current_opt_mode(t0)
            elif self.config.mode == "IV":
                self._run_iv_mode(t0)
            elif self.config.mode == "RAMP":
                self._run_ramp_mode(t0)
            else:
                # Unknown mode — fall back to RAMP for back-compat and log a
                # warning so it shows up clearly in the user log.
                logger.warning(f"Unknown mode '{self.config.mode}'; falling back to RAMP")
                self._run_ramp_mode(t0)
            self._publish(LiveData(phase="COMPLETE"))
            _update_sample_log(self._log_id, "COMPLETED",
                               time.time() - t0, self._n_pts)
        except Exception as e:
            logger.error(f"Sweep failed: {e}")
            self._publish(LiveData(phase="ERROR", progress=str(e)))
            _update_sample_log(self._log_id, "ABORTED",
                               time.time() - t0, self._n_pts)
        finally:
            # Hard-zero the current source immediately in all exit paths
            # (normal complete, error, manual stop, exception).
            # _safe_shutdown then ramps B→0 and T→1.5K.
            try:
                if self.smu:
                    ch = self._ch
                    self.smu.write(f"{ch}.source.leveli = 0")
                    self.smu.write(f"{ch}.source.output = {ch}.OUTPUT_OFF")
            except Exception:
                pass
            try:
                if self.mfli: self.mfli.output_off()
                if self.mfli_slave: self.mfli_slave.output_off()
            except Exception:
                pass
            # Disable NVM REL so the next sweep doesn't inherit this run's
            # captured reference. Uses STAT OFF only — we leave the stored
            # REF value alone (it's harmless when STAT is OFF).
            try:
                self._clear_nvm_rel()
            except Exception:
                pass
            self._publish(LiveData(phase="SHUTDOWN: I → 0 A  ·  ramping B → 0T  ·  T → 1.5K"))
            self._safe_shutdown()

    def _safe_shutdown(self):
        global _next_conditions
        # Capture and clear the bridge target atomically
        with lock:
            bridge = _next_conditions
            _next_conditions = None

        # ── 0. Ramp gate back to 0 V safely before anything else ───────
        try:
            self._gate_off()
        except Exception as _ge:
            logger.warning(f"Gate shutdown: {_ge}")

        # ── 1. Turn off excitation source immediately ──────────────────
        if self.mfli:
            try: self.mfli.output_off()
            except: pass
        if self.mfli_slave:
            try: self.mfli_slave.output_off()
            except: pass
        if self.smu:
            try:
                ch = self._ch
                self.smu.write(f"{ch}.source.leveli = 0")
                self.smu.write(f"{ch}.source.output = {ch}.OUTPUT_OFF")
                # Cancel any pending TSP operation. Must be channel-scoped
                # and called as a function: `smua.abort()` not `abort` or
                # `smua.abort` (the latter two are syntax errors → -285).
                self.smu.write(f"{ch}.abort()")
                self.smu.close()
            except: pass

        if bridge:
            # ── BRIDGE MODE: next sweep queued — go to its start conditions ──
            # Skip the full ramp-to-base; instead drive T and B to the values
            # the next sweep will need.  This saves the time & helium needed to
            # cool all the way to base and then back up again.
            B_tgt = float(bridge.get("B_start", 0.0))
            T_tgt = float(bridge.get("T_start", 1.5))
            self._publish(LiveData(phase=f"BRIDGE: B → {B_tgt:+.3f} T for next sweep"))
            if self.ips:
                try:
                    self.ips.set_switch_heater(True, self.config.field_group); time.sleep(3)
                    rr = float(self.config.ramp_rate_B)
                    if rr > 0:
                        self.ips.set_ramp_rate_field(rr, self.config.field_group); time.sleep(0.5)
                    self.ips.set_target_field(B_tgt, self.config.field_group); time.sleep(0.5)
                    self.ips.set_to_setpoint(self.config.field_group)
                    deadline = time.time() + 300
                    while time.time() < deadline:
                        B_now, _ = self.ips.read_field(self.config.field_group)
                        self._publish(LiveData(
                            phase=f"BRIDGE: B = {B_now:.4f} T → {B_tgt:+.3f} T"))
                        if abs(B_now - B_tgt) <= self.config.tol_B:
                            break
                        time.sleep(2.0)
                    self.ips.set_hold(self.config.field_group)
                except Exception as e:
                    logger.warning(f"Bridge field error: {e}")
            self._publish(LiveData(phase=f"BRIDGE: T → {T_tgt:.3f} K for next sweep"))
            if self.itc:
                try:
                    self.itc.set_ramp_rate(5.0, self.config.temp_device)
                    self.itc.set_ramp_mode(True, self.config.temp_device)
                    self.itc.set_control_mode("AUTO", self.config.temp_device)
                    self.itc.set_temperature_setpoint(T_tgt, self.config.temp_device)
                    # ── VTI: ramp alongside probe to bridge target ────────────
                    self._set_vti(T_tgt, enable_ramp=True, ramp_rate=5.0)
                    deadline = time.time() + 900   # 15 min max for bridge
                    while time.time() < deadline:
                        T_now = self.itc.read_temperature(self.config.temp_device)
                        if T_now and T_now > 0:
                            self._publish(LiveData(
                                phase=f"BRIDGE: T = {T_now:.3f} K → {T_tgt:.3f} K"))
                            if abs(T_now - T_tgt) <= self.config.tol_T * 3:
                                break
                        time.sleep(3.0)
                except Exception as e:
                    logger.warning(f"Bridge temperature error: {e}")

        else:
            # ── FULL SHUTDOWN: last sweep or manual stop — ramp to base ──
            # ── 2. Ramp field to zero ──────────────────────────────────────
            if self.ips:
                try:
                    self._publish(LiveData(phase="SHUTDOWN: ramping B → 0 T"))
                    # Mirror the same sequence used in _wait_B: heater on, rate, target, go
                    self.ips.set_switch_heater(True, self.config.field_group)
                    time.sleep(3)
                    rr = float(self.config.ramp_rate_B)
                    if rr > 0:
                        self.ips.set_ramp_rate_field(rr, self.config.field_group)
                        time.sleep(0.5)
                    self.ips.set_target_field(0.0, self.config.field_group)
                    time.sleep(0.5)
                    self.ips.set_to_setpoint(self.config.field_group)
                    deadline = time.time() + 300  # 5 min max
                    while time.time() < deadline:
                        B_now, _ = self.ips.read_field(self.config.field_group)
                        self._publish(LiveData(phase=f"SHUTDOWN: B = {B_now:.4f} T → 0"))
                        if abs(B_now) <= 0.002:
                            break
                        time.sleep(2.0)
                    self.ips.set_hold(self.config.field_group)
                except Exception as e:
                    logger.warning(f"Field shutdown error: {e}")

            # ── 3. Ramp temperature to 1.5 K ──────────────────────────────
            if self.itc:
                try:
                    self._publish(LiveData(phase="SHUTDOWN: cooling T → 1.5 K"))
                    cfg = self.config
                    self.itc.set_ramp_rate(5.0, cfg.temp_device)   # 5 K/min cool-down
                    self.itc.set_ramp_mode(True, cfg.temp_device)
                    self.itc.set_control_mode("AUTO", cfg.temp_device)
                    self.itc.set_temperature_setpoint(1.5, cfg.temp_device)
                    # ── VTI: cool to base alongside probe ─────────────────────
                    self._set_vti(1.5, enable_ramp=True, ramp_rate=5.0)
                    deadline = time.time() + 1800  # 30 min max
                    while time.time() < deadline:
                        T_now = self.itc.read_temperature(cfg.temp_device)
                        if T_now and T_now > 0:
                            self._publish(LiveData(phase=f"SHUTDOWN: T = {T_now:.3f} K → 1.5 K"))
                            if T_now <= 1.7:  # within 0.2 K of target
                                break
                        time.sleep(3.0)
                except Exception as e:
                    logger.warning(f"Temperature shutdown error: {e}")

        # ── 4. Flush and close open data file ─────────────────────────
        if self._data_file:
            try:
                self._data_file.flush()
                self._data_file.close()
                self._data_file = None
            except Exception:
                pass

        # ── 5. Close all instruments ───────────────────────────────────
        if self.mfli:
            try: self.mfli.close()
            except: pass
        if self.mfli_slave:
            try: self.mfli_slave.close()
            except: pass
        for inst in [self.nvm1, self.nvm2, self.itc, self.ips]:
            try:
                if inst: inst.close()
            except: pass
        self._publish(LiveData(phase="IDLE"))


# =============================================================================
# AUTO-SYMMETRISATION  –  called at end of a completed STEP sweep
# For each *_STEP_*K.txt file, produces a *_STEP_*K_sym.txt with:
#   Rxx_sym  = (Rxx(+B) + Rxx(-B)) / 2   (kills MR asymmetry artefacts)
#   Rxy_anti = (Rxy(+B) - Rxy(-B)) / 2   (kills Hall offset)
# Both Vxx and Vxy channels are treated the same way.
# =============================================================================

def _auto_symmetrise_step(cfg) -> int:
    """
    Scan save_folder for *_STEP_*K.txt files from this sweep (identified by
    sample_name), load each, symmetrise the ±B data, write a *_sym.txt file.
    Returns the number of files symmetrised.
    """
    import os, glob
    folder = getattr(cfg, 'save_folder', '').strip() or '.'
    sample = getattr(cfg, 'sample_name', 'Sample')
    pattern = os.path.join(folder, f"{sample}_STEP_*.txt")
    files = [f for f in glob.glob(pattern) if not f.endswith('_sym.txt')]

    n_sym = 0
    for fpath in sorted(files):
        try:
            # ── Read the file, skip comment lines ─────────────────────────
            header_lines, data_rows = [], []
            with open(fpath) as f:
                for line in f:
                    if line.startswith('#'):
                        header_lines.append(line)
                    elif line.strip():
                        parts = line.strip().split('\t')
                        try:
                            data_rows.append([float(p) for p in parts])
                        except ValueError:
                            header_lines.append(line)  # treat as header

            if len(data_rows) < 4:
                continue   # not enough data for symmetrisation

            # Expected columns: B, Vxx, Vxy, Rxx, Rxy, mu, ns, timestamp
            data = np.array(data_rows)
            B_col = data[:, 0]

            # Build a dict of |B| → list of row indices
            from collections import defaultdict
            pairs = defaultdict(list)
            for i, b in enumerate(B_col):
                key = round(abs(b), 6)
                pairs[key].append(i)

            # Only keep |B| values that have both + and − measurements
            sym_rows = []
            for absB, idxs in sorted(pairs.items()):
                pos = [i for i in idxs if B_col[i] >= 0]
                neg = [i for i in idxs if B_col[i] <  0]
                if not pos or not neg:
                    continue
                # Take the last measurement for each polarity (most settled)
                rp = data[pos[-1]]
                rn = data[neg[-1]]
                # Symmetrised row: use +B as reference axis, columns:
                # B(+), Vxx_sym, Vxy_anti, Rxx_sym, Rxy_anti, mu_sym, ns_sym, ts_avg
                row = [
                    rp[0],                          # B (+)
                    (rp[1] + rn[1]) / 2,           # Vxx sym
                    (rp[2] - rn[2]) / 2,           # Vxy antisym
                    (rp[3] + rn[3]) / 2,           # Rxx sym
                    (rp[4] - rn[4]) / 2,           # Rxy antisym
                    (rp[5] + rn[5]) / 2 if data.shape[1] > 5 else float('nan'),  # mu sym
                    (rp[6] + rn[6]) / 2 if data.shape[1] > 6 else float('nan'),  # ns sym
                    (rp[7] + rn[7]) / 2 if data.shape[1] > 7 else float('nan'),  # ts avg
                ]
                sym_rows.append(row)

            if len(sym_rows) < 2:
                continue

            # ── Write sym file ─────────────────────────────────────────────
            sym_path = fpath.replace('.txt', '_sym.txt')
            with open(sym_path, 'w', encoding='utf-8') as f:
                for h in header_lines:
                    f.write(h)
                f.write(f"# Symmetrised: Rxx_sym=(R(+B)+R(-B))/2, Rxy_anti=(R(+B)-R(-B))/2\n")
                f.write(f"# Source: {os.path.basename(fpath)}  |  {len(sym_rows)} ±B pairs\n")
                f.write("# B(T)\tVxx_sym(V)\tVxy_anti(V)\tRxx_sym(Ohm)\tRxy_anti(Ohm)\t"
                        "Mobility(cm2/Vs)\tCarrierDensity(cm-2)\ttimestamp(s)\n")
                for row in sym_rows:
                    f.write('\t'.join(
                        'nan' if (isinstance(v, float) and np.isnan(v)) else f"{v:.9g}"
                        for v in row) + '\n')

            logger.info(f"Auto-symmetrised: {os.path.basename(sym_path)}  ({len(sym_rows)} pairs)")
            n_sym += 1

        except Exception as e:
            logger.warning(f"Symmetrise {fpath}: {e}")

    return n_sym


def _auto_symmetrise_hysteresis(cfg) -> int:
    """
    Scan save_folder for *_HYSTERESIS_*K.txt files from this sweep, load each,
    symmetrise the ±B data, write a *_sym.txt file.

    HYSTERESIS files contain ±B paired data by construction (the loop visits
    both polarities). The file format is identical to STEP, so this wrapper
    just runs the same algorithm against the HYSTERESIS naming pattern.
    """
    import os, glob
    folder = getattr(cfg, 'save_folder', '').strip() or '.'
    sample = getattr(cfg, 'sample_name', 'Sample')
    pattern = os.path.join(folder, f"{sample}_HYSTERESIS_*.txt")
    files = [f for f in glob.glob(pattern) if not f.endswith('_sym.txt')]

    n_sym = 0
    for fpath in sorted(files):
        try:
            # Reuse _auto_symmetrise_step's per-file logic by temporarily
            # spoofing the cfg.sample_name pattern. Simpler: reimplement the
            # core inline (identical to _auto_symmetrise_step).
            header_lines, data_rows = [], []
            with open(fpath) as f:
                for line in f:
                    if line.startswith('#'):
                        header_lines.append(line)
                    elif line.strip():
                        parts = line.strip().split('\t')
                        try:
                            data_rows.append([float(p) for p in parts])
                        except ValueError:
                            header_lines.append(line)

            if len(data_rows) < 4:
                continue

            data = np.array(data_rows)
            B_col = data[:, 0]

            from collections import defaultdict
            pairs = defaultdict(list)
            for i, b in enumerate(B_col):
                key = round(abs(b), 6)
                pairs[key].append(i)

            sym_rows = []
            for absB, idxs in sorted(pairs.items()):
                pos = [i for i in idxs if B_col[i] >= 0]
                neg = [i for i in idxs if B_col[i] <  0]
                if not pos or not neg:
                    continue
                rp = data[pos[-1]]
                rn = data[neg[-1]]
                row = [
                    rp[0],                          # B (+)
                    (rp[1] + rn[1]) / 2,           # Vxx sym
                    (rp[2] - rn[2]) / 2,           # Vxy antisym
                    (rp[3] + rn[3]) / 2,           # Rxx sym
                    (rp[4] - rn[4]) / 2,           # Rxy antisym
                ]
                # Pass through remaining columns (mobility, ns, timestamp, Vg) as averages
                for c in range(5, data.shape[1]):
                    try:
                        row.append((rp[c] + rn[c]) / 2 if not (np.isnan(rp[c]) or np.isnan(rn[c])) else float('nan'))
                    except Exception:
                        row.append(float('nan'))
                sym_rows.append(row)

            if not sym_rows:
                continue

            sym_path = fpath.replace('.txt', '_sym.txt')
            with open(sym_path, 'w', encoding='utf-8') as fout:
                for h in header_lines:
                    fout.write(h)
                fout.write("# Symmetrised: Vxx_sym=(V(+B)+V(-B))/2, Vxy_anti=(V(+B)-V(-B))/2\n")
                fout.write("# B(T)\tVxx_sym(V)\tVxy_anti(V)\tRxx_sym(Ohm)\tRxy_anti(Ohm)\tMobility\tCarrierDensity\ttimestamp(s)\tVgate(V)\n")
                for row in sym_rows:
                    fout.write("\t".join(f"{v:.9g}" if isinstance(v, (int, float)) else str(v) for v in row) + "\n")
            n_sym += 1
        except Exception as e:
            logger.warning(f"Symmetrise {fpath}: {e}")

    return n_sym


def _auto_symmetrise_angle(cfg) -> int:
    """Symmetrise *_ANGLE_HYST_*.txt files. Each file contains a closed B
    loop along a single (θ,φ) direction, so the standard ±B symmetrisation
    works unchanged — only the glob pattern differs from HYSTERESIS.
    """
    import os, glob
    folder = getattr(cfg, 'save_folder', '').strip() or '.'
    sample = getattr(cfg, 'sample_name', 'Sample')
    pattern = os.path.join(folder, f"{sample}_ANGLE_HYST_*.txt")
    files = [f for f in glob.glob(pattern) if not f.endswith('_sym.txt')]

    n_sym = 0
    for fpath in sorted(files):
        try:
            header_lines, data_rows = [], []
            with open(fpath) as f:
                for line in f:
                    if line.startswith('#'):
                        header_lines.append(line)
                    elif line.strip():
                        parts = line.strip().split('\t')
                        try:
                            data_rows.append([float(p) for p in parts])
                        except ValueError:
                            header_lines.append(line)

            if len(data_rows) < 4:
                continue

            data = np.array(data_rows)
            B_col = data[:, 0]

            from collections import defaultdict
            pairs = defaultdict(list)
            for i, b in enumerate(B_col):
                key = round(abs(b), 6)
                pairs[key].append(i)

            sym_rows = []
            for absB, idxs in sorted(pairs.items()):
                pos = [i for i in idxs if B_col[i] >= 0]
                neg = [i for i in idxs if B_col[i] <  0]
                if not pos or not neg:
                    continue
                rp = data[pos[-1]]
                rn = data[neg[-1]]
                row = [
                    rp[0],                          # B (+)
                    (rp[1] + rn[1]) / 2,            # Vxx sym
                    (rp[2] - rn[2]) / 2,            # Vxy antisym
                    (rp[3] + rn[3]) / 2,            # Rxx sym
                    (rp[4] - rn[4]) / 2,            # Rxy antisym
                ]
                for c in range(5, data.shape[1]):
                    try:
                        row.append((rp[c] + rn[c]) / 2 if not (np.isnan(rp[c]) or np.isnan(rn[c])) else float('nan'))
                    except Exception:
                        row.append(float('nan'))
                sym_rows.append(row)

            if not sym_rows:
                continue

            sym_path = fpath.replace('.txt', '_sym.txt')
            with open(sym_path, 'w', encoding='utf-8') as fout:
                for h in header_lines:
                    fout.write(h)
                fout.write("# Symmetrised: Vxx_sym=(V(+B)+V(-B))/2, Vxy_anti=(V(+B)-V(-B))/2 (along (θ,φ))\n")
                fout.write("# B(T)\tVxx_sym(V)\tVxy_anti(V)\tRxx_sym(Ohm)\tRxy_anti(Ohm)\tMobility\tCarrierDensity\ttimestamp(s)\tVgate(V)\n")
                for row in sym_rows:
                    fout.write("\t".join(f"{v:.9g}" if isinstance(v, (int, float)) else str(v) for v in row) + "\n")
            n_sym += 1
        except Exception as e:
            logger.warning(f"Symmetrise {fpath}: {e}")

    return n_sym


# ── API routes ────────────────────────────────────────────────────────────────
def run_sweep(config: SweepConfig):
    global sweep_thread, _last_itc_cfg, _last_ips_cfg
    # Cache cryostat connection params for idle-poll use
    _last_itc_cfg = {'ip': config.itc_ip, 'port': config.itc_port,
                     'device': config.temp_device}
    _last_ips_cfg = {'ip': config.ips_ip, 'port': config.ips_port,
                     'group': config.field_group}
    stop_event.clear()
    pause_event.clear()
    with _sse_replay_lock:
        _sse_replay_cache.clear()
    engine = SweepEngine(config, stop_event, pause_event)
    sweep_thread = _threading.current_thread()
    engine.run()
    with lock:
        sweep_thread = None  # type: ignore


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """Serve the embedded frontend HTML with role injected."""
    role = request.session.get('role', 'monitor')
    html = _get_html()
    # Inject role as a JS global before </head>
    inject = f'<script>window.QTMS_ROLE="{role}";</script>'
    html = html.replace('</head>', inject + '</head>', 1)
    return HTMLResponse(content=html)


@app.get("/analysis", response_class=HTMLResponse)
def analysis_page():
    """Serve the dedicated analysis window (SdH fit, relaxation, 2D map, Tc scan)."""
    import zlib as _zlib, base64 as _b64
    b = ''.join(_ANALYSIS_B64.split()).replace('"', '')
    html = _zlib.decompress(_b64.b64decode(b)).decode()
    return HTMLResponse(content=html)


@app.get("/api/ping")
async def api_ping():
    """No-auth connectivity test — returns 200 + JSON from any device on the network.
    Mobile users: open http://<lab-pc-ip>:8000/api/ping in the phone browser.
    If you see {"status":"ok"} the network path works; if it times out or refuses,
    the firewall or routing is the problem (not the app).
    """
    import socket
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if not ip.startswith("127.") and ":" not in ip and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return {"status": "ok", "server_ips": ips, "port": 8000,
            "tip": "If you can see this, the network path is open. Now go to http://<this-ip>:8000 and log in."}


@app.get("/api/state")
def get_state():
    with lock:
        return {"phase": "RUNNING" if (sweep_thread and sweep_thread.is_alive()) else "IDLE"}


@app.post("/api/iv_read_bt")
async def iv_read_bt(request: Request):
    """Read current T and B from the cryostat for the IV active-mode
    confirmation modal. The frontend calls this just before showing the
    "Confirm and proceed" dialog so the user can compare their requested
    B and T setpoints with the current actual values.

    POST body: {itc_ip, itc_port, ips_ip, ips_port, temp_device, field_group}
    Returns: {T_K: float|null, B_T: float|null, errors: [str]}
    """
    if sweep_thread and sweep_thread.is_alive():
        raise HTTPException(400, "A sweep is currently running")
    body = await request.json()
    itc_ip   = body.get('itc_ip',   '192.168.123.101')
    itc_port = int(body.get('itc_port', 7020))
    ips_ip   = body.get('ips_ip',   '192.168.123.102')
    ips_port = int(body.get('ips_port', 7020))
    temp_dev = body.get('temp_device', 'DB8.T1')
    field_grp = body.get('field_group', 'GRPZ')
    errors = []
    T_val = B_val = None
    try:
        itc = MercuryITC(itc_ip, port=itc_port, timeout_s=2.0)
        itc.open()
        T_val = float(itc.read_temperature(temp_dev))
        itc.close()
        if T_val is not None and T_val <= 0:
            T_val = None
            errors.append("iTC returned T <= 0 (sensor likely disconnected)")
    except Exception as e:
        errors.append(f"iTC: {e}")
    try:
        ips = MercuryIPS(ips_ip, port=ips_port, group=field_grp)
        ips.open()
        b, ok = ips.read_field(field_grp)
        ips.close()
        if ok:
            B_val = float(b)
        else:
            errors.append("IPS returned no valid field reading")
    except Exception as e:
        errors.append(f"IPS: {e}")
    return {"T_K": T_val, "B_T": B_val, "errors": errors}


@app.post("/api/start")
def start_sweep(config: SweepConfigModel):
    global current_config, sweep_thread
    if sweep_thread and sweep_thread.is_alive():
        raise HTTPException(400, "Sweep already running")
    cfg = SweepConfig(**config.dict())

    # ── DEFENCE 1: log received config at INFO so the backend has an audit
    # trail of which target values were sent for each sweep. If the magnet
    # later runs to the wrong B, this line is the first place to look.
    try:
        m = cfg.mode
        if m == 'RELAX':
            logger.info(
                "/api/start RELAX  T_start=%.4f K  relax_B_step=%.4f T  "
                "duration=%.0f s  interval=%.2f s  sample=%s",
                float(cfg.T_start), float(cfg.relax_B_step),
                float(cfg.relax_duration_s), float(cfg.relax_interval_s),
                cfg.sample_name)
        elif m == 'RELAX_SCAN':
            B_list = (cfg.relaxscan_B_list or '').strip()
            B_preview = B_list[:80] + ('...' if len(B_list) > 80 else '')
            logger.info(
                "/api/start RELAX_SCAN  T_start=%.4f K  B_list=[%s]  "
                "duration=%.0f s  interval=%.2f s  sample=%s",
                float(cfg.T_start), B_preview,
                float(cfg.relaxscan_duration_s), float(cfg.relaxscan_interval_s),
                cfg.sample_name)
        elif m == 'TCSCAN':
            logger.info(
                "/api/start TCSCAN  B_fixed=%.4f T  T: %.3f→%.3f K  dT=%.3f K  "
                "wait=%.1f s  sample=%s",
                float(cfg.tcscan_B_fixed), float(cfg.tcscan_T_start),
                float(cfg.tcscan_T_end), float(cfg.tcscan_dT),
                float(cfg.tcscan_wait_s), cfg.sample_name)
        else:  # STEP-family, RAMP
            logger.info(
                "/api/start %s  T: %.3f→%.3f K  B_max=%.3f T  B_step=%.4f T  sample=%s",
                m, float(cfg.T_start), float(cfg.T_end),
                float(cfg.B_max), float(cfg.B_step), cfg.sample_name)
    except Exception as _log_err:
        logger.warning(f"/api/start: could not format config log line: {_log_err}")

    with lock:
        current_config = cfg
    t = _threading.Thread(target=run_sweep, args=(cfg,), daemon=True)
    t.start()
    return {"status": "started"}


@app.post("/api/stop")
def stop_sweep():
    global _next_conditions
    pause_event.clear()   # always clear pause when stopping
    stop_event.set()
    with lock:
        _next_conditions = None   # manual stop → always do full shutdown
    return {"status": "stopping"}


@app.post("/api/queue_transition")
async def queue_transition(request: Request):
    """Tell the backend what T/B conditions the *next* queued sweep needs.

    Call this before the current sweep ends.  _safe_shutdown will then
    drive T and B to those values instead of ramping all the way to base
    (0 T, 1.5 K), saving time and cryogen between back-to-back sweeps.

    POST body:  {"T_start": float, "B_start": float}
    POST body:  {} or {"T_start": null}  →  clear, force full shutdown
    """
    global _next_conditions
    body = await request.json()
    T = body.get("T_start")
    B = body.get("B_start")
    with lock:
        if T is None or B is None:
            _next_conditions = None
        else:
            _next_conditions = {"T_start": float(T), "B_start": float(B)}
    return {"status": "ok", "next_conditions": _next_conditions}


@app.post("/api/contact_check")
async def contact_check(request: Request):
    """Perform a quick 4-probe resistance check without starting a full sweep.

    Connects to the SMU and NVMs (or MFLI if source_mode != DC), applies the
    configured current for one measurement, returns Rxx and Rxy with a
    pass/warn/fail verdict.

    POST body: same fields as SweepConfigModel (subset used: smu_resource,
               channel, com_port_1/2, I_const, nplc, nvm_range,
               source_mode, mfli_* fields).

    Returns: {ok, warning, message, Rxx_Ohm, Rxy_Ohm}
    """
    body = await request.json()
    # Treat as a SweepConfigModel with defaults for unused fields
    try:
        from copy import deepcopy
        defaults = SweepConfigModel().dict()
        defaults.update({k: v for k, v in body.items() if k in defaults})
        cfg = SweepConfig(**defaults)
    except Exception as e:
        raise HTTPException(400, f"Bad config: {e}")

    Rxx = Rxy = None
    try:
        mode = getattr(cfg, 'source_mode', 'DC')
        if mode in ('MFLI', 'MFLI_SINGLE', 'MFLI_DUAL'):
            if zi is None:
                return {"ok": False, "warning": False,
                        "message": "zhinst not installed — cannot use MFLI for contact check",
                        "Rxx_Ohm": None, "Rxy_Ohm": None}
            mfli = MFLI(
                device_id=cfg.mfli_device_id, host=cfg.mfli_host,
                port=cfg.mfli_port, frequency=cfg.mfli_frequency,
                output_amplitude=cfg.mfli_output_amplitude,
                series_resistance=cfg.mfli_series_resistance,
                time_constant=cfg.mfli_time_constant,
                filter_order=cfg.mfli_filter_order,
                input_range=cfg.mfli_input_range,
                output_range=cfg.mfli_output_range,
                settle_tc=cfg.mfli_settle_tc, role="master", logger=logger)
            mfli.open(); mfli.configure()
            meas = mfli.measure(avg_n=3)
            mfli.output_off(); mfli.close()
        else:
            if pyvisa is None:
                return {"ok": False, "warning": False,
                        "message": "pyvisa not installed — cannot perform DC contact check",
                        "Rxx_Ohm": None, "Rxy_Ohm": None}
            rm   = pyvisa.ResourceManager()
            smu  = rm.open_resource(cfg.smu_resource)
            smu.write_termination = "\n"; smu.read_termination = "\n"
            smu.timeout = 10000
            nvm1 = Serial2182A(cfg.com_port_1)
            nvm2 = Serial2182A(cfg.com_port_2)
            # Minimal NVM config
            for nvm in [nvm1, nvm2]:
                nvm.clear_status()
                nvm.write('SENS:FUNC "VOLT:DC"')
                nvm.write("SENS:VOLT:DC:RANG:AUTO ON")
                nvm.write(f"SENS:VOLT:DC:NPLC {cfg.nplc}")
                nvm.write("SYST:AZER ON")
                nvm.write("INIT:CONT OFF")
            # Quick SMU config
            ch = "smub" if cfg.channel.upper() == "B" else "smua"
            i_range = 1e-3 if abs(cfg.I_const) <= 1e-3 else 1e-2
            smu.write(f"""
{ch}.reset()
{ch}.source.func = {ch}.OUTPUT_DCAMPS
{ch}.source.autorangei = {ch}.AUTORANGE_OFF
{ch}.source.rangei = {i_range}
{ch}.source.limitv = {cfg.v_limit}
{ch}.source.leveli = {cfg.I_const}
{ch}.measure.autorangev = {ch}.AUTORANGE_ON
{ch}.source.output = {ch}.OUTPUT_ON
""")
            import time as _time; _time.sleep(0.3)
            # Single reading
            def _rdv(nvm):
                try:
                    nvm.write("INIT"); _time.sleep(0.1)
                    r = nvm.query("FETC?").strip()
                    vals = [float(x) for x in r.split(",") if x.strip()]
                    return vals[0] if vals else 0.0
                except: return 0.0
            Vxx_raw = _rdv(nvm1); Vxy_raw = _rdv(nvm2)
            # Turn off
            smu.write(f"{ch}.source.output = {ch}.OUTPUT_OFF"); smu.close()
            nvm1.close(); nvm2.close()
            I_eff = cfg.I_const
            meas = {"Rxx": Vxx_raw / I_eff if I_eff else 0,
                    "Rxy": Vxy_raw / I_eff if I_eff else 0,
                    "Vxxp_m": Vxx_raw, "Vxyp_m": Vxy_raw,
                    "Ip_m": I_eff, "I_eff": I_eff}

        Rxx = float(meas.get("Rxx", 0))
        Rxy = float(meas.get("Rxy", 0))

        # Verdict: typical 2DEG contacts should be 100 Ω – 10 kΩ
        if abs(Rxx) < 1:
            return {"ok": False, "warning": False,
                    "message": f"Rxx ≈ {Rxx:.2f} Ω — OPEN or SHORT circuit",
                    "Rxx_Ohm": Rxx, "Rxy_Ohm": Rxy}
        elif abs(Rxx) > 1e6:
            return {"ok": False, "warning": False,
                    "message": f"Rxx ≈ {Rxx:.2e} Ω — contact likely broken",
                    "Rxx_Ohm": Rxx, "Rxy_Ohm": Rxy}
        elif abs(Rxx) > 50e3:
            return {"ok": True, "warning": True,
                    "message": f"Rxx = {Rxx:.0f} Ω — high but may be OK (check bonding)",
                    "Rxx_Ohm": Rxx, "Rxy_Ohm": Rxy}
        else:
            return {"ok": True, "warning": False,
                    "message": f"Rxx = {Rxx:.0f} Ω, Rxy = {Rxy:.0f} Ω — contacts OK",
                    "Rxx_Ohm": Rxx, "Rxy_Ohm": Rxy}

    except Exception as e:
        logger.error(f"Contact check error: {e}")
        return {"ok": False, "warning": False,
                "message": f"Instrument error: {e}",
                "Rxx_Ohm": Rxx, "Rxy_Ohm": Rxy}


@app.post("/api/mfli_diagnose")
async def mfli_diagnose(request: Request):
    """One-shot MFLI connection check, NO sweep. Connects to LabOne data
    server, reads version + device tree, returns a structured diagnostic
    report. Intended for confirming master/slave wiring before committing
    to a sweep.

    POST body: same MFLI fields as SweepConfigModel.
    Returns: {ok, message, details: {labone_version, api_level, master_status,
              slave_status, clock_lock, ...}}
    """
    body = await request.json()
    host = body.get('mfli_host', '192.168.123.108')
    port = int(body.get('mfli_port', 8004))
    master_id = body.get('mfli_device_id', 'DEV6568')
    slave_id  = body.get('mfli_slave_device_id', '')
    test_dual = bool(slave_id) and body.get('source_mode', 'DC') == 'MFLI_DUAL'

    details = {
        'host': host, 'port': port,
        'master_id': master_id, 'slave_id': slave_id if test_dual else None,
        'labone_version': None, 'labone_revision': None, 'api_level': None,
        'master_connected': False, 'slave_connected': False,
        'master_iface': None, 'slave_iface': None,
        'slave_clock_locked': None,
        'errors': [],
    }

    if zi is None:
        return {"ok": False,
                "message": "zhinst not installed on the measurement PC. Install with: pip install zhinst",
                "details": details}

    daq = None
    last_err = None
    for api_level in (6, 5, 4, 1):
        try:
            daq = zi.ziDAQServer(host, port, api_level)
            details['api_level'] = api_level
            break
        except Exception as e:
            last_err = e
            daq = None
    if daq is None:
        return {"ok": False,
                "message": (f"Cannot reach LabOne data server at {host}:{port} "
                            f"on any API level. Last error: {last_err}. "
                            f"Verify LabOne is running and the data-server port matches."),
                "details": details}

    try:
        details['labone_version']  = daq.getString('/zi/about/version')
        details['labone_revision'] = daq.getString('/zi/about/revision')
    except Exception as e:
        details['errors'].append(f"version-read: {e}")

    # ── Master ──
    for iface in ('PCIe', '1GbE', 'USB'):
        try:
            daq.connectDevice(master_id, iface)
            details['master_connected'] = True
            details['master_iface']     = iface
            break
        except Exception as e:
            last_err = e
    if not details['master_connected']:
        details['errors'].append(f"master ({master_id}) connectDevice failed: {last_err}")

    # ── Slave (if requested) ──
    if test_dual and details['master_connected']:
        for iface in ('PCIe', '1GbE', 'USB'):
            try:
                daq.connectDevice(slave_id, iface)
                details['slave_connected'] = True
                details['slave_iface']     = iface
                break
            except Exception as e:
                last_err = e
        if not details['slave_connected']:
            details['errors'].append(f"slave ({slave_id}) connectDevice failed: {last_err}")
        else:
            # Try to set extclk and verify
            try:
                d = slave_id.lower()
                daq.setInt(f'/{d}/system/extclk', 1)
                time.sleep(0.5)
                val = daq.getInt(f'/{d}/system/extclk')
                details['slave_clock_locked'] = (val == 1)
            except Exception as e:
                details['errors'].append(f"slave clock check: {e}")

    # Close
    try: daq.disconnect()
    except: pass

    # Build verdict
    if details['master_connected'] and (not test_dual or
            (details['slave_connected'] and details['slave_clock_locked'])):
        ok = True
        msg = (f"MFLI diagnostic PASSED. LabOne v{details['labone_version']} "
               f"(API level {details['api_level']}). Master {master_id} "
               f"connected via {details['master_iface']}.")
        if test_dual:
            msg += (f" Slave {slave_id} connected via {details['slave_iface']}, "
                    f"locked to master 10 MHz.")
    else:
        ok = False
        msg = "MFLI diagnostic FAILED — see details and errors."
    return {"ok": ok, "message": msg, "details": details}


@app.post("/api/pause")
def pause_sweep():
    pause_event.set()
    return {"status": "paused"}


@app.post("/api/resume")
def resume_sweep():
    pause_event.clear()
    return {"status": "resumed"}


@app.post("/api/emergency")
def emergency_stop():
    return stop_sweep()


# =============================================================================
# WARM / COOL  –  ramp probe + VTI to 300 K or 1.5 K with B=0, I=0
# =============================================================================
_warmcool_thread: Optional[_threading.Thread] = None
_warmcool_stop = _threading.Event()

def _warmcool_worker(body: dict):
    """Background thread: safely warm up or cool down the entire cryostat."""
    action    = body.get("action", "cool")          # "warm" | "cool"
    ramp_rate = float(body.get("ramp_rate", 5.0))   # K/min
    T_target  = 300.0 if action == "warm" else 1.5
    label     = f"WARM → {T_target:.0f} K" if action == "warm" else f"COOL → {T_target:.1f} K"

    # Instrument connection details
    itc_ip   = body.get("itc_ip",   "192.168.123.101")
    itc_port = int(body.get("itc_port", 7020))
    ips_ip   = body.get("ips_ip",   "192.168.123.102")
    ips_port = int(body.get("ips_port", 7020))
    temp_dev = body.get("temp_device", "DB8.T1")
    vti_dev  = body.get("vti_device",  "MB1.T1")
    vti_off  = float(body.get("vti_offset", 1.0))
    vti_track = body.get("vti_tracking", True)
    fld_grp  = body.get("field_group", "GRPZ")
    smu_res  = body.get("smu_resource", "")
    channel  = body.get("channel", "B")
    src_mode = body.get("source_mode", "DC")
    mfli_host = body.get("mfli_host", "")
    mfli_port = int(body.get("mfli_port", 8004))
    mfli_dev  = body.get("mfli_device_id", "DEV6568")

    itc = ips = None
    try:
        _sse_broadcast(LiveData(phase=f"{label}: connecting instruments"))

        # ── 0. Connect ITC + IPS ──────────────────────────────────────────
        itc = MercuryITC(itc_ip, port=itc_port, timeout_s=3.0)
        itc.open()
        ips = MercuryIPS(ips_ip, port=ips_port, group=fld_grp)
        ips.open()

        # ── 1. Ensure I = 0  (turn off excitation source) ────────────────
        _sse_broadcast(LiveData(phase=f"{label}: setting I → 0 A"))
        if src_mode in ('MFLI', 'MFLI_SINGLE', 'MFLI_DUAL'):
            try:
                if zi is not None and mfli_host:
                    mfli = MFLI(device_id=mfli_dev, host=mfli_host,
                                port=mfli_port, role="master")
                    mfli.open()
                    mfli.output_off()
                    mfli.close()
            except Exception as e:
                logger.warning(f"{label}: MFLI off error: {e}")
        else:
            try:
                if pyvisa is not None and smu_res:
                    rm = pyvisa.ResourceManager()
                    smu = rm.open_resource(smu_res)
                    smu.write_termination = "\n"
                    smu.read_termination = "\n"
                    smu.timeout = 5000
                    ch = "smua" if channel.upper() == "A" else "smub"
                    smu.write(f"{ch}.source.leveli = 0")
                    smu.write(f"{ch}.source.output = {ch}.OUTPUT_OFF")
                    smu.close()
            except Exception as e:
                logger.warning(f"{label}: SMU off error: {e}")

        # ── 2. Ramp B → 0 T ──────────────────────────────────────────────
        B_now, _ = ips.read_field(fld_grp)
        if abs(B_now) > 0.002:
            _sse_broadcast(LiveData(phase=f"{label}: ramping B → 0 T  (now {B_now:.4f} T)"))
            try:
                ips.set_switch_heater(True, fld_grp); time.sleep(3)
                ips.set_ramp_rate_field(0.2, fld_grp); time.sleep(0.5)
                ips.set_target_field(0.0, fld_grp); time.sleep(0.5)
                ips.set_to_setpoint(fld_grp)
                deadline = time.time() + 600  # 10 min max
                while time.time() < deadline:
                    if _warmcool_stop.is_set():
                        ips.set_hold(fld_grp)
                        _sse_broadcast(LiveData(phase=f"{label}: STOPPED by user"))
                        return
                    B_now, _ = ips.read_field(fld_grp)
                    _sse_broadcast(LiveData(
                        phase=f"{label}: B = {B_now:.4f} T → 0 T",
                        B_T=B_now))
                    if abs(B_now) <= 0.002:
                        break
                    time.sleep(2.0)
                ips.set_hold(fld_grp)
            except Exception as e:
                logger.warning(f"{label}: field ramp error: {e}")
        else:
            _sse_broadcast(LiveData(phase=f"{label}: B already at zero"))

        # ── 3. Ramp T (probe + VTI) → target ─────────────────────────────
        T_now = itc.read_temperature(temp_dev)
        _sse_broadcast(LiveData(
            phase=f"{label}: ramping T  {T_now:.1f} → {T_target:.0f} K  "
                  f"at {ramp_rate:.1f} K/min"))

        # Probe
        itc.set_ramp_rate(ramp_rate, temp_dev)
        itc.set_ramp_mode(True, temp_dev)
        itc.set_control_mode("AUTO", temp_dev)
        itc.set_temperature_setpoint(T_target, temp_dev)

        # VTI
        if vti_track:
            vti_sp = max(1.5, T_target - vti_off)
            try:
                itc.set_ramp_rate(ramp_rate, vti_dev)
                itc.set_ramp_mode(True, vti_dev)
                itc.set_control_mode("AUTO", vti_dev)
                itc.set_temperature_setpoint(vti_sp, vti_dev)
                logger.info(f"{label}: VTI {vti_dev} → {vti_sp:.1f} K")
            except Exception as e:
                logger.warning(f"{label}: VTI set error: {e}")

        # ── 4. Wait for T to reach target ─────────────────────────────────
        warming = T_target > T_now
        deadline = time.time() + 7200  # 2 hr max
        while time.time() < deadline:
            if _warmcool_stop.is_set():
                # Freeze at current T on abort
                T_cur = itc.read_temperature(temp_dev)
                if T_cur and T_cur > 0:
                    itc.set_ramp_mode(False, temp_dev)
                    itc.set_temperature_setpoint(T_cur, temp_dev)
                    if vti_track:
                        try:
                            itc.set_ramp_mode(False, vti_dev)
                            itc.set_temperature_setpoint(max(1.5, T_cur - vti_off), vti_dev)
                        except Exception:
                            pass
                _sse_broadcast(LiveData(phase=f"{label}: STOPPED at {T_cur:.1f} K"))
                return
            T_now = itc.read_temperature(temp_dev)
            if T_now and T_now > 0:
                _sse_broadcast(LiveData(
                    phase=f"{label}: T = {T_now:.1f} K → {T_target:.0f} K",
                    T_K=T_now))
                if warming and T_now >= T_target - 1.0:
                    break
                if not warming and T_now <= T_target + 0.2:
                    break
            time.sleep(5.0)

        _sse_broadcast(LiveData(
            phase=f"{label}: COMPLETE  (T ≈ {T_now:.1f} K)",
            T_K=T_now))

    except Exception as e:
        logger.error(f"{label} error: {e}")
        _sse_broadcast(LiveData(phase=f"{label}: ERROR — {e}"))
    finally:
        if itc:
            try: itc.close()
            except: pass
        if ips:
            try: ips.close()
            except: pass


@app.post("/api/warmcool")
async def warmcool(request: Request):
    global _warmcool_thread
    # Block if a sweep is running
    if sweep_thread and sweep_thread.is_alive():
        raise HTTPException(400, "Cannot warm/cool while a sweep is running")
    if _warmcool_thread and _warmcool_thread.is_alive():
        raise HTTPException(400, "Warm/cool already in progress — stop it first")
    body = await request.json()
    action = body.get("action")
    if action not in ("warm", "cool"):
        raise HTTPException(400, "action must be 'warm' or 'cool'")
    _warmcool_stop.clear()
    _warmcool_thread = _threading.Thread(
        target=_warmcool_worker, args=(body,), daemon=True)
    _warmcool_thread.start()
    target = "300 K" if action == "warm" else "1.5 K"
    return {"status": "started", "target": target}


@app.post("/api/warmcool_stop")
def warmcool_stop():
    _warmcool_stop.set()
    return {"status": "stopping"}



# =============================================================================
# AUTH ROUTES  –  login / logout / role / upgrade
# =============================================================================
_LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QTMS — Login</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0a0f1a;font-family:'Segoe UI',Arial,sans-serif;
       display:flex;align-items:center;justify-content:center;min-height:100vh;
       color:#c8d6e8}
  .card{background:#0e1625;border:1px solid #1e2d45;border-radius:12px;
        padding:2.5rem 2rem;width:360px;box-shadow:0 8px 40px rgba(0,0,0,.6)}
  .logo{font-size:2rem;font-weight:800;letter-spacing:4px;color:#00d4ff;
        text-align:center;margin-bottom:.25rem}
  .subtitle{font-size:.72rem;color:#4a6080;text-align:center;
            letter-spacing:1px;margin-bottom:2rem}
  label{display:block;font-size:.72rem;color:#7a9ab8;margin-bottom:.35rem;
        letter-spacing:.5px;text-transform:uppercase}
  input[type=password]{width:100%;background:#0a0f1a;border:1px solid #1e2d45;
    border-radius:6px;padding:.6rem .75rem;color:#c8d6e8;font-size:.9rem;outline:none}
  input[type=password]:focus{border-color:#00d4ff}
  .submit{width:100%;margin-top:1.25rem;padding:.7rem;background:#00d4ff;
          border:none;border-radius:6px;color:#0a0f1a;font-weight:700;
          font-size:.95rem;letter-spacing:1px;cursor:pointer}
  .submit:hover{background:#33deff}
  .error{margin-top:.75rem;padding:.5rem .75rem;background:rgba(255,80,80,.1);
         border:1px solid rgba(255,80,80,.4);border-radius:5px;
         color:#ff6060;font-size:.78rem;text-align:center}
  .hint{margin-top:1.25rem;font-size:.68rem;color:#3a5070;text-align:center;
        line-height:1.6}
  .roles{display:flex;gap:.5rem;margin-top:1rem}
  .role-chip{flex:1;padding:.3rem;border-radius:5px;text-align:center;
             font-size:.68rem;letter-spacing:.5px}
  .role-monitor{background:rgba(0,212,255,.07);border:1px solid rgba(0,212,255,.3);
                color:#00d4ff}
  .role-control{background:rgba(179,136,255,.07);border:1px solid rgba(179,136,255,.3);
                color:#b388ff}
</style>
</head>
<body>
<div class="card">
  <div class="logo">QTMS</div>
  <div class="subtitle">QUANTUM TRANSPORT MEASUREMENT SYSTEM</div>
  <form method="POST" action="/login">
    <div>
      <label>Access Password</label>
      <input type="password" name="password" autofocus
             placeholder="Enter monitor or control password">
    </div>
    {ERROR}
    <button class="submit" type="submit">Access System</button>
  </form>
  <div class="roles">
    <div class="role-chip role-monitor">Monitor — read only</div>
    <div class="role-chip role-control">Control — full access</div>
  </div>
  <div class="hint">
    Enter your monitor password for read-only access to plots and status.<br>
    Enter your control password to start/stop sweeps and manage the queue.
  </div>
</div>
</body>
</html>"""

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(_LOGIN_HTML.replace("{ERROR}", ""))

@app.post("/login")
async def login_post(request: Request):
    form = await request.form()
    password = form.get("password", "")
    if _check_password(password, "control"):
        request.session["role"] = "control"
        return RedirectResponse("/", status_code=303)
    if _check_password(password, "monitor"):
        request.session["role"] = "monitor"
        return RedirectResponse("/", status_code=303)
    error = '<div class="error">Incorrect password. Try again.</div>'
    return HTMLResponse(_LOGIN_HTML.replace("{ERROR}", error), status_code=401)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

@app.get("/api/role")
async def get_role(request: Request):
    return {"role": request.session.get("role", "none")}

@app.post("/api/auth/upgrade")
async def upgrade_role(request: Request):
    """Upgrade a monitor session to control without a page reload."""
    body = await request.json()
    password = body.get("password", "")
    if _check_password(password, "control"):
        request.session["role"] = "control"
        return {"role": "control"}
    raise HTTPException(status_code=403, detail="Incorrect control password")


# =============================================================================
# SAMPLE LOG  –  append one row per sweep to sample_log.csv
# =============================================================================

_LOG_FILE    = Path(__file__).parent / "sample_log.csv"
_LOG_COLUMNS = [
    "log_id", "timestamp_start", "sample_id", "mode", "source_mode",
    "T_start_K", "T_end_K", "T_step_K",
    "B_start_T", "B_end_T", "B_step_T",
    "I_A", "freq_Hz", "save_folder",
    "status", "duration_s", "n_points", "notes",
]

def _ensure_log_header():
    if not _LOG_FILE.exists():
        _LOG_FILE.write_text("\t".join(_LOG_COLUMNS) + "\n")

def _next_log_id() -> int:
    if not _LOG_FILE.exists():
        return 1
    lines = [l for l in _LOG_FILE.read_text().splitlines() if l.strip()]
    return max(1, len(lines))   # header counts as line 1, so first data row = 2 → id=1

def _append_sample_log(cfg, status: str,
                        duration_s: float = 0.0,
                        n_points: int = 0,
                        notes: str = "") -> int:
    """
    Write one row to sample_log.csv.
    Returns the log_id so it can be used to UPDATE the row later.
    Thread-safe: uses a file-lock via a .lock sentinel file.
    """
    _ensure_log_header()
    log_id = _next_log_id()

    # Derive current from config
    mode = getattr(cfg, "source_mode", "DC")
    if mode in ("MFLI", "MFLI_SINGLE", "MFLI_DUAL"):
        I_A   = getattr(cfg, "mfli_output_amplitude", 0) / max(
                    getattr(cfg, "mfli_series_resistance", 1), 1)
        freq  = getattr(cfg, "mfli_frequency", 0)
    else:
        I_A   = getattr(cfg, "I_const", 0)
        freq  = 0.0

    row = {
        "log_id"          : log_id,
        "timestamp_start" : datetime.now().isoformat(timespec="seconds"),
        "sample_id"       : getattr(cfg, "sample_name", ""),
        "mode"            : getattr(cfg, "mode", ""),
        "source_mode"     : mode,
        "T_start_K"       : getattr(cfg, "T_start", ""),
        "T_end_K"         : getattr(cfg, "T_end",   ""),
        "T_step_K"        : getattr(cfg, "T_step",  ""),
        "B_start_T"       : getattr(cfg, "B_start", ""),
        "B_end_T"         : getattr(cfg, "B_end",   ""),
        "B_step_T"        : getattr(cfg, "B_step",  ""),
        "I_A"             : f"{I_A:.3e}",
        "freq_Hz"         : freq,
        "save_folder"     : getattr(cfg, "save_folder", ""),
        "status"          : status,
        "duration_s"      : round(duration_s, 1),
        "n_points"        : n_points,
        "notes"           : notes.replace("\t", " ").replace("\n", " ") if notes else "",
    }
    line = "\t".join(str(row[c]) for c in _LOG_COLUMNS) + "\n"
    with open(_LOG_FILE, "a") as f:
        f.write(line)
    logger.info(f"Sample log: {status} → row {log_id}  ({row['sample_id']})")
    return log_id


def _update_sample_log(log_id: int, status: str,
                        duration_s: float, n_points: int):
    """
    Rewrite the row with the given log_id to update status/duration/n_points.
    Reads the whole file, modifies the row in-place, writes back.
    """
    if not _LOG_FILE.exists():
        return
    try:
        lines = _LOG_FILE.read_text().splitlines(keepends=True)
        for i, line in enumerate(lines):
            if i == 0:
                continue   # header
            parts = line.rstrip("\n").split("\t")
            if parts and parts[0] == str(log_id):
                # Find column indices
                cols = lines[0].rstrip("\n").split("\t")
                d    = dict(zip(cols, parts))
                d["status"]     = status
                d["duration_s"] = round(duration_s, 1)
                d["n_points"]   = n_points
                lines[i] = "\t".join(d.get(c, "") for c in cols) + "\n"
                break
        _LOG_FILE.write_text("".join(lines))
    except Exception as exc:
        logger.warning(f"Could not update sample log row {log_id}: {exc}")


@app.get("/api/sample_log")
async def get_sample_log(request: Request):
    """Return sample log as JSON array for the UI."""
    if not _LOG_FILE.exists():
        return []
    lines = _LOG_FILE.read_text().splitlines()
    if len(lines) < 2:
        return []
    cols = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if line.strip():
            parts = line.split("\t")
            rows.append(dict(zip(cols, parts)))
    return rows


@app.post("/api/sample_log/{log_id}/notes")
async def update_notes(log_id: int, request: Request):
    """Update the notes field for a specific log entry."""
    body = await request.json()
    note = body.get("notes", "")
    if not _LOG_FILE.exists():
        raise HTTPException(404, "Log file not found")
    lines = _LOG_FILE.read_text().splitlines(keepends=True)
    cols  = lines[0].rstrip("\n").split("\t")
    notes_idx = cols.index("notes") if "notes" in cols else -1
    found = False
    for i, line in enumerate(lines[1:], 1):
        parts = line.rstrip("\n").split("\t")
        if parts and parts[0] == str(log_id):
            if notes_idx >= 0 and notes_idx < len(parts):
                parts[notes_idx] = note.replace("\t", " ").replace("\n", " ")
            else:
                while len(parts) <= notes_idx:
                    parts.append("")
                parts[notes_idx] = note.replace("\t", " ").replace("\n", " ")
            lines[i] = "\t".join(parts) + "\n"
            found = True
            break
    if not found:
        raise HTTPException(404, f"Log entry {log_id} not found")
    _LOG_FILE.write_text("".join(lines))
    return {"status": "updated", "log_id": log_id}

@app.get("/api/instrument_status")
async def instrument_status():
    """Return the last known T/B from idle polling (or null if not yet polled)."""
    return {
        "T_K": _sse_broadcast.__self__ if False else None,   # placeholder pattern
        "itc_configured": bool(_last_itc_cfg),
        "ips_configured": bool(_last_ips_cfg),
    }


@app.on_event("startup")
def _start_idle_poll():
    """Launch the idle-instrument-polling background thread at server startup."""
    global _idle_poll_thread
    _idle_poll_stop.clear()
    _idle_poll_thread = _threading.Thread(
        target=_idle_poll_worker, daemon=True, name="idle-poll")
    _idle_poll_thread.start()
    logger.info("Idle instrument poll thread started.")


# ── SSE replay cache ─────────────────────────────────────────────────────────
# Keeps the last 30 messages so a reconnecting client can catch up instantly.
_SSE_REPLAY_MAX  = 30
_sse_replay_cache: list = []        # list[LiveData], newest last
_sse_replay_lock  = _threading.Lock()

def _sse_cache_append(data: LiveData):
    with _sse_replay_lock:
        _sse_replay_cache.append(data)
        if len(_sse_replay_cache) > _SSE_REPLAY_MAX:
            del _sse_replay_cache[0]


@app.get("/api/export_zip")
async def export_zip():  # noqa: E302
    """Bundle all data files in the configured save folder into a ZIP archive
    and return it as a streaming download.  Only .txt and .csv files are included.
    If the save folder is not set, uses the directory containing app.py.
    """
    # Determine the data folder from the current (or last) config
    with lock:
        cfg = current_config
    folder = Path(getattr(cfg, 'save_folder', '').strip() if cfg else '') or Path(__file__).parent

    if not folder.exists():
        raise HTTPException(404, f"Save folder not found: {folder}")

    # Collect data files
    data_files = sorted(folder.glob("*.txt")) + sorted(folder.glob("*.csv"))
    if not data_files:
        raise HTTPException(404, "No data files found in save folder")

    # Build ZIP in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fpath in data_files:
            try:
                zf.write(fpath, arcname=fpath.name)
            except Exception as e:
                logger.warning(f"export_zip: skipping {fpath.name}: {e}")
    buf.seek(0)
    content = buf.read()   # read all bytes so we can set Content-Length

    from datetime import datetime
    from fastapi.responses import Response as _Response
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"QTMS_data_{stamp}.zip"
    return _Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )


def _ld_json(ld: "LiveData") -> str:
    """Serialize LiveData to JSON string — works with pydantic v1 and v2."""
    try:
        return ld.model_dump_json(exclude_none=False)   # pydantic v2
    except AttributeError:
        return ld.json()                                 # pydantic v1


@app.get("/api/stream")
async def stream(request: Request):
    # SSE requires Cache-Control: no-cache so proxies/browsers don't buffer.
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",   # tell nginx not to buffer SSE
    }
    # Create a per-client bounded queue and register it.
    # maxsize=300: a slow/disconnected tab fills up and new messages are
    # silently dropped (queue.Full) — it never blocks the sweep or leaks memory.
    client_q: queue.Queue = queue.Queue(maxsize=300)

    # Replay: if the browser sends Last-Event-ID, inject cached messages with
    # seq > that value so the header readouts restore instantly after a reconnect.
    last_id = 0
    try:
        raw_id = request.headers.get("Last-Event-ID", "0")
        last_id = int(raw_id) if raw_id else 0
    except (ValueError, TypeError):
        pass

    with _sse_lock:
        _sse_subscribers.append(client_q)

    # Mode announcement — sent before replay cache so 2nd window sets mode first
    with lock:
        _cfg_now = current_config
        _running = sweep_thread is not None and sweep_thread.is_alive()
    if _cfg_now:
        _ann = LiveData(sweep_mode=_cfg_now.mode,
                        phase="RUNNING" if _running else "IDLE")
        _ann.seq = 0
        try: client_q.put_nowait(_ann)
        except queue.Full: pass

    # Pre-fill the client queue with cached messages.
    # Fresh connection (last_id==0): replay all cached messages so a second
    # browser/PC joining mid-sweep sees the existing traces immediately.
    # Reconnect (last_id>0): only replay messages newer than the last seen id.
    with _sse_replay_lock:
        for cached in _sse_replay_cache:
            if last_id == 0 or cached.seq > last_id:
                try:
                    client_q.put_nowait(cached)
                except queue.Full:
                    pass

    async def gen():
        loop = asyncio.get_running_loop()
        last_yield = loop.time()
        MIN_INTERVAL = 0.10   # minimum seconds between SSE frames (10 Hz cap)
        try:
            while True:
                try:
                    data = await loop.run_in_executor(
                        None, client_q.get, True, 0.5)
                    # ── Drain any backlog: coalesce queued T/B-only messages ────
                    coalesced = data
                    while True:
                        try:
                            nxt = client_q.get_nowait()
                            has_measurement = (
                                coalesced.main_x is not None or
                                coalesced.Vxx_V is not None or
                                coalesced.phase is not None or
                                coalesced.progress is not None
                            )
                            if has_measurement:
                                yield f"id: {coalesced.seq}\nevent: msg\ndata: {_ld_json(coalesced)}\n\n"
                                _sse_cache_append(coalesced)
                                coalesced = nxt
                            else:
                                if nxt.T_K  is not None: coalesced.T_K  = nxt.T_K
                                if nxt.B_T  is not None: coalesced.B_T  = nxt.B_T
                                if nxt.t_s  is not None: coalesced.t_s  = nxt.t_s
                                if nxt.phase is not None:
                                    yield f"id: {coalesced.seq}\nevent: msg\ndata: {_ld_json(coalesced)}\n\n"
                                    _sse_cache_append(coalesced)
                                    coalesced = nxt
                        except queue.Empty:
                            break
                    yield f"id: {coalesced.seq}\nevent: msg\ndata: {_ld_json(coalesced)}\n\n"
                    _sse_cache_append(coalesced)
                    # Throttle: if we've been emitting too fast, yield a small pause
                    now = loop.time()
                    gap = MIN_INTERVAL - (now - last_yield)
                    if gap > 0:
                        await asyncio.sleep(gap)
                    last_yield = loop.time()
                except queue.Empty:
                    yield "event: ping\ndata: \n\n"
        finally:
            # Clean up when browser disconnects
            with _sse_lock:
                try:
                    _sse_subscribers.remove(client_q)
                except ValueError:
                    pass

    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)


# =============================================================================
# LAUNCHER  –  start server, open pywebview window
# =============================================================================
def _start_server():
    import uvicorn
    import socket
    import subprocess
    import sys

    # ── Collect all LAN IPs (not loopback) ─────────────────────────────────
    lan_ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if not ip.startswith("127.") and ":" not in ip:   # skip loopback + IPv6
                if ip not in lan_ips:
                    lan_ips.append(ip)
    except Exception:
        pass
    if not lan_ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ips = [s.getsockname()[0]]
            s.close()
        except Exception:
            lan_ips = ["<unknown>"]

    # ── Firewall self-check ─────────────────────────────────────────────────
    fw_ok = False
    fw_cmd = None
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule",
                 "name=QTMS", "dir=in"],
                capture_output=True, text=True, timeout=5)
            fw_ok = "QTMS" in result.stdout and "Allow" in result.stdout
        except Exception:
            fw_ok = False
        fw_cmd = (
            'netsh advfirewall firewall add rule name="QTMS" '
            'dir=in action=allow protocol=TCP localport=8000'
        )

    # ── Print startup banner ────────────────────────────────────────────────
    W = 66
    print("=" * W)
    print("  QTMS  —  Quantum Transport Measurement System")
    print("=" * W)
    print(f"  Local (this machine) :  http://127.0.0.1:8000")
    print()
    if len(lan_ips) == 1:
        print(f"  LAN / VPN access     :  http://{lan_ips[0]}:8000")
    else:
        print("  LAN / VPN access (all interfaces):")
        for ip in lan_ips:
            print(f"      http://{ip}:8000")
    print()
    print("  ── Remote access guide ──────────────────────────────────")
    print("  Office PC / lab PC on wired LAN  →  use any IP above")
    print("  Phone on eduroam wifi            →  eduroam blocks PC↔phone")
    print("    FIX: connect phone to university VPN first, then use IP above")
    print("  Phone on university VPN          →  use any IP above  ✓")
    print("  Phone on personal hotspot        →  will NOT work (different net)")
    print()

    if sys.platform == "win32":
        if fw_ok:
            print("  Firewall rule (port 8000) :  ✓ already open")
        else:
            print("  Firewall rule (port 8000) :  ✗ NOT FOUND — remote devices cannot connect!")
            print("  Run this once in an elevated PowerShell to fix:")
            print(f"    {fw_cmd}")
    print()
    print("  Auth config  :  qtms_auth.cfg  (same folder as app.py)")
    print("  Roles        :  control (full), monitor (view only — for phone)")
    print("  Add user     :  python app.py --add-user")
    print("=" * W)

    port = int(getattr(_start_server, '_port', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def _wait_for_server(url="http://127.0.0.1:8000", timeout=15):
    import urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except:
            time.sleep(0.2)
    return False


if __name__ == "__main__":
    # First line in the log, every launch — the proof of which build is live.
    logger.info("=" * 60)
    logger.info("QTMS starting — %s", APP_VERSION)
    logger.info("Code path: %s", os.path.abspath(__file__))
    logger.info("=" * 60)
    import ctypes
    import argparse as _ap
    _parser = _ap.ArgumentParser(description="QTMS — Quantum Transport Measurement System")
    _parser.add_argument("--port", type=int, default=8000,
                         help="HTTP port to serve on (default 8000; use 80 for firewall bypass, requires admin)")
    _parser.add_argument("--add-user", action="store_true", help="Add/update a user password interactively")
    _args, _ = _parser.parse_known_args()

    if _args.add_user:
        print("=== QTMS User Management ===")
        role = input("Role (monitor/control): ").strip().lower()
        if role not in ("monitor", "control"):
            print("Invalid role."); import sys; sys.exit(1)
        pw = input(f"New {role} password: ").strip()
        if not pw: print("Empty password rejected."); import sys; sys.exit(1)
        cfg = _load_auth()
        salt = __import__('secrets').token_hex(16)
        cfg[f'{role}_salt'] = salt
        cfg[f'{role}_hash'] = _pbkdf2(pw, salt)
        _AUTH_FILE.write_text(__import__('json').dumps(cfg, indent=2))
        print(f"✓ {role} password updated in {_AUTH_FILE}"); import sys; sys.exit(0)

    _start_server._port = _args.port

    def show_error(msg):
        """Show a visible popup error on Windows so crashes aren't silent."""
        try:
            ctypes.windll.user32.MessageBoxW(0, msg, "QTMS – Error", 0x10)
        except:
            pass  # non-Windows fallback — just silently ignore

    def _prevent_sleep():
        """Tell Windows not to sleep while QTMS is running.

        SetThreadExecutionState flags:
          ES_CONTINUOUS      (0x80000000) — keep this state until cleared
          ES_SYSTEM_REQUIRED (0x00000001) — prevent system sleep
          ES_DISPLAY_REQUIRED (0x00000002) — prevent screen-saver / display sleep
        Combined: 0x80000003 prevents both sleep and screen-off.
        No admin rights required.  Cleared on process exit automatically.
        """
        try:
            ES_CONTINUOUS       = 0x80000000
            ES_SYSTEM_REQUIRED  = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            print("  Sleep prevention : active (PC will not sleep while QTMS runs)")
        except Exception as e:
            print(f"  Sleep prevention : unavailable ({e})")

    def _allow_sleep():
        """Re-enable normal sleep policy when QTMS exits."""
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS alone = clear
        except:
            pass

    try:
        import os
        _prevent_sleep()   # keep PC awake for the entire QTMS session

        # ── Port conflict: check if another QTMS is already alive ───────────
        # If port 8000 is already serving our app, just open the browser
        # and reuse it — no need to kill anything.
        already_running = False
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://127.0.0.1:8000/api/state", timeout=1)
            if resp.status == 200:
                already_running = True
                print("  Existing QTMS server detected — reusing it.")
        except Exception:
            pass  # port free or different app; proceed to start fresh

        if already_running:
            # Just open the browser window, skip starting a new server
            import subprocess
            browsers = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]
            for browser in browsers:
                if os.path.exists(browser):
                    subprocess.Popen([browser, "--app=http://127.0.0.1:8000",
                                      "--window-size=1600,980", "--window-position=50,30",
                                      "--disable-extensions", "--no-first-run",
                                      "--no-default-browser-check"])
                    break
            else:
                webbrowser.open("http://127.0.0.1:8000")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                _allow_sleep()
            sys.exit(0)

        # Start FastAPI backend in background thread
        server_thread = threading.Thread(target=_start_server, daemon=True)
        server_thread.start()

        # Wait up to 20 seconds for server to be ready
        if not _wait_for_server(timeout=20):
            show_error(
                "QTMS could not start the backend server.\n\n"
                "Make sure no other program is using port 8000,\n"
                "then try double-clicking QTMS.exe again."
            )
            sys.exit(1)

        # Open as a proper desktop app window using Chrome/Edge app mode.
        # This gives a native-looking window with no address bar, no tabs —
        # identical to a standalone application.
        import subprocess

        # Candidate browser paths on Windows
        browsers = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]

        launched = False
        for browser in browsers:
            if os.path.exists(browser):
                subprocess.Popen([
                    browser,
                    "--app=http://127.0.0.1:8000",
                    "--window-size=1600,980",
                    "--window-position=50,30",
                    "--disable-extensions",
                    "--no-first-run",
                    "--no-default-browser-check",
                ])
                launched = True
                break

        if not launched:
            # No Chrome/Edge found — fall back to default browser
            webbrowser.open("http://127.0.0.1:8000")

        # Keep the server alive while the app is open
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            _allow_sleep()

    except Exception as e:
        _allow_sleep()
        show_error(
            f"QTMS crashed on startup:\n\n{e}\n\n"
            "Please report this message."
        )
