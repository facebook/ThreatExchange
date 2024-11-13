from PIL import Image


def is_pixel_black(pixel, threshold):
    """
    Check if each color channel in the pixel is below the threshold
    """
    r, g, b = pixel
    return r < threshold and g < threshold and b < threshold


def detect_top_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the top black border by counting rows with only black pixels.
    Checks each RGB channel of each pixel in each row.
    Returns the first row that is not all black from the top.
    """
    width, height = image.size
    for y in range(height):
        row_pixels = list(image.crop((0, y, width, y + 1)).getdata())
        if all(is_pixel_black(pixel, black_threshold) for pixel in row_pixels):
            continue
        return y
    return height


def detect_bottom_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the bottom black border by counting rows with only black pixels from the bottom up.
    Checks each RGB channel of each pixel in each row.
    Returns the first row that is not all black from the bottom.
    """
    width, height = image.size
    for y in range(height - 1, -1, -1):
        row_pixels = list(image.crop((0, y, width, y + 1)).getdata())
        if all(is_pixel_black(pixel, black_threshold) for pixel in row_pixels):
            continue
        return height - y - 1
    return height


def detect_left_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the left black border by counting columns with only black pixels.
    Checks each RGB channel of each pixel in each column.
    Returns the first column from the left that is not all black.
    """
    width, height = image.size
    for x in range(width):
        col_pixels = list(image.crop((x, 0, x + 1, height)).getdata())
        if all(is_pixel_black(pixel, black_threshold) for pixel in col_pixels):
            continue
        return x
    return width


def detect_right_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the right black border by counting columns with only black pixels from the right.
    Checks each RGB channel of each pixel in each column.
    Returns the first column from the right that is not all black.
    """
    width, height = image.size
    for x in range(width - 1, -1, -1):
        col_pixels = list(image.crop((x, 0, x + 1, height)).getdata())
        if all(is_pixel_black(pixel, black_threshold) for pixel in col_pixels):
            continue
        return width - x - 1
    return width
