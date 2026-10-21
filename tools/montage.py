# -*- coding: utf-8 -*-
"""把 PDF 每 6 页拼成一张缩略图，便于快速通览版式。"""
import glob
import os
import sys

from PIL import Image

src = sys.argv[1]
out = sys.argv[2]
files = sorted(glob.glob(os.path.join(src, "page-*.png")))
print("pages:", len(files))
cols, rows = 3, 2
for k in range(0, len(files), cols * rows):
    batch = files[k:k + cols * rows]
    ims = [Image.open(f).convert("RGB") for f in batch]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * cols, h * rows), "white")
    for idx, im in enumerate(ims):
        sheet.paste(im, ((idx % cols) * w, (idx // cols) * h))
    p = os.path.join(out, "sheet-%02d.png" % (k // (cols * rows) + 1))
    sheet.save(p)
    print(p, len(batch))
