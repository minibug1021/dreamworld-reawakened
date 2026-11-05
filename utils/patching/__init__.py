"""Patches to the original SWFs for various bugfixes or improvements.

- substitutions.py: find-and-replace patches for JS/HTML/CSS.
- swf_patches.py: the ActionScript patches for the SWFs.
- ffdec.py: applies the above to the SWFs with ffdec and caches the results in patches/.
"""
from utils.patching.ffdec import get_patched_swf, prewarm
from utils.patching.substitutions import apply_substitutions
from utils.patching.swf_patches import SWF_PATHS

__all__ = ["SWF_PATHS", "apply_substitutions", "get_patched_swf", "prewarm"]
