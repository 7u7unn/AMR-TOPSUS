"""Map selection, navigation annotations, and keepout-mask utilities."""

import json
import logging
import math
import re
import threading
import time
import uuid
from pathlib import Path

from .maps import parse_map_yaml, point_in_polygon, read_pgm_image


logger = logging.getLogger("AryaWebInterface.MapManagement")

MAP_SELECTION_FILE = Path.home() / ".arya_amr" / "selected_localization_map.txt"
KEEPOUT_SELECTION_FILE = Path.home() / ".arya_amr" / "selected_keepout_mask.txt"

MAP_SELECTION_LOCK = threading.Lock()
MAPPING_SAVE_LOCK = threading.Lock()


def nav_annotation_path(map_path: Path) -> Path:
    """Get navigation annotation JSON file path for a map."""
    return map_path.with_name(f"{map_path.stem}_nav.json")


def keepout_mask_paths(map_path: Path) -> tuple[Path, Path]:
    """Get file paths for keepout mask PGM and YAML."""
    return (
        map_path.with_name(f"{map_path.stem}_keepout.pgm"),
        map_path.with_name(f"{map_path.stem}_keepout.yaml"),
    )


def normalize_annotation_id(raw_id: str | None, prefix: str) -> str:
    """Normalize annotation ID or generate a unique one."""
    clean_id = str(raw_id or "").strip()
    if clean_id and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", clean_id):
        return clean_id
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def normalize_keepout_zone(raw_zone: dict, index: int) -> dict:
    """Validate and normalize keepout zone parameters."""
    if not isinstance(raw_zone, dict):
        raise ValueError("Restriction area harus object.")

    points = raw_zone.get("points")
    if not isinstance(points, list) or len(points) != 4:
        raise ValueError("Restriction area harus berupa rectangle 4 titik.")

    clean_points = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            raise ValueError("Titik restriction area tidak valid.")
        try:
            x = float(point[0])
            y = float(point[1])
        except (TypeError, ValueError) as exc:
            raise ValueError("Koordinat restriction area tidak valid.") from exc
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Koordinat restriction area tidak valid.")
        clean_points.append([round(x, 4), round(y, 4)])

    return {
        "id": normalize_annotation_id(raw_zone.get("id"), "zone"),
        "name": str(raw_zone.get("name") or f"Restriction {index + 1}").strip()[:80],
        "enabled": bool(raw_zone.get("enabled", True)),
        "points": clean_points,
    }


