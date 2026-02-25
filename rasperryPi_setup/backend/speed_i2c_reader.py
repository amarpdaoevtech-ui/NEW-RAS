#!/usr/bin/env python3
import smbus2
import time
import json
import re
import logging

logger = logging.getLogger(__name__)

class SpeedI2CReader:
    def __init__(self, bus_id=1, addr=0x08):
        self.bus_id = bus_id
        self.addr = addr
        self.bus = None
        self.last_seq = None
        self.last_mode = None
        self.mode_names = {0: "LOW", 1: "MED", 2: "HIGH"} # Updated based on user script: 0=LOW, 1=MED, 2=HIGH
        self.last_data = {
            "speed_kmph": 0.0,
            "throttle": 0.0,
            "mode": "ECONOMY",
            "mode_index": 1,
            "voltage": 0.0,
            "soc": 0,
            "current": 0,
            "brake": 0,
            "seq": 0
        }
        self.connected = False

    def connect(self):
        try:
            self.bus = smbus2.SMBus(self.bus_id)
            self.connected = True
            logger.info(f"Connected to Speed I2C Bus {self.bus_id} at address {hex(self.addr)}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Speed I2C: {e}")
            self.connected = False
            return False

    def _parse_best_frame(self, raw_bytes):
        """
        ✅ FIX: Extract the LAST (most recent) valid JSON frame from the I2C buffer.
        Motor electrical noise can corrupt the 128-byte buffer, creating multiple
        partial or overlapping frames. We scan ALL matches and use the last valid one.
        """
        text = "".join(chr(b) for b in raw_bytes if 32 <= b < 127).strip()
        all_matches = list(re.finditer(r'<(\{[^>]+\})>', text))

        if not all_matches:
            return None

        # Try from last match backward (most recent = most reliable)
        for match in reversed(all_matches):
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

        return None

    def read_data(self):
        if not self.bus:
            if not self.connect():
                return None

        raw = None
        try:
            msg = smbus2.i2c_msg.read(self.addr, 128)
            self.bus.i2c_rdwr(msg)
            raw = list(msg)
        except OSError as e:
            # ✅ FIX: Retry once on I2C OS error.
            # Motor EMI causes transient bus errors. A short backoff + retry
            # recovers the frame instead of silently dropping the throttle update.
            logger.debug(f"I2C OSError (retrying in 5ms): {e}")
            try:
                time.sleep(0.005)
                msg = smbus2.i2c_msg.read(self.addr, 128)
                self.bus.i2c_rdwr(msg)
                raw = list(msg)
            except Exception as retry_err:
                logger.debug(f"I2C retry failed: {retry_err}")
                # Reset bus so next call re-connects
                try:
                    self.bus.close()
                except Exception:
                    pass
                self.bus = None
                self.connected = False
                return None
        except Exception as e:
            logger.debug(f"I2C Read Error: {e}")
            return None

        if raw is None:
            return None

        d = self._parse_best_frame(raw)

        if d is None:
            return None

        current_seq = d.get('seq', -1)
        new_throttle = float(d.get('th', 0.0))
        last_throttle = self.last_data.get('throttle', 0.0)

        # ✅ FIX: Relaxed sequence dedup.
        # OLD behaviour: skip ANY frame with the same seq number. This caused the
        # throttle to FREEZE at 0% when motor noise made the ESP32 retransmit the
        # same seq while the throttle position had changed.
        # NEW behaviour: only skip if seq is the same AND throttle hasn't moved
        # more than 1 percentage point. If throttle moved, accept the frame.
        if self.last_seq is not None and current_seq == self.last_seq:
            if abs(new_throttle - last_throttle) <= 1.0:
                return None  # Truly duplicate - nothing changed
            logger.debug(
                f"Seq={current_seq} repeated but throttle changed "
                f"{last_throttle:.1f}% -> {new_throttle:.1f}%, accepting frame"
            )

        self.last_seq = current_seq

        # Sanity check speed
        speed = float(d.get('spd', 0.0))
        if speed > 150 or speed < 0:
            speed = 0.0

        # Clamp throttle
        throttle = max(0.0, min(100.0, new_throttle))

        mode_idx = d.get('mode', 1)
        mode_str = self.mode_names.get(mode_idx, f"UNK({mode_idx})")

        logger.debug(
            f"I2C Frame OK: seq={current_seq} spd={speed:.1f}km/h "
            f"th={throttle:.1f}% mode={mode_str}"
        )

        self.last_data = {
            "speed_kmph": round(speed, 1),
            "throttle": round(throttle, 1),
            "mode": mode_str,
            "mode_index": mode_idx,
            "voltage": d.get('v', 0.0),
            "soc": d.get('soc', 0),
            "current": d.get('cur', 0),
            "brake": d.get('brk', 0),
            "seq": current_seq
        }

        return self.last_data

    def close(self):
        if self.bus:
            self.bus.close()
