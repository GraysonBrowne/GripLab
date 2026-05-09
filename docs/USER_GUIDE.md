# GripLab User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Importing Data](#importing-data)
3. [Managing Datasets](#managing-datasets)
4. [Settings](#settings)
5. [Plotting](#plotting)
6. [Plot Settings](#plot-settings)
7. [Tips and Tricks](#tips-and-tricks)

---

## Getting Started

### Installation
GripLab is available as a standalone executable — no installation required.

1. Navigate to the [GitHub repository](https://github.com/GraysonBrowne/GripLab)
2. Click **Releases** and download the executable from the **Assets** section
3. Move the executable to a dedicated folder — GripLab generates a log file and config file alongside the executable over time, so keeping it in its own folder helps stay organized

### Launching the App
Double-click the executable to launch. A terminal window will open — this is the local server that hosts the app. GripLab will then open in your web browser automatically.

> **Important:** Keep the terminal window open. It is the local server running the app. Closing it will stop the app from responding.

The terminal also displays logging information and is a useful reference if something goes wrong.

---

## Importing Data

Click **Import Data** in the sidebar to open a file selection dialog.

- Supported formats: `.mat` (MATLAB) and `.dat` / `.txt` (ASCII)
- All TTC data formats are supported
- Multiple files can be selected and imported at once

Once imported, each dataset appears in the data table with its filename as the default name and an auto-assigned node color.

---

## Managing Datasets

### Renaming a Dataset
Click directly on the dataset name in the table to edit it inline.

### Changing Node Color
Click the colored cell next to a dataset name. This opens the **Data Info** tab in the sidebar. Alternatively, navigate to the **Data Info** tab and select the dataset from the dropdown.

From the Data Info tab you can update:
- **Name** — display name for the dataset
- **Node Color** — color used for this dataset in all plots
- **Tire ID** — tire identifier
- **Rim Width** — rim width
- **Notes** — any additional notes

Click **Update** to save changes.

### Removing a Dataset
Click the trash icon next to a dataset in the table. A confirmation dialog will appear before removal.

---

## Settings

Open settings by clicking the **Settings** button in the header.

| Setting | Description |
|---|---|
| **Theme** | Light (`default`) or dark. Takes effect on next launch. |
| **Color Sequence** | The order of auto-assigned node colors as datasets are imported. |
| **Demo Mode** | Obfuscates dataset names and axis values — useful for demonstrations where TTC data should not be displayed publicly. |
| **Unit System** | USCS or Metric (see below). |
| **Sign Convention** | SAE, Adapted SAE, ISO, or Adapted ISO. |
| **Data Directory** | Default directory for the file import dialog. |

### Unit Systems

| Channel Type | USCS | Metric |
|---|---|---|
| Force | lbf | N |
| Moment | in·lbf | N·m |
| Length | in | cm |
| Pressure | psi | kPa |
| Speed | mph | km/h |
| Temperature | °F | °C |

### Sign Conventions
For a full description of the available sign conventions, see **Help → Sign Convention**.

---

## Plotting

### Plot Types
GripLab supports four plot types, selectable from the **Plot Data** tab:

- **2D** — Standard scatter plot (X vs Y)
- **2D Color** — Scatter plot with a third channel mapped to marker color
- **3D** — Three-axis scatter plot
- **3D Color** — Three-axis scatter plot with a fourth channel mapped to marker color

### Channel Selection
Use the axis dropdowns to select which channel to plot on each axis. Available channels are populated from the imported datasets.

### Downsample Factor
The downsample factor controls how many data points are plotted. A factor of `n` plots every nth node.

- Higher factor → fewer points → faster, more responsive app
- Factor of `1` → all points plotted

Start with a high downsample factor when first exploring a dataset, then reduce it as you narrow in on specific regions of interest.

### Command Channels
Command channels (`CmdSA`, `CmdFZ`, `CmdIA`, `CmdP`, `CmdV`) are automatically generated on import. They represent the nearest target command value for each data point based on the run guide.

Use the command channel selectors to filter the dataset by specific test conditions — for example, viewing only data at a specific pressure, load, or inclination angle. Multiple command channels can be active simultaneously.

### Overlaying Datasets
Multiple datasets can be selected in the table at once and plotted together. Each dataset retains its assigned node color. Hover over a point to see which dataset it belongs to and its channel values.

---

## Plot Settings

Click the **⚙** icon next to the Plot button to open plot settings.

| Setting | Description |
|---|---|
| **Title** | Custom plot title. Defaults to the tire ID if all datasets share the same ID, or a channel description if they differ. |
| **Subtitle** | Descriptive subtitle, auto-populated with the active command channel conditions. |
| **X / Y / Z / Color Labels** | Custom axis labels. Defaults to the standard channel name and unit. |
| **Color Map** | Color scale for color plots. Options: Jet, Inferno, Viridis. |
| **Font Size** | Axis and label font size. |
| **Marker Size** | Size of scatter plot markers. |
| **Marker Opacity** | Opacity of marker fill. Reduce to see overlapping points more clearly. |

---

## Tips and Tricks

- **Start coarse, refine later.** Use a high downsample factor when first exploring data, then reduce it once you've identified the region or conditions of interest.

- **3D plots handle more points.** Due to how Plotly renders 3D vs 2D, you can use a lower downsample factor on 3D plots without significantly impacting responsiveness. That said, 3D plots are best suited for data exploration — static 3D plots are difficult to interpret in reports.

- **Color plots work best with a single dataset.** When overlaying multiple datasets on a color plot, the color axis applies to all datasets combined, making it difficult to distinguish between them. For multi-dataset comparisons, stick to standard 2D plots.

- **Hide the sidebar** using the collapse button (☰) to give the plot more screen space.

- **Download plots** using the camera icon in the plot toolbar to save a PNG image.

- **Do not refresh the page or click the GripLab logo.** This is a known issue — refreshing the browser will crash the local server and require restarting the app.
