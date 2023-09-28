# TODO: Implement this
# This will use `open_clip` to pull the model and generate embeddings.
# Model initialization will need to be done up-front.
# The hashing process benefits from:
#   - Batch processing: If we can hash multiple images at once, we should.
#   - GPU processing: Checks should be done to see if a GPU is available.
#                     Since we will be using PyTorch, this should just be
#                     a `torch.cuda.is_available()` check.
# Note that we will *only* be using the visual component of the CLIP model
# for this process, not the text component.
