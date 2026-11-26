"""Reconstruct the recorded BF16 vectors on CPU without writing a checkpoint."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from struct import pack, unpack




def read_tensor(checkpoint, name):
    with checkpoint.open("rb") as handle:
        header_length = unpack("<Q",handle.read(8))[0]
        if not 0 < header_length < 20_000_000:
            raise ValueError("Invalid safetensors header length")
        entry = json.loads(handle.read(header_length))[name]
        if entry["dtype"] != "BF16" or entry["shape"] != [2560]:
            raise ValueError("Unexpected parameter storage")
        start,end = entry["data_offsets"]
        if start < 0 or end - start != 5120:
            raise ValueError("Unexpected byte offsets")
        handle.seek(8+header_length+start)
        raw = handle.read(end-start)
    if len(raw) != 5120:
        raise ValueError("Truncated parameter")
    return raw


def rebuild(base, patch):
    words = list(unpack(f"<{len(base)//2}H",base))
    original_hash = sha256(base).hexdigest()
    if original_hash != patch["base_sha256"]:
        raise ValueError("Unexpected original parameter hash")
    indices = patch["coordinates"]
    changes = patch["deltas"]
    if len(indices) != len(changes) or len(indices) != len(set(indices)):
        raise ValueError("Invalid parameter coordinates")
    for index,delta in zip(indices, changes, strict=True):
        if type(index) is not int or not 0 <= index < len(words) or not math.isfinite(delta) or delta == 0:
            raise ValueError("Invalid BF16 change")
        original = unpack("<f",pack("<I",words[index]<<16))[0]
        bits = unpack("<I",pack("<f",original+delta))[0]
        if bits & 0xffff or bits >> 16 == words[index]:
            raise ValueError("Patch delta does not yield a different exact BF16 value")
        words[index] = bits >> 16
    return pack(f"<{len(words)}H",*words)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    patch = json.loads(Path(__file__).with_name("patch.json").read_text())
    checksum = sha256()
    with args.checkpoint.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    if checksum.hexdigest() != patch["model_sha256"]:
        raise ValueError("Checkpoint differs from the experiment")
    base = read_tensor(args.checkpoint, patch["parameter"])
    results = {}
    for arm in ("targeted", "matched_random"):
        vector = rebuild(base, patch[arm])
        results[arm] = sha256(vector).hexdigest()
        if results[arm] != patch[arm]["parameter_sha256"]:
            raise ValueError(f"Reconstructed tensor mismatch for {arm}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
