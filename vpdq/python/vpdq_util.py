import vpdq
import numpy as np


def vector_to_hex(hash_vector):
    """Convect from hash vector to hex string

    Args:
        hash_vector (numpy array): Numpy array vector of a pdq hash

    Returns:
        str : Hex string of the hash
    """
    bin_str = "".join([str(x) for x in hash_vector])
    # binary to hex using format string
    # '%0*' is for padding up to ceil(num_bits/4),
    # '%X' create a hex representation from the binary string's integer value
    hex_str = "%0*X" % ((len(bin_str) + 3) // 4, int(bin_str, 2))
    hex_str = hex_str.lower()
    return hex_str


def hash_to_vector(hash_value):
    """Convect from pdq hash to numpy array

    Args:
        hash_value (Hash256):

    Returns:
        numpy array:
    """
    hash_value = hash_value["w"]
    return np.array([(hash_value[(k & 255) >> 4] >> (k & 15)) & 1 for k in range(256)])[
        ::-1
    ]


def hash_to_hex(hash_value):
    """Convect from pdq hash to hex str

    Args:
        hash_value (Hash256):

    Returns:
        str: hex str of hash
    """
    return vector_to_hex(hash_to_vector(hash_value))


def output_hash_to_file(outputHashFileName, hashes):
    """Output vpdq hash to txt file

    Args:
        outputHashFileName (str): Output hash file path
        hash (list of vpdq_feature): Vpdq Hash
    """
    with open(outputHashFileName, "w") as file:
        for cur in hashes:
            file.write(
                str(cur.frame_number)
                + ","
                + str(cur.quality)
                + ","
                + hash_to_hex(cur.hash["w"])
            )
            file.write("\n")


def read_file_to_hash(inputHashFileName):
    """Read hash file and return vpdq hash

    Args:
        inputHashFileName (str): Input hash file path

    Returns:
        list of vpdq_feature: vpdq hash from the hash file
    """
    hash = []
    with open(inputHashFileName, "r") as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            content = line.split(",")
            pdq_hash = vpdq.fromString(content[2])
            feature = vpdq.vpdq_feature(int(content[1]), int(content[0]), pdq_hash)
            hash.append(feature)

    return hash
