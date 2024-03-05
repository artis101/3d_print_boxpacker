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

time_regex = re.compile(
    r"; estimated printing time \(.*\) = (?:(\d+)d\s)?(?:(\d+)h\s)?(?:(\d+)m\s)?(?:(\d+)s)?"
)


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
                print_time_found = False

                for line in gcode_file:
                    match = time_regex.search(line)
                    if match:
                        days, hours, minutes, seconds = [
                            int(t) if t else 0 for t in match.groups()
                        ]
                        total_seconds = (
                            seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
                        )

                        print_times.append((stl_file, total_seconds))
                        print_time_found = True
                        break

                if not print_time_found:
                    raise Exception(f"Print time not found for {stl_file}")

            # Remove G-code file
            # os.remove(gcode_file_path)

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

        print("{:<35} {:<10} {:<20}".format("STL File", "Color", "Print Time"))
        print("-" * 80)
        for stl_file, time in print_times:
            days = time // (24 * 3600)
            time %= 24 * 3600
            hours = time // 3600
            time %= 3600
            minutes = time // 60
            print(
                "{:<35} {:<10} {:02d} days {:02d} hours {:02d} minutes".format(
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

prev_color = None

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
        print(f"Batch {i + 1} for {subdir}")
        # print(f"Bin {i + 1}: {rect.width}x{rect.height}")
        curr_color = rect.bid

        if prev_color != curr_color:
            prev_color = curr_color

            print("{:<35} {:<20}".format("STL File", "Print Time"))
            print("-" * 80)

        batch_print_time = 0

        for stl_file, _, _, _, _ in [list(l)[::-1] for l in rect.rect_list()]:
            print_time_list = [
                time for _, file, time in all_print_times if file == stl_file
            ]

            if not print_time_list:
                raise Exception(f"Print time not found for {stl_file}")

            print_time = print_time_list[0]
            batch_print_time += print_time

            print_days = print_time // (24 * 3600)
            print_hours = print_time // 3600
            print_minutes = (print_time % 3600) // 60

            print(
                "{:<35} {:02d} days {:02d} hours {:02d} minutes".format(
                    stl_file, print_days, print_hours, print_minutes
                )
            )

        total_days = batch_print_time // (24 * 3600)
        total_hours = batch_print_time // 3600
        total_minutes = (batch_print_time % 3600) // 60

        print("\n")
        print(
            "Total print time: {:02d} days {:02d} hours {:02d} minutes".format(
                total_days, total_hours, total_minutes
            )
        )
        print("-" * 80)
        print("\n")
