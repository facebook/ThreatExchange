import vpdq


def read_file_to_hash(input_hash_filename):
    """Read hash file and return vpdq hash

    Args:
        input_hash_filename (str): Input hash file path

    Returns:
        list of vpdq_feature: vpdq hash from the hash file"""

    hash = []
    with open(input_hash_filename, "r") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            content = line.split(",")
            pdq_hash = vpdq.str_to_hash(content[2])
            feature = vpdq.vpdq_feature(int(content[1]), int(content[0]), pdq_hash)
            hash.append(feature)

    return hash


def output_hash_to_file(output_hash_filename, hashes):
    """Output vpdq hash to txt file

    Args:
        output_hash_filename (str): Output hash file path
        hash (list of vpdq_feature): Vpdq Hash"""

    with open(output_hash_filename, "w") as file:
        for cur in hashes:
            file.write(
                str(cur.frame_number)
                + ","
                + str(cur.quality)
                + ","
                + hash_to_hex(cur.hash["w"])
            )
            file.write("\n")
