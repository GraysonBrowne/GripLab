# GripLab Requirements Document

## 1. Introduction
The goal of this project is to develop an open-source Python application to help Formula SAE/Formula Student teams efficiently process and analyze tire test data, fit tire models, and visualize results. The app should lower the barrier for students to use TTC data in vehicle simulations by providing clear, accessible tools for data handling and modeling.  

## 2. Functional Requirements

### 2.1 Data Import
- Must support importing TTC data format files.  (.mat/.dat)
- Should allow importing from CSV/TXT and other common structured data files.  
- Should validate file format and provide meaningful error messages.  

### 2.2 Data Processing and Manipulation
- Filter, smooth, and normalize raw data.  
- Select and subset data (e.g., specific loads, pressures, slip ranges).  
- Perform unit/coordinate system conversions where applicable.  
- Handle missing or corrupt data gracefully.  
- Combine datasets.
- Parse/remove unwanted data points.
- Custom math channels.

### 2.3 Visualization
- **2D Plots:**  
  - Tire forces vs. slip angle, slip ratio, normal load, etc.  
  - Overlay experimental data and fitted model results.  
  - Colorbar option for third variable.
  - Set marker size, color, and downsample rate.
  - Find slope and peak value of model plots.
  - Subplots and multichannel overlays. 
- **3D Plots:**  
  - Surface plots (e.g., lateral force vs. slip angle & normal load).  
  - Interactive rotation and zoom functionality.  

### 2.4 Model Fitting
- Fit common tire models (PAC2002, MF6.2).  
- Provide parameter estimation routines (curve fitting, optimization).  
- Allow users to export fitted model parameters.  
- Display goodness-of-fit metrics (R², RMSE, etc.).  

### 2.5 User Interface
- Jypter notebook for function testing  and examples.  
- GUI built using Panel API and compiled to an EXE with Pyinstaller.  

## 3. Non-Functional Requirements
- Open-source license (MIT).  
- Written in Python 3.12.  
- Should use widely adopted libraries (NumPy, pandas, matplotlib, SciPy, Plotly/Mayavi for 3D).  
- Documentation: clear user guide and examples (e.g., Jupyter notebooks).  
- Modular codebase to allow easy contributions from the community.  

## 4. Out of Scope
- The app will not distribute TTC data directly (per TTC agreement).  
- Vehicle-level simulation is not included (students can export fitted models for use in external simulation tools).  

## 5. Future Enhancements (Optional)
- Support for additional tire models (e.g., brush, rigid-ring).  
- Automated report generation (plots + parameters).  
- Web-based interface for easier accessibility.  
- Integration with vehicle simulation software (CarSim, Adams, etc.).  
