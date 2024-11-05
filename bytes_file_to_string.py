#!/usr/bin/env python


# This script comes in handy when debugging C# applications in Visual Studio.
# If the C# code contains a byte array, then the Visual Studio debugger simply
# shows them as numbers. Thankfully, it allows one to export the numbers to a
# CSV file. A so-exported CSV file can be given as input to this script to get
# the equivalent string representation.


import argparse


def main():
    parser = argparse.ArgumentParser(description="Convert numbers in a file to an ASCII string.")
    parser.add_argument('file_path', help="Path to the input file containing numbers")
    args = parser.parse_args()

    output_string = ''

    # Open the file with 'utf-8-sig' encoding to handle potential BOM at the
    # beginning of the file.
    with open(args.file_path, 'r', encoding='utf-8-sig') as file:
        first_line = True
        for line in file:
            line = line.strip()
            if first_line:
                first_line = False
                if line == "Byte":
                    continue
            ascii_value = int(line)
            output_string += chr(ascii_value)

    print(output_string)


if __name__ == '__main__':
    main()
