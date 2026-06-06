# app/models.py
"""Page and subplot models for GripLab tab management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Union

import panel as pn

if TYPE_CHECKING:
    from ui.components import (
        PlotControlWidgets,
        PlotSettingsWidgets,
        TimeSeriesControlWidgets,
    )


@dataclass
class SubplotConfig:
    """Configuration for a single time series subplot row."""
    channels: List[str] = field(default_factory=list)
    label: str = ""


@dataclass
class ScatterPage:
    """State container for a scatter plot tab."""
    name: str
    controls: PlotControlWidgets
    settings: PlotSettingsWidgets
    pane: pn.pane.Plotly


@dataclass
class TimeSeriesPage:
    """State container for a time series tab."""
    name: str
    controls: TimeSeriesControlWidgets
    pane: pn.pane.Plotly
    subplots: List[SubplotConfig] = field(default_factory=list)


PageType = Union[ScatterPage, TimeSeriesPage]
