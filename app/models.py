# app/models.py
"""Page and subplot models for GripLab tab management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import panel as pn

if TYPE_CHECKING:
    from ui.components import (
        PlotControlWidgets,
        PlotSettingsWidgets,
        TimeSeriesControlWidgets,
        TimeSeriesSettingsWidgets,
    )


@dataclass
class SubplotConfig:
    """Configuration for a single time series subplot row."""

    channels: list[str] = field(default_factory=list)
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
    name: str
    controls: TimeSeriesControlWidgets
    settings: TimeSeriesSettingsWidgets
    pane: pn.pane.Plotly
    subplots: list[list[SubplotConfig]] = field(default_factory=list)
    tab_content: Any = field(default=None)


PageType = ScatterPage | TimeSeriesPage
