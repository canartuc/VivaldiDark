"""Build a theme folder into an installable Vivaldi theme zip."""
import importlib.util
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from tools.render import render_svg
from tools.settings_schema import DEFAULT_COLOURS, EXPORT_KEYS, MAX_ZIP_BYTES, MIN_ALPHA, MIN_IMAGE, SHARED

REPO = Path(__file__).resolve().parent.parent


@dataclass
class ThemeConfig:
    slug: str
    name: str
    id: str
    highlight: str
    radius: int
    alpha: float
    blur: int
    webp_quality: int | None = None  # lossy quality for vector scenes; pixel scenes are always lossless
    bg: str = DEFAULT_COLOURS["bg"]
    fg: str = DEFAULT_COLOURS["fg"]
    accent: str = DEFAULT_COLOURS["accent"]
    window: str = DEFAULT_COLOURS["window"]
    contrast: int = DEFAULT_COLOURS["contrast"]
    icons: str = "outline"


ICON_FAMILIES = ("outline", "pixel")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)  # fixed, so a rebuild with the same inputs gives the same bytes


def load_config(theme_dir: Path) -> ThemeConfig:
    return ThemeConfig(**json.loads((theme_dir / "theme.json").read_text()))


def load_scene(theme_dir: Path):
    spec = importlib.util.spec_from_file_location(f"scene_{theme_dir.name}", theme_dir / "scene.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_settings(cfg: ThemeConfig, buttons: dict[str, str]) -> dict:
    return {
        **SHARED,
        "alpha": cfg.alpha,
        "blur": cfg.blur,
        "buttons": dict(buttons),
        "colorAccentBg": cfg.accent,
        "colorBg": cfg.bg,
        "colorFg": cfg.fg,
        "colorHighlightBg": cfg.highlight,
        "colorWindowBg": cfg.window,
        "contrast": cfg.contrast,
        "id": cfg.id,
        "name": cfg.name,
        "radius": cfg.radius,
    }


def validate(settings: dict, image: Path, zip_path: Path) -> list[str]:
    problems = []
    keys = set(settings)
    if keys - EXPORT_KEYS:
        problems.append(f"unknown settings keys: {sorted(keys - EXPORT_KEYS)}")
    if EXPORT_KEYS - keys:
        problems.append(f"missing settings keys: {sorted(EXPORT_KEYS - keys)}")
    name = settings.get("name", "")
    if "·" in name or any(w in name.lower() for w in ("vivaldinight", "vivaldidark")):
        problems.append(f"name {name!r} must be the theme title only, with no collection prefix")
    if settings.get("alpha", 0) < MIN_ALPHA:
        problems.append(f"alpha {settings.get('alpha')} < {MIN_ALPHA} makes every tab title white")
    w, h = Image.open(image).size
    if w < MIN_IMAGE[0] or h < MIN_IMAGE[1]:
        problems.append(f"image {w}x{h} is smaller than {MIN_IMAGE[0]}x{MIN_IMAGE[1]}")
    if zip_path.stat().st_size >= MAX_ZIP_BYTES:
        problems.append(f"zip is {zip_path.stat().st_size} bytes; the gallery limit is 8 MB")
    return problems


def check_config(cfg: ThemeConfig, raster: bool) -> list[str]:
    problems = []
    if cfg.icons not in ICON_FAMILIES:
        problems.append(f"icons {cfg.icons!r} must be one of {ICON_FAMILIES}")
    if raster and cfg.webp_quality is not None:
        problems.append("webp_quality has no effect on a pixel scene (always lossless); remove it")
    if not raster and cfg.webp_quality is None:
        problems.append("webp_quality is required for a vector scene")
    return problems


def zip_name(cfg: ThemeConfig) -> str:
    return cfg.name.replace(" ", "-") + ".zip"


def build_theme(theme_dir: Path, icons_dir: Path) -> Path:
    theme_dir = Path(theme_dir)
    cfg = load_config(theme_dir)
    work = theme_dir.parent.parent / "build" / cfg.slug
    work.mkdir(parents=True, exist_ok=True)

    scene = load_scene(theme_dir)
    raster = hasattr(scene, "build_image")
    problems = check_config(cfg, raster)
    if problems:
        raise ValueError(f"{cfg.name}: " + "; ".join(problems))
    image = theme_dir / "background.webp"
    if raster:  # raster (pixel-art) scene: lossless keeps every pixel edge hard
        scene.build_image().convert("RGB").save(image, "WEBP", lossless=True, method=6)
    else:
        svg_path, png_path = work / "art.svg", work / "art.png"
        svg_path.write_text(scene.build())
        render_svg(svg_path, png_path)
        Image.open(png_path).convert("RGB").save(image, "WEBP", quality=cfg.webp_quality, method=6)

    icons_dir = Path(icons_dir) / "pixel" if cfg.icons == "pixel" else Path(icons_dir)
    manifest = icons_dir / "manifest.json"
    if not manifest.exists():
        raise ValueError(f"{cfg.name}: no icon manifest at {manifest}")
    buttons = json.loads(manifest.read_text())
    settings = build_settings(cfg, buttons)
    settings_path = work / "settings.json"
    settings_path.write_text(json.dumps(settings, indent=3) + "\n")

    zip_path = theme_dir / zip_name(cfg)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for src, name in [(settings_path, "settings.json"), (image, "background.webp")] + [
                (icons_dir / f, f) for f in sorted(set(buttons.values()))]:
            info = zipfile.ZipInfo(name, ZIP_DATE)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(info, src.read_bytes())

    problems = validate(settings, image, zip_path)
    if problems:
        raise ValueError(f"{cfg.name}: " + "; ".join(problems))
    return zip_path


if __name__ == "__main__":
    print(build_theme(Path(sys.argv[1]), REPO / "icons"))
