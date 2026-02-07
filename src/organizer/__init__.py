"""
PS2 Texture Sorter - Organization System Package
Author: Dead On The Inside / JosephsDeadish

This package contains the organization/hierarchy system for sorting textures
into various folder structures based on different organization styles.
"""

from .organization_engine import OrganizationEngine
from .organization_styles import (
    SimsStyle,
    NeopetsStyle,
    FlatStyle,
    GameAreaStyle,
    AssetPipelineStyle,
    ModularStyle,
    MinimalistStyle,
    MaximumDetailStyle,
    CustomStyle,
    ORGANIZATION_STYLES
)

__all__ = [
    'OrganizationEngine',
    'SimsStyle',
    'NeopetsStyle',
    'FlatStyle',
    'GameAreaStyle',
    'AssetPipelineStyle',
    'ModularStyle',
    'MinimalistStyle',
    'MaximumDetailStyle',
    'CustomStyle',
    'ORGANIZATION_STYLES'
]
