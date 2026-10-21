# -*- coding: utf-8 -*-
"""从 LibreOffice 导出的 PDF 书签中提取「标题 -> 物理页码」映射。"""
import re
import sys


def parse_objects(data):
    objs = {}
    for m in re.finditer(rb"(\d+)\s+0\s+obj\b(.*?)\bendobj", data, re.S):
        objs[int(m.group(1))] = m.group(2)
    return objs


def decode_pdf_string(raw):
    raw = raw.strip()
    if raw.startswith(b"<") and raw.endswith(b">"):
        hexs = re.sub(rb"[^0-9A-Fa-f]", b"", raw[1:-1])
        b = bytes.fromhex(hexs.decode("ascii"))
        try:
            if b.startswith(b"\xfe\xff"):
                return b[2:].decode("utf-16-be", "ignore")
            return b.decode("latin-1", "ignore")
        except Exception:
            return ""
    if raw.startswith(b"(") and raw.endswith(b")"):
        return raw[1:-1].decode("latin-1", "ignore")
    return ""


def page_index(objs):
    """返回 {page_obj_num: 1-based page}"""
    root = None
    for num, body in objs.items():
        if b"/Type/Pages" in body.replace(b" ", b"") and b"/Parent" not in body:
            root = num
            break
    if root is None:
        for num, body in objs.items():
            if b"/Type/Pages" in body.replace(b" ", b""):
                root = num
                break
    pages = []

    def walk(num):
        body = objs[num]
        kids = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
        if kids and b"/Type/Page" not in body.replace(b" ", b"").replace(b"/Type/Pages", b""):
            for ref in re.findall(rb"(\d+)\s+0\s+R", kids.group(1)):
                walk(int(ref))
        else:
            pages.append(num)

    walk(root)
    return {p: i + 1 for i, p in enumerate(pages)}


def outline_items(objs, data):
    cat = None
    for num, body in objs.items():
        if b"/Type/Catalog" in body.replace(b" ", b""):
            cat = num
            break
    m = re.search(rb"/Outlines\s+(\d+)\s+0\s+R", objs[cat])
    if not m:
        return []
    root = int(m.group(1))
    items = []

    def dest_page(body):
        m2 = re.search(rb"/Dest\s*\[\s*(\d+)\s+0\s+R", body)
        if m2:
            return int(m2.group(1))
        m3 = re.search(rb"/D\s*\[\s*(\d+)\s+0\s+R", body)
        if m3:
            return int(m3.group(1))
        return None

    def walk(num, depth):
        body = objs[num]
        tm = re.search(rb"/Title\s*(<[0-9A-Fa-f]*>|\([^)]*\))", body, re.S)
        title = decode_pdf_string(tm.group(1)) if tm else ""
        items.append((depth, title, dest_page(body), num))
        first = re.search(rb"/First\s+(\d+)\s+0\s+R", body)
        if first:
            cur = int(first.group(1))
            while cur:
                walk(cur, depth + 1)
                nx = re.search(rb"/Next\s+(\d+)\s+0\s+R", objs[cur])
                cur = int(nx.group(1)) if nx else 0

    first = re.search(rb"/First\s+(\d+)\s+0\s+R", objs[root])
    if first:
        cur = int(first.group(1))
        while cur:
            walk(cur, 1)
            nx = re.search(rb"/Next\s+(\d+)\s+0\s+R", objs[cur])
            cur = int(nx.group(1)) if nx else 0
    return items


def main():
    path = sys.argv[1]
    data = open(path, "rb").read()
    objs = parse_objects(data)
    pidx = page_index(objs)
    for depth, title, dest, num in outline_items(objs, data):
        print("%s%s\tpage=%s" % ("  " * (depth - 1), title, pidx.get(dest, "?")))


if __name__ == "__main__":
    main()
