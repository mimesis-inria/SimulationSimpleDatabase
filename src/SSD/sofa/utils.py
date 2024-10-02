import traceback


def error_message(message):

    print("\nTraceback (most recent call last):")
    # Get each line of the traceback
    for filename, line_num, func, _ in traceback.extract_stack()[:-1]:
        # Print the file information
        print(f"\n  File '{filename}', line {line_num}, in {func}")
        # Read file
        with open(filename) as f:
            lines = f.readlines()
        # Select the lines around the error
        first_line = max(0, line_num - 2)
        error_line = line_num - first_line - 1
        last_line = min(line_num + 1, len(lines))
        # Get indentation of the selected lines to align them
        indent = None
        for line in lines[first_line: last_line]:
            space = 0
            while space < len(line) and line[space] == ' ':
                space += 1
            indent = space if indent is None else min(indent, space)
        # Print the lines
        for i, line in enumerate(lines[first_line: last_line]):
            line = line.rstrip()
            print(f"   {'>' if i == error_line else ' '}  {line[indent:]}")
    # Print error message and exit code
    print(f'\n[ERROR] {message}\n')
    quit()
