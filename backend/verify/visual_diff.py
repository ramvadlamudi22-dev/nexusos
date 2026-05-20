"""Visual diff engine — compares screenshots against baselines to detect regressions."""

import hashlib
import struct
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class VisualDiffEngine:
    """Compares verification screenshots against stored baselines.

    Uses PNG pixel comparison for accurate visual regression detection.
    Falls back to size-based comparison if pixel parsing fails.
    """

    def __init__(self, baselines_dir: str = "artifacts/baselines"):
        self._baselines_dir = Path(baselines_dir)
        self._baselines_dir.mkdir(parents=True, exist_ok=True)

    def compare(
        self, current_path: str, target_url: str, page_path: str
    ) -> Dict:
        """Compare a screenshot against its baseline.

        Args:
            current_path: Path to the current screenshot.
            target_url: Target URL (used for baseline key).
            page_path: Page path (used for baseline key).

        Returns:
            Comparison result with match status and diff metrics.
        """
        baseline_key = self._make_key(target_url, page_path)
        baseline_path = self._baselines_dir / f"{baseline_key}.png"

        current = Path(current_path)
        if not current.exists():
            return {
                "status": "NO_CURRENT",
                "baseline_exists": baseline_path.exists(),
                "diff_percent": None,
                "message": "Current screenshot not found",
            }

        if not baseline_path.exists():
            self._save_baseline(current, baseline_path)
            return {
                "status": "NEW_BASELINE",
                "baseline_exists": False,
                "diff_percent": 0.0,
                "message": "First run — screenshot saved as baseline",
                "baseline_path": str(baseline_path),
            }

        # Compare content hashes (fast path)
        current_bytes = current.read_bytes()
        baseline_bytes = baseline_path.read_bytes()
        current_hash = hashlib.sha256(current_bytes).hexdigest()
        baseline_hash = hashlib.sha256(baseline_bytes).hexdigest()

        if current_hash == baseline_hash:
            return {
                "status": "MATCH",
                "baseline_exists": True,
                "diff_percent": 0.0,
                "message": "Screenshot matches baseline exactly",
                "current_hash": current_hash[:16],
                "baseline_hash": baseline_hash[:16],
            }

        # Pixel-level comparison
        diff_percent = self._pixel_diff(current_bytes, baseline_bytes)

        if diff_percent is not None:
            if diff_percent > 5.0:
                return {
                    "status": "REGRESSION",
                    "baseline_exists": True,
                    "diff_percent": round(diff_percent, 2),
                    "message": f"Visual regression: {diff_percent:.2f}% pixels differ",
                    "current_hash": current_hash[:16],
                    "baseline_hash": baseline_hash[:16],
                }
            elif diff_percent > 0.5:
                return {
                    "status": "CHANGED",
                    "baseline_exists": True,
                    "diff_percent": round(diff_percent, 2),
                    "message": f"Minor visual change: {diff_percent:.2f}% pixels differ",
                    "current_hash": current_hash[:16],
                    "baseline_hash": baseline_hash[:16],
                }
            else:
                return {
                    "status": "MATCH",
                    "baseline_exists": True,
                    "diff_percent": round(diff_percent, 2),
                    "message": "Screenshots match (sub-pixel rendering variance)",
                    "current_hash": current_hash[:16],
                    "baseline_hash": baseline_hash[:16],
                }

        # Fallback: size-based comparison
        size_diff = abs(len(current_bytes) - len(baseline_bytes)) / max(len(baseline_bytes), 1) * 100
        status = "REGRESSION" if size_diff > 20 else "CHANGED" if size_diff > 5 else "MATCH"
        return {
            "status": status,
            "baseline_exists": True,
            "diff_percent": round(size_diff, 2),
            "message": f"Size-based comparison: {size_diff:.1f}% difference",
            "current_hash": current_hash[:16],
            "baseline_hash": baseline_hash[:16],
        }

    def _pixel_diff(self, png_a: bytes, png_b: bytes) -> Optional[float]:
        """Compare two PNG images at the pixel level.

        Returns percentage of differing pixels, or None if parsing fails.
        """
        try:
            pixels_a = self._decode_png_pixels(png_a)
            pixels_b = self._decode_png_pixels(png_b)

            if pixels_a is None or pixels_b is None:
                return None

            if len(pixels_a) != len(pixels_b):
                # Different dimensions — 100% different
                return 100.0

            total_pixels = len(pixels_a)
            if total_pixels == 0:
                return 0.0

            diff_count = sum(1 for a, b in zip(pixels_a, pixels_b) if a != b)
            return (diff_count / total_pixels) * 100

        except Exception:
            return None

    def _decode_png_pixels(self, png_data: bytes) -> Optional[List[int]]:
        """Decode PNG to raw pixel bytes (simplified decoder for comparison).

        Extracts IDAT chunks, decompresses, and returns raw scanline data.
        """
        try:
            if png_data[:8] != b'\x89PNG\r\n\x1a\n':
                return None

            pos = 8
            width = height = bit_depth = color_type = 0
            idat_chunks = []

            while pos < len(png_data):
                length = struct.unpack('>I', png_data[pos:pos+4])[0]
                chunk_type = png_data[pos+4:pos+8]
                chunk_data = png_data[pos+8:pos+8+length]
                pos += 12 + length  # 4(len) + 4(type) + data + 4(crc)

                if chunk_type == b'IHDR':
                    width = struct.unpack('>I', chunk_data[0:4])[0]
                    height = struct.unpack('>I', chunk_data[4:8])[0]
                    bit_depth = chunk_data[8]
                    color_type = chunk_data[9]
                elif chunk_type == b'IDAT':
                    idat_chunks.append(chunk_data)
                elif chunk_type == b'IEND':
                    break

            if not idat_chunks or width == 0:
                return None

            # Decompress
            raw = zlib.decompress(b''.join(idat_chunks))

            # For comparison purposes, just return the raw decompressed bytes
            # Each scanline has a filter byte + pixel data
            # We compare the raw bytes directly (filter byte differences are acceptable)
            return list(raw)

        except Exception:
            return None

    def update_baseline(self, current_path: str, target_url: str, page_path: str) -> bool:
        """Update the baseline with the current screenshot."""
        current = Path(current_path)
        if not current.exists():
            return False
        baseline_key = self._make_key(target_url, page_path)
        baseline_path = self._baselines_dir / f"{baseline_key}.png"
        self._save_baseline(current, baseline_path)
        return True

    def get_baseline_info(self, target_url: str, page_path: str) -> Optional[Dict]:
        """Get info about a stored baseline."""
        baseline_key = self._make_key(target_url, page_path)
        baseline_path = self._baselines_dir / f"{baseline_key}.png"
        if not baseline_path.exists():
            return None
        return {
            "key": baseline_key,
            "path": str(baseline_path),
            "size_bytes": baseline_path.stat().st_size,
            "hash": hashlib.sha256(baseline_path.read_bytes()).hexdigest()[:16],
        }

    def list_baselines(self) -> List[Dict]:
        """List all stored baselines."""
        return [
            {"key": f.stem, "path": str(f), "size_bytes": f.stat().st_size}
            for f in self._baselines_dir.glob("*.png")
        ]

    def _make_key(self, target_url: str, page_path: str) -> str:
        """Generate a deterministic key for a baseline."""
        return hashlib.sha256(f"{target_url}{page_path}".encode()).hexdigest()[:24]

    def _save_baseline(self, source: Path, dest: Path) -> None:
        """Copy a screenshot to the baselines directory."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
