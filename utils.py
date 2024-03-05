import os
from stl import mesh


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


def display_total_print_time(time: int):
    days = time // (24 * 3600)
    time %= 24 * 3600
    hours = time // 3600
    time %= 3600
    minutes = time // 60

    print(f"Total print time {days} days {hours} hours {minutes} minutes")


def display_stl_print_time(stl_file: str, time: int):
    days = time // (24 * 3600)
    time %= 24 * 3600
    hours = time // 3600
    time %= 3600
    minutes = time // 60

    print(f"{stl_file:<35} {days} days {hours} hours {minutes} minutes")


def display_divider():
    print("-" * 80)


def filter_stl_files(p: str) -> list[str]:
    return [f for f in os.listdir(p) if f.endswith(".stl")]


def get_file_print_time(all_print_times, stl_file):
    print_time_list = [time for _, file, time in all_print_times if file == stl_file]

    if not print_time_list:
        raise Exception(f"Print time not found for {stl_file}")

    print_time = print_time_list[0]
    return print_time
