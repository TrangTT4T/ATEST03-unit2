"""VisualComparison: compare two screenshots pixel by pixel and save what differs (Day 5: assertions).

Playwright for Python has no screenshot assertion, so this class does it with Pillow:

    comparison = VisualComparison(tmp_path)
    result = comparison.compare("products", actual_png, expected_png)
    assert result.ratio <= 0.001, result.message

A pixel "differs" when one of its colour channels moves by more than PIXEL_TOLERANCE (anti-aliasing
noise stays below it). The expected, actual and diff images are saved in the folder (the diff shows
the actual screenshot with every differing pixel in red) and attached to Allure.
"""
import io
from dataclasses import dataclass
from pathlib import Path

import allure
from PIL import Image, ImageChops


@dataclass
class ComparisonResult:
    ratio: float  # share of the pixels that differ, 0.0 - 1.0
    diff_path: Path
    message: str


class VisualComparison:
    PIXEL_TOLERANCE = 16  # 0-255 per channel

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    ############################################################################
    # Compare methods
    # Scope: Two screenshots > ratio of differing pixels, diff image
    ############################################################################
    def compare(self, name: str, actual_png: bytes, expected_png: bytes) -> ComparisonResult:
        """Compare ``actual_png`` with ``expected_png``; save and attach the three images.

        :param name: file name prefix, e.g. "products-page"
        :return: the share of differing pixels, the diff image and a readable message
        """
        actual = Image.open(io.BytesIO(actual_png)).convert("RGB")
        expected = Image.open(io.BytesIO(expected_png)).convert("RGB")
        size = (max(actual.width, expected.width), max(actual.height, expected.height))
        actual_padded, expected_padded = self._pad(actual, size), self._pad(expected, size)
        changed = ImageChops.difference(actual_padded, expected_padded).convert("L").point(self._is_changed)
        changed_pixels = sum(1 for value in changed.getdata() if value)
        ratio = changed_pixels / (size[0] * size[1])
        diff = actual_padded.copy()
        diff.paste((255, 0, 0), mask=changed)
        paths = {}
        for kind, image in (("expected", expected), ("actual", actual), ("diff", diff)):
            paths[kind] = self.folder / f"{name}-{kind}.png"
            image.save(paths[kind])
            allure.attach.file(str(paths[kind]), name=f"{name}: {kind}", attachment_type=allure.attachment_type.PNG)
        message = (f"{name}: {changed_pixels} of {size[0] * size[1]} pixels differ ({ratio:.2%}); "
                   f"size expected {expected.size}, actual {actual.size}; diff image: {paths['diff']}")
        return ComparisonResult(ratio=ratio, diff_path=paths["diff"], message=message)

    @staticmethod
    def _pad(image: Image.Image, size: tuple[int, int]) -> Image.Image:
        """The image on a white canvas of ``size``: two screenshots of different heights stay comparable."""
        canvas = Image.new("RGB", size, (255, 255, 255))
        canvas.paste(image, (0, 0))
        return canvas

    @classmethod
    def _is_changed(cls, value: int) -> int:
        return 255 if value > cls.PIXEL_TOLERANCE else 0
