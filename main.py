import os
import subprocess
import re
from rectpack import newPacker, SORT_RATIO

from utils import (
    calculate_bounding_box,
    display_divider,
    display_stl_print_time,
    display_total_print_time,
    filter_stl_files,
    get_file_print_time,
)

# Configuration
script_dir = os.path.dirname(os.path.realpath(__file__))
stl_dir = os.path.join(script_dir, "stl")
prusa_slicer_path = "/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"  # Adjust if needed

config_map = {
    "MK3S": "prusa_mk3s_petg_0.15mm.ini",
    "Mini": "prusa_mini_petg_0.15mm.ini",
}

# Printer build plate sizes (length, width) in mm
build_plate_sizes = {"MK3S": (250, 210), "Mini": (180, 180)}

time_regex = re.compile(
    r"; estimated printing time \(.*\) = (?:(\d+)d\s)?(?:(\d+)h\s)?(?:(\d+)m\s)?(?:(\d+)s)?"
)


def process_stl_file(subdirectory, stl_file, config_file):
    config_file_path = os.path.join(script_dir, config_file)
    subdir_path = os.path.join(stl_dir, subdirectory)
    stl_file_path = os.path.join(subdir_path, stl_file)

    stl_file_name = os.path.splitext(stl_file)[0]
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
            match = time_regex.search(line)

            if match:
                days, hours, minutes, seconds = [
                    int(t) if t else 0 for t in match.groups()
                ]
                total_seconds = (
                    seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
                )
                return total_seconds

    raise Exception(f"Print time not found for {stl_file}")


# Function to process STL files in stl subdirectory
def process_stl_files(subdir, config_file):
    subdir_path = os.path.join(stl_dir, subdir)

    print_times = []

    for stl_file in filter_stl_files(subdir_path):
        print_time = process_stl_file(subdir, stl_file, config_file)
        print_times.append((stl_file, print_time))

    return print_times


def gather_print_times():
    all_print_times = []
    for current_subdir, config in config_map.items():
        print_times = process_stl_files(current_subdir, config)
        all_print_times.extend(
            [(current_subdir, stl_file, time) for stl_file, time in print_times]
        )

        print(f"Processed {len(print_times)} files in {current_subdir}")

    return all_print_times


def group_print_times(all_print_times):
    # Group print times per subdirectory
    subdir_print_times = {}
    for current_subdir, stl_file, time in all_print_times:
        if current_subdir not in subdir_print_times:
            subdir_print_times[current_subdir] = []

        subdir_print_times[current_subdir].append([stl_file, time])

    # sort print times by time
    for _, print_times in subdir_print_times.items():
        print_times.sort(key=lambda x: x[1], reverse=True)

    return subdir_print_times


def display_print_times(subdir_print_times):
    for subdir, print_times in subdir_print_times.items():
        print(f"Subdirectory: {subdir}")
        display_divider()
        for stl_file, time in print_times:
            display_stl_print_time(stl_file, time)
        display_divider()


def get_stl_dimensions():
    stl_dimensions = {}

    for subdir in config_map.keys():
        stl_dimensions[subdir] = []
        subdir_path = os.path.join("stl", subdir)  # Adjust path as needed
        for stl_file in filter_stl_files(subdir_path):
            stl_path = os.path.join(subdir_path, stl_file)
            length, width, _ = calculate_bounding_box(stl_path, padding=20.0)
            stl_dimensions[subdir].append((stl_file, (length, width)))

    return stl_dimensions


def get_print_times():
    all_print_times = gather_print_times()
    subdir_print_times = group_print_times(all_print_times)
    display_print_times(subdir_print_times)

    return all_print_times


def get_print_batches(
    all_print_times: list[tuple[str, str, int]],
    stl_dimensions: dict[str, list[tuple[str, tuple[int, int]]]],
):
    prev_printer = None

    # Add each rectangle (length, width) to the packer
    for subdir, dimensions in stl_dimensions.items():
        # Create a new packer
        packer = newPacker(sort_algo=SORT_RATIO)

        for stl_file, (length, width) in dimensions:
            build_plate_size = build_plate_sizes[subdir]
            # Add the rectangles to the packer
            # it's the same as printing one stl file at a time on a printer
            packer.add_rect(length, width, rid=stl_file)
            packer.add_bin(*build_plate_size, bid=subdir)

        # Pack the rectangles into the minimum number of bins
        packer.pack()

        # Print the resulting bins
        for i, rect in enumerate(packer):
            print(f"Batch {i + 1} for {subdir}")
            curr_printer = rect.bid

            if prev_printer != curr_printer:
                prev_printer = curr_printer

                print("{:<35} {:<20}".format("STL File", "Print Time"))
                display_divider()

            batch_print_time = 0

            for stl_file, _, _, _, _ in [list(l)[::-1] for l in rect.rect_list()]:
                print_time = get_file_print_time(all_print_times, stl_file)
                batch_print_time += print_time

                display_stl_print_time(stl_file, print_time)

            display_total_print_time(batch_print_time)
            display_divider()


if __name__ == "__main__":
    get_print_batches(get_print_times(), get_stl_dimensions())
