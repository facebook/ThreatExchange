Let's take the example of a photo. Once submitted, a photo goes through three phases in the HMA system.

This is shown graphically below.

![Graphic showing what happens to an uploaded photo](https://github.com/facebook/ThreatExchange/blob/f8cabae8d151a4b68588adfa0454d48af95c7277/hasher-matcher-actioner/docs/images/what-happens-to-photos.png)

Note: Video with MD5 hashing is not supported yet.

### Hashing Phase

For photos, the supported hashing algorithm is PDQ. We apply the PDQ algorithm and get a hash. This is passed on to the matching phase.

### Matching Phase

For PDQ hashes, checking equality is not enough. We must compute the distance of the hash from other hashes if present. We us an index from the [FAISS](https://github.com/facebookresearch/faiss) library for this. All matches found within a specific hash-distance are forwarded to the actioning phase.

### Actioning Phase

When a match occurs, relevant details, for example the name, id and tags of the matching collaboration are evaluated against your configured action rules. If any action rule is applicable, the connected action is performed.

---

## Privacy

During all the above phases, the raw content of the image never leaves your cloud provider account. ThreatExchange does not receive hashes from HMA during this flow. If you have configured the setting, hashes of the images found on ThreatExchange get a `saw_this_too` reaction. [Learn how to control that setting](https://github.com/facebook/ThreatExchange/wiki/How-to-disable-writebacks-to-ThreatExchange).