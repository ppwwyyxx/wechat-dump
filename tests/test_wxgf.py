#!/usr/bin/env python3
"""Unit tests for WXGF decoding with ffmpeg."""

import os
import sys
import shutil
import pytest
from io import BytesIO
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wechat.wxgf import (
    decode_wxgf_with_ffmpeg,
    is_wxgf_buffer,
)



# Path to the test WXGF file
TEST_WXGF_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "WXGFDecoder", "app", "src", "main", "res", "raw", "test_wxgf.jpg"
)


# Fixtures
@pytest.fixture(scope="module")
def has_ffmpeg():
    """Check if ffmpeg and ffprobe are available."""
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


@pytest.fixture(scope="module")
def has_test_file():
    """Check if test WXGF file exists."""
    return os.path.exists(TEST_WXGF_FILE)


@pytest.fixture(scope="module")
def test_wxgf_data(has_test_file):
    """Load test WXGF file data."""
    if not has_test_file:
        pytest.skip("Test WXGF file not available")
    with open(TEST_WXGF_FILE, 'rb') as f:
        return f.read()


def test_is_wxgf_buffer():
    """Test is_wxgf_buffer function."""
    assert is_wxgf_buffer(b'wxgf\x00\x00\x00') is True
    assert is_wxgf_buffer(b'\x89PNG\r\n\x1a\n') is False
    assert is_wxgf_buffer(b'') is False
    assert is_wxgf_buffer(b'abc') is False


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="ffmpeg/ffprobe not available"
)
def test_decode_wxgf_with_ffmpeg_success(test_wxgf_data):
    """Test successful WXGF decoding with ffmpeg."""
    data = test_wxgf_data

    # Decode the WXGF file
    result = decode_wxgf_with_ffmpeg(data)

    # Should return PNG bytes (starts with PNG signature)
    assert result is not None, "Decoding should succeed"
    assert isinstance(result, bytes)
    assert result.startswith(b'\x89PNG'), "Decoded output should be a PNG file"

    # PNG should have reasonable size
    assert len(result) > 100, "PNG should have reasonable size"

    img = Image.open(BytesIO(result))
    assert img.size == (1920, 1080), f"Expected image size (1920, 1080), got {img.size}"


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="ffmpeg/ffprobe not available"
)
def test_decode_wxgf_with_ffmpeg_invalid_data():
    """Test ffmpeg decoding with invalid data."""
    # Not a WXGF file
    result = decode_wxgf_with_ffmpeg(b'\x89PNG\r\n\x1a\n')
    assert result is None

    # WXGF header but no valid HEVC data
    result = decode_wxgf_with_ffmpeg(b'wxgf\x00\x00\x00\x01\x00\x00')
    assert result is None


def test_decode_wxgf_without_ffmpeg(test_wxgf_data):
    """Test decoding when ffmpeg is not available."""
    data = test_wxgf_data

    # Use non-existent ffmpeg paths
    result = decode_wxgf_with_ffmpeg(data, ffmpeg="nonexistent_ffmpeg", ffprobe="nonexistent_ffprobe")
    assert result is None
