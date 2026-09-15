"""상점 아이템 그림 정리.

items/원본/ 에 넣은 그림을 다듬어 items/<이름>.png 로 내보낸다.
원본은 절대 건드리지 않는다. 결과가 마음에 안 들면 다시 돌리면 된다.

하는 일
  1. 가장자리에서 배경(밝고 색이 거의 없는 칸)을 타고 들어가며 지운다.
     전체에서 흰색을 다 지우면 문양 안쪽의 흰 부분까지 날아간다.
  2. 지우다 보면 삼색기의 흰 줄처럼 좁은 틈이 같이 날아간다.
     위아래가 가까이서 '색이 진한' 칸으로 막혀 있으면 되살린다.
  3. 본체에 비해 아주 작은 조각은 버린다 (체크무늬 찌꺼기 등).
  4. 빈 여백을 잘라내고 한 변 256px 로 줄인다.

주의: getbbox() 는 (255,255,255,0) 을 '비어 있음'으로 보지 않는다.
알파 채널만 보고 잘라야 여백이 실제로 떨어진다.
"""
import os, glob
from collections import deque
from PIL import Image

SRC = '../items/원본'
OUT = '../items'
BOX = 256
EXT = ('.png', '.jpg', '.jpeg', '.webp')


def _is_bg(px, x, y):
    r, g, b, a = px[x, y]
    return a > 0 and min(r, g, b) >= 210 and (max(r, g, b) - min(r, g, b)) <= 18


def _strong(c):
    r, g, b, a = c
    return a > 0 and (max(r, g, b) - min(r, g, b)) >= 55


def clean(path, out, box=BOX):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    px = im.load()

    # 1. 가장자리에서 배경 지우기. 이미 비어 있는 칸도 지나갈 수 있어야
    #    한 번 지워진 그림을 다시 돌려도 안쪽까지 닿는다.
    def passable(x, y):
        return px[x, y][3] == 0 or _is_bg(px, x, y)

    seen = bytearray(w * h)
    q = deque()
    edge = [(x, y) for x in range(w) for y in (0, h - 1)]
    edge += [(x, y) for y in range(h) for x in (0, w - 1)]
    for x, y in edge:
        if not seen[y * w + x] and passable(x, y):
            seen[y * w + x] = 1
            q.append((x, y))
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and passable(nx, ny):
                seen[ny * w + nx] = 1
                q.append((nx, ny))

    # 2. 좁은 틈 되살리기 (삼색기 흰 줄 같은 것)
    filled = 0
    for x in range(w):
        y = 0
        while y < h:
            if px[x, y][3] == 0:
                y0 = y
                while y < h and px[x, y][3] == 0:
                    y += 1
                if (y - y0) <= 8 and y0 > 0 and y < h \
                        and _strong(px[x, y0 - 1]) and _strong(px[x, y]):
                    for yy in range(y0, y):
                        px[x, yy] = (255, 255, 255, 255)
                        filled += 1
            else:
                y += 1

    # 3. 본체에 비해 아주 작은 조각 버리기
    lab = [-1] * (w * h)
    sizes = []
    for sy in range(h):
        for sx in range(w):
            if lab[sy * w + sx] != -1 or px[sx, sy][3] == 0:
                continue
            cid = len(sizes)
            lab[sy * w + sx] = cid
            n = 0
            q = deque([(sx, sy)])
            while q:
                x, y = q.popleft()
                n += 1
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            j = ny * w + nx
                            if lab[j] == -1 and px[nx, ny][3] > 0:
                                lab[j] = cid
                                q.append((nx, ny))
            sizes.append(n)
    keep = max(sizes) * 0.02 if sizes else 0
    dropped = 0
    for y in range(h):
        for x in range(w):
            c = lab[y * w + x]
            if c != -1 and sizes[c] < keep:
                px[x, y] = (0, 0, 0, 0)
                dropped += 1

    # 4. 여백 잘라내고 줄이기
    bbox = im.getchannel('A').getbbox()
    if bbox:
        im = im.crop(bbox)
    im.thumbnail((box, box), Image.LANCZOS)
    im.save(out)
    return im.size, filled, dropped, len(sizes)


if __name__ == '__main__':
    files = [f for f in sorted(glob.glob(os.path.join(SRC, '*')))
             if os.path.splitext(f)[1].lower() in EXT]
    if not files:
        print(f'{SRC} 에 그림이 없습니다.')
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        out = os.path.join(OUT, name + '.png')
        size, filled, dropped, comps = clean(f, out)
        print(f'  {name:14} {size[0]}x{size[1]}  '
              f'되살린 칸 {filled}, 버린 칸 {dropped}, 조각 {comps}개  -> {out}')
