# STL Batch Processing

This project is a Python-based tool to automate the processing of multiple STL files for 3D printing, including slicing them into G-code and estimating print times. It supports multiple printers, organizes print jobs into batches, and calculates the estimated printing times for individual and combined batches.

## Features
- **Automatic STL Processing**: Automates the slicing of STL files using PrusaSlicer.
- **Batch Packing**: Efficiently packs STL files into batches to minimize print times using the `rectpack` library.
- **Print Time Estimation**: Estimates print time for each STL and displays total print time for each batch.
- **Support for Multiple Printers**: Configurable to handle different printers (e.g., MK3S, Mini) with different build plate sizes and slicing configurations.

## Requirements
- **Python 3.8+**
- **Dependencies**:
  - `rectpack`
  - `numpy-stl`
- **PrusaSlicer**: Make sure PrusaSlicer is installed and accessible. Update the path to the slicer in `main.py` as needed.

## Installation
1. Clone the repository:
   ```sh
   git clone <repository_url>
   ```
2. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Update the `prusa_slicer_path` variable in `main.py` to point to your PrusaSlicer installation.

## Usage
1. Place your STL files in the `stl/` directory, organized in subdirectories for each printer type (e.g., `MK3S`, `Mini`).
2. Run the script:
   ```sh
   python main.py
   ```
3. The script will generate G-code files for each STL and calculate the estimated printing times.

## Configuration
- **Printer Configurations**: Printer settings (e.g., slicing profiles) can be modified in the `config_map` in `main.py`. Add or update configurations as needed for additional printers.
- **STL Padding**: Modify the `padding` parameter in `calculate_bounding_box()` in `utils.py` to adjust the extra space added around each STL.

## Project Structure
- `main.py`: Main script to process STL files and organize them into print batches.
- `utils.py`: Utility functions for handling STL files, calculating bounding boxes, and displaying print times.
- `stl/`: Directory to hold the STL files, organized by printer types.

## Limitations
- The script currently assumes that the G-code output will be generated successfully. Error handling for slicer failures needs improvement.
- STL file dimensions are loaded entirely into memory, which may be problematic for very large files.

## License
This project is licensed under the MIT License.
