#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Wrapper around the video content type.
"""
from PIL import Image
import io

from .content_base import ContentType, RotationType


class PhotoContent(ContentType):
    """
    Content that contains static visual imagery.

    Examples might be:
      * jpeg
      * png
      * gif (non-animated)
      * frames from videos
      * thumbnails of videos
    """

    @classmethod
    def rotate_image(cls, image_data: bytes, angle: float) -> bytes:
        """
        Rotate an image by a given angle.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            rotated_img = img.rotate(angle, expand=True)
            with io.BytesIO() as buffer:
                rotated_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_x(cls, image_data: bytes) -> bytes:
        """
        Flip the image horizontally along the X-axis.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_y(cls, image_data: bytes) -> bytes:
        """
        Flip the image vertically along the Y-axis.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_plus1(cls, image_data: bytes) -> bytes:
        """
        Flip the image diagonally along the line y = x.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.ROTATE_270).transpose(
                Image.Transpose.FLIP_LEFT_RIGHT
            )
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_minus1(cls, image_data: bytes) -> bytes:
        """
        Flip the image diagonally along the line y = -x.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.ROTATE_90).transpose(
                Image.Transpose.FLIP_LEFT_RIGHT
            )
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def all_simple_rotations(cls, image_data: bytes):
        """
        Generate the 8 naive rotations of an image.

        This can be helpful for testing.
        And for image algorithms that don't have a native way to generate rotations during hashing,
        this can be a way to brute force rotations.
        """
        rotations = {
            RotationType.ORIGINAL: image_data,
            RotationType.ROTATE90: cls.rotate_image(image_data, 90),
            RotationType.ROTATE180: cls.rotate_image(image_data, 180),
            RotationType.ROTATE270: cls.rotate_image(image_data, 270),
            RotationType.FLIPX: cls.flip_x(image_data),
            RotationType.FLIPY: cls.flip_y(image_data),
            RotationType.FLIPPLUS1: cls.flip_plus1(image_data),
            RotationType.FLIPMINUS1: cls.flip_minus1(image_data),
        }
        return rotations
    
    @classmethod
    def load_grayscale_image(image_data: bytes) -> Image.Image:
        """
        Load image from bytes and convert it to grayscale.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            return img.convert("L")
          
    @classmethod
    def detect_top_border(grayscale_img: Image.Image, black_threshold: int = 10) -> int:
        """
        Detect the top black border by counting rows with only black pixels.
        Uses a defualt black threshold of 10 so that only rows with pixel brightness 
        of 10 or lower will be removed.
        
        Returns the first row that is not all blacked out from the top.
        """
        width, height = grayscale_img.size
        for y in range(height):
            if all(grayscale_img.getpixel((x, y)) < black_threshold for x in range(width)):
                continue
            return y
        return height
      
    @classmethod
    def detect_bottom_border(grayscale_img: Image.Image, black_threshold: int = 10) -> int:
        """
        Detect the bottom black border by counting rows with only black pixels from the bottom up.
        Uses a defualt black threshold of 10 so that only rows with pixel brightness 
        of 10 or lower will be removed.
        
        Returns the first row that is not all blacked out from the bottom.
        """
        width, height = grayscale_img.size
        for y in range(height - 1, -1, -1):
            if all(grayscale_img.getpixel((x, y)) < black_threshold for x in range(width)):
                continue
            return height - y - 1
        return height
    
    @classmethod
    def detect_left_border(grayscale_img: Image.Image, black_threshold: int = 10) -> int:
        """
        Detect the left black border by counting columns with only black pixels.
        Uses a defualt black threshold of 10 so that only colums with pixel brightness 
        of 10 or lower will be removed.
        
        Returns the first column from the left that is not all blacked out in the column.
        """
        width, height = grayscale_img.size
        for x in range(width):
            if all(grayscale_img.getpixel((x, y)) < black_threshold for y in range(height)):
                continue
            return x
        return width
    
    @classmethod  
    def detect_right_border(grayscale_img: Image.Image, black_threshold: int = 10) -> int:
        """
        Detect the right black border by counting columns with only black pixels from the right.
        Uses a defualt black threshold of 10 so that only colums with pixel brightness 
        of 10 or lower will be removed.
        
        Returns the first column from the right that is not all blacked out in the column.
        """
        width, height = grayscale_img.size
        for x in range(width - 1, -1, -1):
            if all(grayscale_img.getpixel((x, y)) < black_threshold for y in range(height)):
                continue
            return width - x - 1
        return width
      
    @classmethod
    def unletterbox(cls, image_data: bytes, black_threshold: int = 10) -> bytes:
        """
        Remove black letterbox borders from the sides and top of the image.
        
        Converts the image to grescale then remove the columns and rows that 
        are all completly blacked out. 
        
        Then removing the edges to give back a cleaned image.
        """
        grayscale_img = cls.load_image(image_data)
        
        top = cls.detect_top_border(grayscale_img, black_threshold)
        bottom = cls.detect_bottom_border(grayscale_img, black_threshold)
        left = cls.detect_left_border(grayscale_img, black_threshold)
        right = cls.detect_right_border(grayscale_img, black_threshold)

        width, height = grayscale_img.size
        # creates the new size of the image based off the updated rows
        cropped_size = (left, top, width - right, height - bottom)
      
        with Image.open(io.BytesIO(image_data)) as img:
            cropped_img = img.crop(cropped_size)
            with io.BytesIO() as buffer:
                cropped_img.save(buffer, format=img.format)
                return buffer.getvalue()
