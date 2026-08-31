"""홈 화면 아이콘을 그린다.

이모지는 파비콘으로는 쓸 수 있지만 홈 화면 아이콘으로는 못 쓴다.
(아이폰은 apple-touch-icon 으로 PNG 를 요구한다)
4배 크기로 그린 뒤 줄여서 가장자리를 매끄럽게 만든다.
"""
import os

from PIL import Image, ImageDraw

OUT_DIR = "../icons"
BG = (245, 201, 89)        # 꿀색
BODY = (58, 44, 24)        # 벌 몸통
STRIPE = (247, 214, 106)   # 몸통 줄무늬
WING = (255, 255, 255)

SIZES = [180, 192, 512]    # 애플 홈 화면 / 매니페스트


def draw_icon(size, pad_ratio):
    """pad_ratio: 벌 주위 여백. 잘려도 되는 아이콘(maskable)은 크게 준다."""
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 배경: 둥근 사각형
    r = int(S * 0.22)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=r, fill=BG)

    cx, cy = S / 2, S / 2
    body_w = S * (1 - pad_ratio) * 0.52
    body_h = body_w * 1.12

    # 날개 (몸통보다 먼저 그려 뒤로 보낸다)
    wing_w, wing_h = body_w * 0.62, body_h * 0.46
    for sx in (-1, 1):
        box = [cx + sx * body_w * 0.30 - wing_w / 2, cy - body_h * 0.52,
               cx + sx * body_w * 0.30 + wing_w / 2, cy - body_h * 0.52 + wing_h]
        d.ellipse(box, fill=WING + (235,))

    # 몸통
    body = [cx - body_w / 2, cy - body_h / 2 + body_h * 0.10,
            cx + body_w / 2, cy + body_h / 2 + body_h * 0.10]
    d.ellipse(body, fill=BODY)

    # 줄무늬 — 몸통 안쪽만 남기려고 몸통 모양으로 오려낸다
    stripes = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripes)
    top = body[1]
    h = body[3] - body[1]
    for i in (1, 2):
        y = top + h * (0.30 + 0.26 * (i - 1))
        sd.rounded_rectangle([body[0], y, body[2], y + h * 0.15],
                             radius=int(h * 0.07), fill=STRIPE)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse(body, fill=255)
    img.paste(stripes, (0, 0), Image.composite(
        mask, Image.new("L", (S, S), 0), stripes.split()[3]))

    # 눈
    eye = body_w * 0.07
    for sx in (-1, 1):
        ex = cx + sx * body_w * 0.17
        ey = top + h * 0.17
        d.ellipse([ex - eye, ey - eye, ex + eye, ey + eye], fill=BG)

    return img.resize((size, size), Image.LANCZOS)


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    made = []
    for s in SIZES:
        p = os.path.join(OUT_DIR, f"icon-{s}.png")
        draw_icon(s, 0.10).save(p, optimize=True)
        made.append(f"icons/icon-{s}.png")
    # 안드로이드는 아이콘을 원형으로 자르기도 한다. 여백을 더 준 판을 따로 둔다.
    p = os.path.join(OUT_DIR, "maskable-512.png")
    draw_icon(512, 0.34).save(p, optimize=True)
    made.append("icons/maskable-512.png")
    total = sum(os.path.getsize(os.path.join("..", m)) for m in made)
    print(f"  아이콘 {len(made)}개, {total/1024:.1f} KB")
    return made


if __name__ == "__main__":
    build()
