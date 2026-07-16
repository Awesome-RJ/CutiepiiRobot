"""
Pillow Compatibility Helper
Provides backward compatibility for deprecated Pillow methods
"""

from PIL import ImageFont
from typing import Tuple


def get_text_size(font: ImageFont.FreeTypeFont, text: str) -> Tuple[int, int]:
    """
    Get text size using the appropriate method for the Pillow version.
    
    In Pillow 10.0+, getsize() is deprecated in favor of getbbox().
    This function provides compatibility for both versions.
    
    Args:
        font: PIL ImageFont object
        text: Text to measure
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        # Try the new method first (Pillow 10.0+)
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return (width, height)
    except AttributeError:
        # Fallback to deprecated method (Pillow < 10.0)
        return font.getsize(text)


def get_text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    """
    Get text width only.
    
    Args:
        font: PIL ImageFont object
        text: Text to measure
    
    Returns:
        Width in pixels
    """
    return get_text_size(font, text)[0]


def get_text_height(font: ImageFont.FreeTypeFont, text: str) -> int:
    """
    Get text height only.
    
    Args:
        font: PIL ImageFont object
        text: Text to measure
    
    Returns:
        Height in pixels
    """
    return get_text_size(font, text)[1]


# Monkey-patch the ImageFont.FreeTypeFont class for convenience
# This allows existing code to work without modification
def _patch_font_getsize():
    """
    Monkey-patch ImageFont.FreeTypeFont to add a compatible getsize method.
    This is called automatically on import.
    """
    try:
        # Check if getsize is already available and working
        test_font = ImageFont.truetype if hasattr(ImageFont, 'truetype') else None
        if test_font:
            # Only patch if getsize doesn't exist or is deprecated
            if not hasattr(ImageFont.FreeTypeFont, 'getsize') or \
               hasattr(ImageFont.FreeTypeFont, 'getbbox'):
                # Add a compatibility wrapper
                original_getsize = getattr(ImageFont.FreeTypeFont, 'getsize', None)
                
                def compat_getsize(self, text, *args, **kwargs):
                    """Compatibility wrapper for getsize"""
                    try:
                        if original_getsize:
                            return original_getsize(self, text, *args, **kwargs)
                    except:
                        pass
                    # Use getbbox as fallback
                    bbox = self.getbbox(text, *args, **kwargs)
                    return (bbox[2] - bbox[0], bbox[3] - bbox[1])
                
                # Only patch if needed
                if not original_getsize or callable(original_getsize):
                    ImageFont.FreeTypeFont.getsize_compat = compat_getsize
    except Exception:
        # Silently fail if patching is not possible
        pass


# Automatically patch on import
_patch_font_getsize()


__all__ = ['get_text_size', 'get_text_width', 'get_text_height']
