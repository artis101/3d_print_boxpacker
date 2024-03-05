from main import get_print_batches


def test_get_print_batches():
    all_print_times = [
        ("stl_file1", "MK3S", 10),
        ("stl_file2", "Mini", 15),
        ("stl_file3", "MK3S", 8),
        ("stl_file4", "Mini", 12),
    ]
    stl_dimensions = {
        "MK3S": [("stl_file1", (10, 20)), ("stl_file2", (15, 25))],
        "Mini": [("stl_file3", (8, 12)), ("stl_file4", (10, 15))],
    }

    # Call the function to get the print batches
    get_print_batches(all_print_times, stl_dimensions)

    # Add assertions to verify the expected output
    # For example:
    # assert ...


# Append the test case to the existing test file
test_get_print_batches()
