"""앱에 실제로 쓰인 글자만 담은 글꼴을 내려받아 자체 호스팅한다.

구글 글꼴을 그대로 링크하면 오프라인에서 글꼴이 깨진다.
그렇다고 한글 글꼴 전체를 넣으면 1~2MB가 붙는다.
구글 글꼴 API의 text= 옵션으로 필요한 글자만 받으면 수십 KB로 끝난다.

받은 파일은 fonts/ 에 두고, 글자 목록이 그대로면 다시 받지 않는다.
(네트워크가 없어도 빌드가 되어야 한다)
"""
import hashlib
import io
import json
import os
import re
import urllib.parse

import requests

OUT_DIR = "../fonts"
STAMP = os.path.join(OUT_DIR, "charset.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 역할별로 어떤 글자가 필요한지 다르다.
FACES = [
    # (파일명, 구글 family 표기, 그 글꼴이 그리는 글자 범위)
    ("jua",         "Jua",              "korean"),
    ("gowun-dodum", "Gowun+Dodum",      "korean"),
    ("fredoka-400", "Fredoka:wght@400", "latin"),
    ("fredoka-500", "Fredoka:wght@500", "latin"),
    ("fredoka-600", "Fredoka:wght@600", "latin"),
]

LATIN_BASE = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
              "0123456789 .,!?'\"()[]{}:;/-_+=%&*#@~`|<>^$\\")


def collect_chars(sources):
    """빌드에 들어갈 텍스트에서 쓰인 글자를 모은다."""
    seen = set()
    for text in sources:
        seen.update(text)
    # 화면에 안 나오는 제어문자는 뺀다
    seen = {c for c in seen if c.isprintable() and c not in "\t\n\r"}
    return seen


def split_sets(chars):
    """한글용과 라틴용으로 나눈다."""
    korean = {c for c in chars if ord(c) > 0x2000}   # 한글·기호·이모지 등
    korean |= set(LATIN_BASE)                        # 한글 글꼴도 영문을 섞어 쓴다
    latin = set(LATIN_BASE) | {c for c in chars if ord(c) < 0x250}
    # 이모지는 기기 글꼴이 그린다. 글꼴 파일에 넣을 수 없다.
    drop = {c for c in korean if 0x1F000 <= ord(c) or 0x2600 <= ord(c) <= 0x27BF}
    korean -= drop
    return "".join(sorted(korean)), "".join(sorted(latin))


def fetch_face(family, text):
    """구글에서 필요한 글자만 담은 woff2 하나를 받아온다."""
    url = ("https://fonts.googleapis.com/css2?family=" + family +
           "&text=" + urllib.parse.quote(text) + "&display=swap")
    css = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    css.raise_for_status()
    # text= 로 받으면 확장자 없는 /l/font?kit=... 형태로 온다
    urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css.text)
    if not urls:
        raise RuntimeError(f"{family}: 글꼴 주소를 찾지 못했다\n" + css.text[:200])
    if len(urls) > 1:
        raise RuntimeError(f"{family}: 조각이 {len(urls)}개다 - text= 가 먹지 않았다")
    if "woff2" not in css.text:
        raise RuntimeError(f"{family}: woff2 가 아니다")
    blob = requests.get(urls[0], headers={"User-Agent": UA}, timeout=30)
    blob.raise_for_status()
    return blob.content


def build(sources):
    """글꼴 파일을 준비하고 @font-face 규칙을 돌려준다."""
    chars = collect_chars(sources)
    ko, la = split_sets(chars)
    key = hashlib.sha1((ko + "|" + la).encode("utf-8")).hexdigest()[:12]

    os.makedirs(OUT_DIR, exist_ok=True)
    old = None
    if os.path.exists(STAMP):
        with io.open(STAMP, encoding="utf-8") as f:
            old = json.load(f).get("key")

    files = {name: os.path.join(OUT_DIR, name + ".woff2") for name, _, _ in FACES}
    have_all = all(os.path.exists(p) for p in files.values())

    if old == key and have_all:
        print(f"  글꼴 그대로 ({len(ko)}자 한글셋, 다시 받지 않음)")
    else:
        print(f"  글꼴 받는 중 - 한글 {len(ko)}자 / 라틴 {len(la)}자")
        for name, family, scope in FACES:
            data = fetch_face(family, ko if scope == "korean" else la)
            with open(files[name], "wb") as f:
                f.write(data)
            print(f"    {name:14} {len(data)/1024:6.1f} KB")
        with io.open(STAMP, "w", encoding="utf-8") as f:
            json.dump({"key": key, "korean": len(ko), "latin": len(la)}, f)

    total = sum(os.path.getsize(p) for p in files.values())
    print(f"  글꼴 합계 {total/1024:.1f} KB")

    face = lambda fam, name, weight: (
        f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{weight};"
        f"font-display:swap;src:url(fonts/{name}.woff2) format('woff2')}}")
    return "\n".join([
        face("Jua", "jua", 400),
        face("Gowun Dodum", "gowun-dodum", 400),
        face("Fredoka", "fredoka-400", 400),
        face("Fredoka", "fredoka-500", 500),
        face("Fredoka", "fredoka-600", 600),
    ]), [f"fonts/{n}.woff2" for n, _, _ in FACES]
