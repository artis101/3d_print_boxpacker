import os
import subprocess
import re
from functools import reduce
from stl import mesh
from rectpack import newPacker, SORT_RATIO

# Configuration
script_dir = os.path.dirname(os.path.realpath(__file__))
stl_dir = os.path.join(script_dir, "stl")
prusa_slicer_path = "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"  # Adjust if needed

# Map each subdirectory to its corresponding config.ini file
config_map = {
    "Black": "black.ini",
    "Orange": "orange.ini",
    # Add more mappings as needed
}

# Regular expression to find the estimated print time
black_time_regex = re.compile(
    r"; estimated printing time \(silent mode\) = (\d+h \d+m \d+s)"
)
orange_time_regex = re.compile(
    r"; estimated printing time \(normal mode\) = (\d+h \d+m \d+s)"
)

subdir_map = {
    "Black": black_time_regex,
    "Orange": orange_time_regex,
}


# Function to process STL files in a subdirectory
def process_stl_files(subdir, config_file):
    print_times = []
    subdir_path = os.path.join(stl_dir, subdir)
    config_file_path = os.path.join(script_dir, config_file)

    for stl_file in os.listdir(subdir_path):
        if stl_file.endswith(".stl"):
            stl_file_name = os.path.splitext(stl_file)[0]

            stl_file_path = os.path.join(subdir_path, stl_file)
            gcode_file_path = os.path.join(subdir_path, stl_file_name + "_gcode.gcode")

            # if gcode file exists skip
            if not os.path.exists(gcode_file_path):
                # Run PrusaSlicer
                subprocess.run(
                    [
                        prusa_slicer_path,
                        "--load",
                        config_file_path,
                        "--export-gcode",
                        stl_file_path,
                    ],
                    check=True,
                )

            # Extract print time from G-code
            with open(gcode_file_path, "r") as gcode_file:
                for line in gcode_file:
                    time_regex = subdir_map[subdir]

                    if not time_regex:
                        print(f"Time regex not found for {subdir}")
                        break

                    match = time_regex.search(line)

                    if match:
                        print_times.append((stl_file, match.group(1)))
                        break

            # Remove G-code file
            # os.remove(gcode_file_path)

    # parse print times by STL file and turn string of `h m s` into seconds
    print_times = [
        (
            stl_file,
            int(reduce(lambda x, y: x * 60 + y, map(int, re.findall(r"\d+", time)))),
        )
        for stl_file, time in print_times
    ]

    return print_times


# Main process
all_print_times = []
for current_subdir, config in config_map.items():
    print_times = process_stl_files(current_subdir, config)
    all_print_times.extend(
        [(current_subdir, stl_file, time) for stl_file, time in print_times]
    )

    print(f"Processed {len(print_times)} files in {current_subdir}")

    # Group print times per subdirectory
    subdir_print_times = {}
    for current_subdir, stl_file, time in all_print_times:
        if current_subdir not in subdir_print_times:
            subdir_print_times[current_subdir] = []

        subdir_print_times[current_subdir].append([stl_file, time])

    # sort print times by time
    for subdir, print_times in subdir_print_times.items():
        print_times.sort(key=lambda x: x[1], reverse=True)

    # Print header for each subdirectory
    for subdir, print_times in subdir_print_times.items():
        if current_subdir != subdir:
            continue

        print(
            "{:<30} {:<20} {:<10}".format("STL File", "Color", "Estimated Print Time")
        )
        print("-" * 80)
        for stl_file, time in print_times:
            days = time // (24 * 3600)
            time %= 24 * 3600
            hours = time // 3600
            time %= 3600
            minutes = time // 60
            print(
                "{:<30} {:<20} {:02d} days {:02d} hours {:02d} minutes".format(
                    stl_file, subdir, days, hours, minutes
                )
            )
        print("-" * 80)
        print("\n")


def calculate_bounding_box(stl_path, padding=0.0):
    # Load the STL file
    stl_mesh = mesh.Mesh.from_file(stl_path)

    # Find the max and min points of the mesh in each dimension
    min_x, max_x = stl_mesh.x.min(), stl_mesh.x.max()
    min_y, max_y = stl_mesh.y.min(), stl_mesh.y.max()
    min_z, max_z = stl_mesh.z.min(), stl_mesh.z.max()

    # Calculate the bounding box dimensions
    length = max_x - min_x
    width = max_y - min_y
    height = max_z - min_z

    # Add padding
    length += padding
    width += padding
    height += padding

    return length, width, height


# Example usage
stl_dimensions = {}

subdirectories = ["Black", "Orange"]
for subdir in subdirectories:
    stl_dimensions[subdir] = []
    subdir_path = os.path.join("stl", subdir)  # Adjust path as needed
    for stl_file in os.listdir(subdir_path):
        if stl_file.endswith(".stl"):
            stl_path = os.path.join(subdir_path, stl_file)
            length, width, _ = calculate_bounding_box(stl_path, padding=20.0)
            stl_dimensions[subdir].append((stl_file, (length, width)))

# Printer build plate sizes (length, width) in mm
build_plate_sizes = {"Black": (250, 210), "Orange": (180, 180)}

# Add each rectangle (length, width) to the packer
for subdir, dimensions in stl_dimensions.items():
    # Create a new packer
    packer = newPacker(sort_algo=SORT_RATIO)

    for stl_file, (length, width) in dimensions:
        packer.add_rect(length, width, rid=stl_file)
        build_plate_size = build_plate_sizes[subdir]
        packer.add_bin(*build_plate_size, bid=subdir)

    # Pack the rectangles into the minimum number of bins
    packer.pack()

    # Print the resulting bins
    for i, rect in enumerate(packer):
        print(f"Bin {i + 1}: {rect.width}x{rect.height}")

        for stl_file in [list(l)[::-1] for l in rect.rect_list()]:
            print(f"  {stl_file}")
        print()
