#!/usr/bin/env python3
"""Seal the life scenes for readers of the book.

Usage:
    python3 tools/seal.py PRIVATE_JSON OUT_JSON "passphrase" ["another passphrase" ...]

PRIVATE_JSON is the plain scene book of life scenes (keep it out of the public
repository). OUT_JSON is written as life.enc.json next to index.html.

Every passphrase given opens the same content, so you can accept several
spellings (kanji / kana) or a separate word for the English edition.
The page normalises what the reader types the same way as norm() below.

Requires: pip install cryptography
"""
import base64, json, os, sys, unicodedata, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 310000


def norm(p: str) -> str:
    p = unicodedata.normalize("NFKC", p)
    p = re.sub(r"\s+", "", p)
    return p.lower()


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    src, out, phrases = sys.argv[1], sys.argv[2], sys.argv[3:]
    plain = json.load(open(src, encoding="utf-8"))
    data = json.dumps({"scenes": plain["scenes"]}, ensure_ascii=False).encode()

    cek = AESGCM.generate_key(bit_length=256)
    iv = os.urandom(12)
    sealed = AESGCM(cek).encrypt(iv, data, None)

    keys = []
    for p in phrases:
        salt, kiv = os.urandom(16), os.urandom(12)
        kek = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(norm(p).encode())
        keys.append({"salt": b64(salt), "iv": b64(kiv), "key": b64(AESGCM(kek).encrypt(kiv, cek, None))})

    json.dump({"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITER, "keys": keys, "iv": b64(iv), "data": b64(sealed)},
              open(out, "w", encoding="utf-8"))
    print(f"sealed {len(plain['scenes'])} scenes for {len(phrases)} passphrase(s) -> {out}")


if __name__ == "__main__":
    main()
