#!/usr/bin/env python3

import sys


def print_array(bit_stream):
    byte_num = 0
    array = []

    while len(bit_stream) > 0:
        n = int("".join(bit_stream[0:8]), 2)
        array.append(n)
        print("{} --> {} : {}".format(byte_num, "".join(bit_stream[0:8]), n))
        bit_stream = bit_stream[8:]
        byte_num += 1

    print(array)


# ---- Start here --------------------------------
bit_stream = []

# Hard-code `Version = 1`
bit_stream += list("000001")

# Hard-code `Created = 15100821554`
bit_stream += list("001110000100000101000100000000110010")

# Hard-code `LastUpdated = 15100821554`
bit_stream += list("001110000100000101000100000000110010")

# Hard-code `CmpId = 7`
bit_stream += list("000000000111")

# Hard-code `CmpVersion = 1`
bit_stream += list("000000000001")

# Hard-code `ConsentScreen = 3`
bit_stream += list("000011")

# Hard-code `ConsentLanguage = "EN" (E=4, N13)`
bit_stream += list("000100001101")

# Hard-code `VendorListVersion = 8`
bit_stream += list("000000001000")

# Hard-code `PurposesAllowed = 14680064`
bit_stream += list("111000000000000000000000")

max_vendor_id = int(input("MaxVendorId: "))
bit_stream += list(bin(max_vendor_id)[2:].zfill(16))

# Hard-code `EncodingType = 1`
bit_stream += list("1")

# For now set `DefaultConsent` to 0 (later we'll also use 1)
bit_stream += list("0")

num_entries = int(input("NumEntries: "))
bit_stream += list(bin(num_entries)[2:].zfill(12))

for i in range(num_entries):
    print("RangeEntry[{}]".format(i))
    single_or_range = int(input("    SingleOrRange (single = 0, range = 1): "))
    bit_stream += list(bin(single_or_range)[2:].zfill(1))

    if single_or_range == 0:
        single_vendor_id = int(input("        SingleVendorId[{}]: ".format(i)))
        bit_stream += list(bin(single_vendor_id)[2:].zfill(16))
    elif single_or_range == 1:
        start_vendor_id = int(input("        StartVendorId[{}]: ".format(i)))
        bit_stream += list(bin(start_vendor_id)[2:].zfill(16))

        end_vendor_id = int(input("        EndVendorId[{}]: ".format(i)))
        bit_stream += list(bin(end_vendor_id)[2:].zfill(16))
    else:
        print("WTF?!!")
        sys.exit(0)

# Add padding bits at the end if necessary
# (such that the length of the bit stream is a multiple of 8)
num_padding_bits = 8 - (len(bit_stream) % 8)
if num_padding_bits < 8:
    # Padding bits are needed
    for i in range(num_padding_bits):
        bit_stream += list("0")

# Save a copy that we can later modify
bit_stream2 = bit_stream

print("With DefaultConsent = 0:")
print_array(bit_stream)

# Now set `DefaultConsent` to 1
bit_stream2[173] = '1'

print("")
print("")

print("With DefaultConsent = 1:")
print_array(bit_stream2)
