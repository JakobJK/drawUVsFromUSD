import skia
import argparse
from typing import NamedTuple

class Settings(NamedTuple):
    path: str
    output_path: str
    size: int
    internal_edges: skia.Paint
    border_edges: skia.Paint
    front_facing: skia.Paint
    back_facing: skia.Paint

def get_settings():
    parser = argparse.ArgumentParser(description="Debug argparse")

    parser.add_argument("--path", type=str, default="./example.usd", help="Path to the USD file")
    parser.add_argument("--output_path", type=str, default="output.png", help="Output file path")
    parser.add_argument("-s", "--size", type=int, default=2048, help="Image size")

    settings = parser.parse_args()

    settings.internal_edges = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(0, 0, 0, 1),
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=2,
    )

    settings.border_edges = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(1, 1, 1, 1),
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=4,
    )

    settings.front_facing = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(0, 0, 1, 0.5),
        Style=skia.Paint.kFill_Style,
    )

    settings.back_facing = skia.Paint(
        AntiAlias=True,
        Color=skia.Color4f(1, 0, 0, 0.5),
        Style=skia.Paint.kFill_Style,
    )

    return settings
