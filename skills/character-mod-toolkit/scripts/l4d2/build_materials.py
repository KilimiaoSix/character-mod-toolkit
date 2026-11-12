"""Build Source 1 VTF 7.2/DXT1 and VMT from extracted opaque base colors."""
from io import BytesIO
from struct import pack_into
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageStat

from rochelle_profile import MATERIAL_DIR, STEM

DXT1 = 13
HEADER_SIZE = 80


def encode_dxt1(image):
    payload = BytesIO()
    image.save(payload, format="DDS", pixel_format="DXT1")
    dds = payload.getvalue()
    width, height = image.size
    expected = ((width + 3) // 4) * ((height + 3) // 4) * 8
    if dds[:4] != b"DDS " or dds[84:88] != b"DXT1" or len(dds) != 128 + expected:
        raise ValueError(f"Invalid DXT1 payload for {image.size}; check Pillow version")
    return dds[128:]


def srgb_to_linear(value):
    value /= 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def linear_to_srgb(value):
    value = max(0, min(1, value))
    return round(255 * (12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055))


def build_vtf(image):
    width, height = image.size
    if width != height or width & (width - 1):
        raise ValueError("Expected square power-of-two dimensions")
    level_count = width.bit_length()
    thumbnail_size = min(width, 16)
    thumbnail = image.resize((thumbnail_size, thumbnail_size), Image.Resampling.BOX)
    reflectivity = [srgb_to_linear(value) for value in ImageStat.Stat(thumbnail).mean]
    header = bytearray(HEADER_SIZE)
    pack_into("<4sIIIHHIHH", header, 0, b"VTF\x00", 7, 2, HEADER_SIZE, width, height, 0x02, 1, 0)
    pack_into("<3f", header, 32, *reflectivity)
    pack_into("<fIBIBBH", header, 48, 1.0, DXT1, level_count, DXT1, thumbnail_size, thumbnail_size, 1)
    images = [encode_dxt1(thumbnail)]
    for level in range(level_count):
        size = 1 << level
        mip = image if size == width else image.resize((size, size), Image.Resampling.BOX)
        images.append(encode_dxt1(mip))
    return bytes(header) + b"".join(images)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--size", type=int, default=2048, choices=(128, 256, 512, 1024, 2048, 4096))
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    source = workspace / "02_material_input"
    output = workspace / MATERIAL_DIR
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("Expected a nonempty extracted material manifest")
    output.mkdir(parents=True, exist_ok=True)
    virtual_dir = MATERIAL_DIR.relative_to("addon/materials").as_posix()
    for stem, entry in manifest.items():
        if not STEM.fullmatch(stem):
            raise ValueError(f"Invalid output material stem: {stem}")
        tint = entry["linear_color"]
        if "image" in entry:
            if entry["image"] != f"{stem}.image":
                raise ValueError(f"Unexpected material input filename: {stem}")
            original = (source / entry["image"]).read_bytes()
            if hashlib.sha256(original).hexdigest() != entry["sha256"]:
                raise ValueError(f"Source image hash mismatch: {stem}")
            with Image.open(BytesIO(original)) as decoded:
                image = decoded.convert("RGB").resize((args.size, args.size), Image.Resampling.LANCZOS)
            if tint != [1.0, 1.0, 1.0]:
                lookup = [
                    linear_to_srgb(srgb_to_linear(value) * channel)
                    for channel in tint for value in range(256)
                ]
                image = image.point(lookup)
        else:
            image = Image.new("RGB", (8, 8), tuple(linear_to_srgb(x) for x in tint))
        (output / f"{stem}.vtf").write_bytes(build_vtf(image))
        nocull = '\t"$nocull" "1"\n' if entry["two_sided"] else ""
        (output / f"{stem}.vmt").write_text(
            f'"VertexLitGeneric"\n{{\n\t"$basetexture" "{virtual_dir}/{stem}"\n{nocull}}}\n',
            encoding="ascii",
        )
    print(f"Built {len(manifest)} VTF/VMT pairs in {output}")


if __name__ == "__main__":
    main()
