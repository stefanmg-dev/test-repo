import numpy as np
from PIL import Image

import ocr_engine


class FakeReader:
    def __init__(self):
        self.received_image = None

    def readtext(
        self,
        image,
        detail,
        paragraph,
    ):
        self.received_image = image

        assert detail == 0
        assert paragraph is True

        return [
            "OCR result"
        ]


def run_with_fake_reader(
    monkeypatch,
    image_path,
):
    fake_reader = FakeReader()

    monkeypatch.setattr(
        ocr_engine,
        "reader",
        fake_reader,
    )

    result = ocr_engine.run_ocr(
        str(image_path)
    )

    return result, fake_reader.received_image


def assert_rgb_array(image_array):
    assert isinstance(
        image_array,
        np.ndarray,
    )

    assert image_array.dtype == np.uint8
    assert image_array.ndim == 3
    assert image_array.shape[2] == 3


def test_rgb_png_is_passed_as_three_channels(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "rgb.png"

    Image.new(
        "RGB",
        (20, 10),
        (255, 255, 255),
    ).save(image_path)

    result, image_array = run_with_fake_reader(
        monkeypatch,
        image_path,
    )

    assert result == "OCR result"
    assert_rgb_array(image_array)


def test_rgba_png_is_composited_to_rgb(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "rgba.png"

    Image.new(
        "RGBA",
        (20, 10),
        (255, 0, 0, 128),
    ).save(image_path)

    result, image_array = run_with_fake_reader(
        monkeypatch,
        image_path,
    )

    assert result == "OCR result"
    assert_rgb_array(image_array)

    assert tuple(
        image_array[0, 0]
    ) == (
        255,
        127,
        127,
    )


def test_grayscale_png_is_converted_to_rgb(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "grayscale.png"

    Image.new(
        "L",
        (20, 10),
        200,
    ).save(image_path)

    result, image_array = run_with_fake_reader(
        monkeypatch,
        image_path,
    )

    assert result == "OCR result"
    assert_rgb_array(image_array)

    assert tuple(
        image_array[0, 0]
    ) == (
        200,
        200,
        200,
    )


def test_jpeg_is_passed_as_three_channels(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "image.jpg"

    Image.new(
        "RGB",
        (20, 10),
        (255, 255, 255),
    ).save(
        image_path,
        format="JPEG",
    )

    result, image_array = run_with_fake_reader(
        monkeypatch,
        image_path,
    )

    assert result == "OCR result"
    assert_rgb_array(image_array)