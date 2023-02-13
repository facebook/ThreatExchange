# Multiple modes for same image

Images were generated via the following python code
```python
from PIL import Image
image = Image.open("original.jpg")
image = image.convert(mode)
image.save(filename)
```

for modes listed here
https://pillow.readthedocs.io/en/stable/handbook/concepts.html

with various valid file formats for the mode
https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#image-file-formats

Images are visually inspected to verify that they are similar to the original image.
