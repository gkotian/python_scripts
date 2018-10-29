#!/usr/bin/env python3

import sys


def print_array(bit_stream):
    # MaxVendorId starts in the middle of byte 19
    byte_num = 19

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

# Pre-add 4 zeroes (the last 4 bits from `PurposesAllowed`)
bit_stream += list("0000")

max_vendor_id = int(input("MaxVendorId: "))
bit_stream += list(bin(max_vendor_id)[2:].zfill(16))

# encoding_type = int(input("EncodingType (BitField = 0, Range = 1): "))
# bit_stream += list(bin(encoding_type)[2:].zfill(1))
# We assume `EncodingType` as Range, so simply add a 1
bit_stream += list("1")

# default_consent = int(input("DefaultConsent: "))
# bit_stream += list(bin(default_consent)[2:].zfill(1))
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

# Save a copy that we can later modify
bit_stream2 = bit_stream

print("With DefaultConsent = 0:")
print_array(bit_stream)

# Now set `DefaultConsent` to 1
bit_stream2[21] = '1'

print("")
print("")

print("With DefaultConsent = 1:")
print_array(bit_stream2)
