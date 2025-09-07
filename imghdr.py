"""Recognize image file formats based on their first few bytes."""

__all__ = ['what']

def what(file, h=None):
    """Detect the image file format based on its first few bytes."""
    if h is None:
        with open(file, 'rb') as f:
            h = f.read(32)
    
    for tf in tests:
        res = tf(h)
        if res:
            return res
    return None

# Image format tests
def test_jpeg(h):
    """JPEG data in JFIF or Exif format"""
    if h[6:10] in (b'JFIF', b'Exif'):
        return 'jpeg'

def test_png(h):
    if h.startswith(b'\211PNG\r\n\032\n'):
        return 'png'

def test_gif(h):
    """GIF ('87 and '89 variants)"""
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'

def test_tiff(h):
    """TIFF (can be in Motorola or Intel byte order)"""
    if h[:2] in (b'MM', b'II'):
        return 'tiff'

def test_bmp(h):
    """BMP (bitmap)"""
    if h.startswith(b'BM'):
        return 'bmp'

def test_webp(h):
    """WebP image"""
    if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'

tests = [
    test_jpeg,
    test_png,
    test_gif,
    test_tiff,
    test_bmp,
    test_webp,
]