def normalize_station(raw_station: dict, index: int) -> dict:
    """Validate and normalize station parameters."""
    if not isinstance(raw_station, dict):
        raise ValueError("Station harus object.")
    try:
        x = float(raw_station.get("x"))
        y = float(raw_station.get("y"))
        theta = float(raw_station.get("theta"))
        wait_sec = float(raw_station.get("wait_sec", 0.0) or 0.0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Koordinat station tidak valid.") from exc

    if not all(math.isfinite(value) for value in (x, y, theta, wait_sec)):
        raise ValueError("Koordinat station tidak valid.")
    if wait_sec < 0:
        raise ValueError("wait_sec station tidak boleh negatif.")

    return {
        "id": normalize_annotation_id(raw_station.get("id"), "station"),
        "name": str(raw_station.get("name") or f"Station {index + 1}").strip()[:80],
        "x": round(x, 4),
        "y": round(y, 4),
        "theta": round(theta, 6),
        "wait_sec": round(wait_sec, 2),
        "enabled": bool(raw_station.get("enabled", True)),
    }


def write_keepout_mask(map_path: Path, zones: list[dict]) -> dict:
    """Write keepout mask PGM image and YAML descriptor files."""
    metadata = parse_map_yaml(map_path)
    width, height, _pixels = read_pgm_image(metadata["image_path"])
    resolution = float(metadata["resolution"])
    ox, oy, _oyaw = metadata["origin"]
    pgm_path, yaml_path = keepout_mask_paths(map_path)
    mask = bytearray([255] * (width * height))

    for zone in zones:
        if not zone.get("enabled", True):
            continue
        points = zone["points"]
        min_x = min(point[0] for point in points)
        max_x = max(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_y = max(point[1] for point in points)
        col_start = max(0, int(math.floor((min_x - ox) / resolution)) - 1)
        col_end = min(width - 1, int(math.ceil((max_x - ox) / resolution)) + 1)
        row_start = max(0, int(math.floor((min_y - oy) / resolution)) - 1)
        row_end = min(height - 1, int(math.ceil((max_y - oy) / resolution)) + 1)

        for grid_row in range(row_start, row_end + 1):
            wy = oy + (grid_row + 0.5) * resolution
            image_row = height - 1 - grid_row
            for col in range(col_start, col_end + 1):
                wx = ox + (col + 0.5) * resolution
                if point_in_polygon(wx, wy, points):
                    mask[image_row * width + col] = 0

    with pgm_path.open("wb") as stream:
        stream.write(f"P5\n{width} {height}\n255\n".encode("ascii"))
        stream.write(mask)

    origin = metadata["origin"]
    yaml_text = "\n".join([
        f"image: {pgm_path.name}",
        "mode: trinary",
        f"resolution: {resolution}",
        f"origin: [{origin[0]}, {origin[1]}, 0]",
        "negate: 0",
        "occupied_thresh: 0.65",
        "free_thresh: 0.25",
        "",
    ])
    yaml_path.write_text(yaml_text, encoding="utf-8")
    KEEPOUT_SELECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEEPOUT_SELECTION_FILE.write_text(str(yaml_path.resolve()) + "\n", encoding="utf-8")

    return {
        "pgm_path": str(pgm_path),
        "yaml_path": str(yaml_path),
        "yaml_name": yaml_path.name,
        "width": width,
        "height": height,
    }


def save_nav_annotations(map_path: Path, zones: list[dict], stations: list[dict]) -> dict:
    """Save navigation annotations and write keepout mask."""
    clean_zones = [
        normalize_keepout_zone(zone, index)
        for index, zone in enumerate(zones or [])
    ]
    clean_stations = [
        normalize_station(station, index)
        for index, station in enumerate(stations or [])
    ]
    annotations_path = nav_annotation_path(map_path)
    payload = {
        "map_name": map_path.name,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "zones": clean_zones,
        "stations": clean_stations,
    }
    annotations_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    mask = write_keepout_mask(map_path, clean_zones)
    return {
        "ok": True,
        "message": "Restriction area dan station tersimpan. Restart Nav2 untuk menerapkan keepout.",
        "map_name": map_path.name,
        "zones": clean_zones,
        "stations": clean_stations,
        "annotation_path": str(annotations_path),
        "keepout": mask,
        "restart_required": True,
    }


def find_maps_folder() -> Path | None:
    """Find maps folder from package share directory or fallbacks."""
    current_dir = Path(__file__).resolve().parent
    candidates = []

    for parent in current_dir.parents:
        candidates.append(parent / "amr_bringup_headless" / "maps")
        candidates.append(parent / "amr_bringup_headless" / "amr_bringup_headless" / "maps")
        candidates.append(parent / "amr_bringup" / "maps")

    candidates.append(Path.home() / "arya_ws" / "src" / "amr_bringup_headless" / "maps")
    candidates.append(Path.home() / "awg_ws" / "src" / "amr_bringup_headless" / "maps")

    for package_name in ("amr_bringup_headless", "amr_bringup"):
        try:
            from ament_index_python.packages import get_package_share_directory
            bringup_share = Path(get_package_share_directory(package_name))
            candidates.append(bringup_share / "maps")
        except Exception:
            pass

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    local_maps = current_dir / "maps"
    if local_maps.exists() and local_maps.is_dir():
        return local_maps

    return None


def find_localization_config() -> Path | None:
    """Find AMCL configuration file for default map lookup."""
    current_dir = Path(__file__).resolve().parent
    candidates = []

    for parent in current_dir.parents:
        candidates.append(parent / "amr_bringup_headless" / "config" / "amcl.yaml")
        candidates.append(parent / "amr_bringup_headless" / "amr_bringup_headless" / "config" / "amcl.yaml")
        candidates.append(parent / "amr_bringup" / "config" / "amcl.yaml")

    candidates.append(Path.home() / "arya_ws" / "src" / "amr_bringup_headless" / "config" / "amcl.yaml")
    candidates.append(Path.home() / "awg_ws" / "src" / "amr_bringup_headless" / "config" / "amcl.yaml")

    for package_name in ("amr_bringup_headless", "amr_bringup"):
        try:
            from ament_index_python.packages import get_package_share_directory
            bringup_share = Path(get_package_share_directory(package_name))
            candidates.append(bringup_share / "config" / "amcl.yaml")
        except Exception:
            pass

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    return None


def read_selected_map_path(maps_dir: Path | None = None) -> Path | None:
    """Read the manually selected map file path."""
    try:
        raw_value = MAP_SELECTION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if not raw_value:
        return None

    candidate = Path(raw_value).expanduser()
    if not candidate.is_absolute():
        if maps_dir is None:
            maps_dir = find_maps_folder()
        if maps_dir is None:
            return None
        candidate = maps_dir / candidate.name

    if candidate.exists() and candidate.is_file():
        return candidate

    return None


def extract_default_map_name(maps_dir: Path | None) -> str | None:
    """Extract selected/default map name from user selection or AMCL config."""
    if maps_dir is None:
        return None

    selected_map_path = read_selected_map_path(maps_dir)
    if selected_map_path is not None:
        return selected_map_path.name

    config_path = find_localization_config()
    if config_path:
        try:
            for line in config_path.read_text(encoding="utf-8").splitlines():
                if "yaml_filename:" not in line:
                    continue
                raw_value = line.split("yaml_filename:", 1)[1].strip().strip('"').strip("'")
                if not raw_value:
                    continue
                map_path = Path(raw_value).expanduser()
                if not map_path.is_absolute():
                    map_path = maps_dir / map_path.name
                elif not map_path.exists():
                    map_path = maps_dir / map_path.name
                if map_path.exists():
                    return map_path.name
        except OSError:
            pass

    available_maps = sorted(
        [
            path
            for path in maps_dir.glob("*.yaml")
            if path.is_file() and not path.name.endswith("_keepout.yaml")
        ],
        key=lambda path: path.name.casefold(),
    )
    return available_maps[0].name if available_maps else None


def save_selected_keepout_for_map(map_path: Path):
    """Save default keepout mask path corresponding to the map."""
    keepout_path = map_path.with_name(f"{map_path.stem}_keepout.yaml")
    if not keepout_path.exists():
        mask = write_keepout_mask(map_path, [])
        keepout_path = Path(mask["yaml_path"])

    if keepout_path is None:
        return

    KEEPOUT_SELECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        KEEPOUT_SELECTION_FILE.write_text(str(keepout_path.resolve()) + "\n", encoding="utf-8")
        logger.info(f"Keepout mask selected: {keepout_path}")
    except OSError as exc:
        raise RuntimeError(f"Gagal menyimpan keepout mask pilihan: {exc}") from exc


def save_selected_map(map_path: Path):
    """Persist selected map and its corresponding keepout mask."""
    MAP_SELECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        MAP_SELECTION_FILE.write_text(str(map_path) + "\n", encoding="utf-8")
        logger.info(f"Localization map selected: {map_path}")
    except OSError as exc:
        raise RuntimeError(f"Gagal menyimpan map pilihan: {exc}") from exc

    save_selected_keepout_for_map(map_path)


def get_mapping_save_dir() -> Path:
    """Get the target directory to save SLAM maps."""
    maps_dir = find_maps_folder()
    if maps_dir is not None:
        return maps_dir
    fallback_dir = Path.home() / "arya_ws" / "src" / "amr_bringup_headless" / "maps"
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir
