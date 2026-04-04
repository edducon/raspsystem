"""Backend application package for the scheduling platform."""

import warnings

from pydantic.warnings import UnsupportedFieldAttributeWarning

# FastAPI composes request/response models during module import and currently emits this
# warning for camelCase aliases under Python 3.14, although the schemas still work correctly.
warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)
