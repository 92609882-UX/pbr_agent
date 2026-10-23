# Texture Map Generator

## Description
This tool generates various texture maps from input images, including Normal maps, Ambient Occlusion (AO) maps, and Roughness maps. It can be operated via a Command-Line Interface (CLI) for batch processing or single image processing, and also offers an optional Graphical User Interface (GUI) for easier input selection.

## Features
- Generation of Normal maps (from height maps derived from input images).
- Generation of Ambient Occlusion (AO) maps (from height maps).
- Generation of Roughness maps (using 'inverted_grayscale' or 'local_variance' methods).
- Command-Line Interface for processing:
    - Single image files.
    - All supported image files within a specified folder.
- Optional GUI (`--gui` flag) for interactive selection of:
    - Input image file.
    - Input folder.
    - Output directory.
- Customizable parameters for each map type via CLI (e.g., strength for normal maps, samples for AO).

## Dependencies
The tool requires the following Python libraries:
- **Pillow**: For image loading and saving. (`pip install Pillow`)
- **NumPy**: For numerical operations on image arrays. (`pip install numpy`)
- **SciPy**: For specific filters like Sobel (for normal maps) and generic filters (for local variance roughness). (`pip install scipy`)
- **Tkinter**: For the optional GUI. 
    - Tkinter is usually part of Python's standard library on Windows and macOS.
    - On Linux, it may need to be installed separately, e.g., `sudo apt-get install python3-tk`.

## Usage (CLI)

### Basic Syntax
```bash
python main.py [input_path_or_folder] [options]
```

### GUI Mode
To launch the graphical interface for selecting input and output:
```bash
python main.py --gui [options]
```
If options like `-o` are provided with `--gui`, they will be used; otherwise, the GUI will prompt for them if necessary.

### Key Options
- `input_path_or_folder`: Path to a single image file or a folder containing images. This is required if not using the `--gui` flag.
- `--gui`: Launch the graphical user interface for selecting input (file or folder) and output directory.
- `-o <output_directory>`, `--output_dir <output_directory>`: Specify the directory where generated maps will be saved.
    - Default for single file input: The same directory as the input file.
    - Default for folder input: The input folder itself.
    - If used with `--gui`, this pre-selects the output directory.
- `--all_maps`: Generate all available map types (Normal, AO, Roughness). This is the default behavior if no specific map type (`-n`, `-a`, `-r`) is chosen.
- `-n`, `--normal`: Generate a Normal map.
- `-a`, `--ao`: Generate an Ambient Occlusion map.
- `-r`, `--roughness`: Generate a Roughness map.

### Map Generation Parameters (Examples)
These parameters are for CLI usage. The GUI mode currently uses default values for these.
- `--normal_strength <value>`: Adjust the strength of the normal map effect (e.g., `1.0`, `2.5`). Default: `1.0`.
- `--ao_samples <value>`: Set the number of samples for AO calculation (e.g., `16`, `32`). Higher values are slower but may produce smoother results. Default: `16`.
- `--ao_radius <value>`: Set the sampling radius for AO. Default: `10.0`.
- `--roughness_method <method_name>`: Choose the method for roughness map generation.
    - Options: `inverted_grayscale` (default), `local_variance`.
- `--roughness_ws <value>`: Window size for the 'local_variance' roughness method (e.g., `3`, `5`). Default: `3`.
- `--roughness_scale <value>`: Detail scale for 'local_variance' method. Default: `1.0`.


### Example CLI Commands
1.  **Process a single image and save all maps to a specific output directory:**
    ```bash
    python main.py path/to/your/image.png -o path/to/output/ --all_maps
    ```

2.  **Process all images in a folder, generate Normal and Roughness maps, and save them to `output_maps` (relative to current dir):**
    ```bash
    python main.py path/to/your/folder/ -o output_maps --normal --roughness --roughness_method local_variance
    ```

3.  **Launch the GUI, and if an output directory is specified, use it:**
    ```bash
    python main.py --gui -o path/to/preferred/output/
    ```
    If `-o` is omitted, the GUI will prompt for an output directory after input selection.

## Output Maps
- **Normal Map (`*_normal.ext`):** Tangent space normal map, typically used to add surface detail in 3D rendering. Encodes normal vector components in RGB channels.
- **Ambient Occlusion Map (`*_ao.ext`):** Grayscale map simulating soft shadows in crevices and occluded areas, enhancing perceived depth.
- **Roughness Map (`*_roughness.ext`):** Grayscale map defining how rough or smooth a surface is, influencing how light reflects.

Generated maps are saved in the specified output directory with suffixes appended to the original filename (e.g., `myimage_normal.png`).
