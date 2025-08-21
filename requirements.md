# GripLab Requirements Document

## 1. Introduction
The goal of this project is to develop an open-source Python application to help Formula SAE/Formula Student teams efficiently process and analyze tire test data, fit tire models, and visualize results. The app should lower the barrier for students to use TTC data in vehicle simulations by providing clear, accessible tools for data handling and modeling.  

## 2. Functional Requirements

### 2.1 Data Import
- Must support importing TTC data format files.  
- Should allow importing from CSV and other common structured data files.  
- Should validate file format and provide meaningful error messages.  

### 2.2 Data Processing and Manipulation
- Filter, smooth, and normalize raw TTC data.  
- Select and subset data (e.g., specific loads, pressures, slip ranges).  
- Perform unit conversions where applicable.  
- Handle missing or corrupt data gracefully.  

### 2.3 Visualization
- **2D Plots:**  
  - Tire forces vs. slip angle, slip ratio, normal load, etc.  
  - Overlay experimental data and fitted model results.  
- **3D Plots:**  
  - Surface plots (e.g., lateral force vs. slip angle & normal load).  
  - Interactive rotation and zoom functionality.  

### 2.4 Model Fitting
- Fit common tire models (e.g., Pacejka “Magic Formula,” polynomial fits).  
- Provide parameter estimation routines (curve fitting, optimization).  
- Allow users to export fitted model parameters.  
- Display goodness-of-fit metrics (R², RMSE, etc.).  

### 2.5 User Interface (Phase 2 / Stretch Goal)
- Initial release can be CLI (command-line interface) or notebook-based.  
- Future versions may include a lightweight GUI (e.g., PyQt, Dash, or Streamlit).  

## 3. Non-Functional Requirements
- Open-source license (MIT recommended).  
- Written in Python 3.x.  
- Should use widely adopted libraries (NumPy, pandas, matplotlib, SciPy, Plotly/Mayavi for 3D).  
- Documentation: clear user guide and examples (e.g., Jupyter notebooks).  
- Modular codebase to allow easy contributions from the community.  

## 4. Out of Scope
- The app will not distribute TTC data directly (per TTC agreement).  
- Vehicle-level simulation is not included (students can export fitted models for use in external simulation tools).  

## 5. Future Enhancements (Optional)
- Support for additional tire models (e.g., MF-Tyre, Dugoff).  
- Automated report generation (plots + parameters).  
- Web-based interface for easier accessibility.  
- Integration with vehicle simulation software (CarSim, Adams, etc.).  
