from PIL import Image

from ocr_engine import inspect_image_quality


def test_ocr_quality_accepts_supported_resolution(
    tmp_path,
):
    image_path = tmp_path / "accepted.png"

    Image.new(
        "RGBA",
        (1447, 2048),
        (255, 255, 255, 255),
    ).save(image_path)

    quality = inspect_image_quality(
        str(image_path)
    )

    assert quality["status"] == "accepted"
    assert quality["requires_review"] is False

    assert quality["input"] == {
        "format": "PNG",
        "width": 1447,
        "height": 2048,
        "short_edge": 1447,
        "long_edge": 2048,
        "pixel_count": 2963456,
        "mode": "RGBA",
        "dpi": None,
    }

    assert quality["warnings"] == []


def test_ocr_quality_marks_low_resolution_for_review(
    tmp_path,
):
    image_path = tmp_path / "review.png"

    Image.new(
        "RGBA",
        (1239, 1754),
        (255, 255, 255, 255),
    ).save(image_path)

    quality = inspect_image_quality(
        str(image_path)
    )

    assert quality["status"] == "review"
    assert quality["requires_review"] is True

    assert quality["input"]["width"] == 1239
    assert quality["input"]["height"] == 1754
    assert quality["input"]["mode"] == "RGBA"

    assert quality["warnings"] == [
        {
            "code": "low_image_resolution",
            "message": (
                "Image resolution may be "
                "insufficient for reliable OCR"
            ),
        }
    ]

def test_jpeg_quality_accepts_200_dpi_dimensions(
    tmp_path,
):
    image_path = tmp_path / "accepted.jpeg"

    Image.new(
        "RGB",
        (1652, 2338),
        (255, 255, 255),
    ).save(
        image_path,
        format="JPEG",
        quality=85,
    )

    quality = inspect_image_quality(
        str(image_path)
    )

    assert quality["status"] == "accepted"
    assert quality["requires_review"] is False

    assert quality["input"]["format"] == "JPEG"
    assert quality["input"]["width"] == 1652
    assert quality["input"]["height"] == 2338
    assert quality["input"]["mode"] == "RGB"
    assert quality["warnings"] == []


def test_jpeg_quality_marks_150_dpi_dimensions_for_review(
    tmp_path,
):
    image_path = tmp_path / "review.jpg"

    Image.new(
        "RGB",
        (1239, 1754),
        (255, 255, 255),
    ).save(
        image_path,
        format="JPEG",
        quality=85,
    )

    quality = inspect_image_quality(
        str(image_path)
    )

    assert quality["status"] == "review"
    assert quality["requires_review"] is True

    assert quality["input"]["format"] == "JPEG"
    assert quality["input"]["width"] == 1239
    assert quality["input"]["height"] == 1754
    assert quality["input"]["mode"] == "RGB"

    assert quality["warnings"] == [
        {
            "code": "low_image_resolution",
            "message": (
                "Image resolution may be "
                "insufficient for reliable OCR"
            ),
        }
    ]


def test_jpeg_quality_uses_exif_normalized_dimensions(
    tmp_path,
):
    image_path = tmp_path / "rotated.jpg"

    source = Image.new(
        "RGB",
        (2479, 3508),
        (255, 255, 255),
    )
    stored_pixels = source.transpose(
        Image.Transpose.ROTATE_90
    )

    exif = Image.Exif()
    exif[274] = 6

    stored_pixels.save(
        image_path,
        format="JPEG",
        quality=85,
        exif=exif,
    )

    quality = inspect_image_quality(
        str(image_path)
    )

    assert quality["status"] == "accepted"
    assert quality["requires_review"] is False
    assert quality["input"]["width"] == 2479
    assert quality["input"]["height"] == 3508
    assert quality["input"]["short_edge"] == 2479
    assert quality["input"]["long_edge"] == 3508
