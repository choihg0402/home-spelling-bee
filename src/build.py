"""템플릿에 단어 데이터를 주입해 index.html 생성."""
import io, json, re, collections, sys, hashlib
import pymupdf
import fonts, icons

# 이번 학기 목록은 한 파일에 학년별로 들어 있다.
WORD_PDF = '../docs/samples/26_Fall_Spelling_Bee_Rules_Word_List.pdf'
USE = [
    ('g1',  'G1',    '2026 Fall G1'),        # 유혁
    ('g23', 'G2-G3', '2026 Fall G2\u2013G3'),   # 유진
]
OUT = '../index.html'
def parse_all(path):
    """쪽마다 예문 열을 따로 구해 모든 행을 뽑는다.
    학년 제목도 나온 순서대로 모은다."""
    doc = pymupdf.open(path)
    entries, titles = [], []
    section = None

    def join(items, mark=False):
        out = ''
        for i, sp in enumerate(items):
            if i and (sp['x0'] - items[i - 1]['x1']) > 0.8:
                out += ' '
            t = sp['t']
            out += ('{' + t.strip() + '}') if (mark and sp['bold'] and t.strip()) else t
        return re.sub(r'\s+', ' ', out).strip()

    for page in doc:
        spans = []
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for sp in line['spans']:
                    if sp['text'].strip():
                        spans.append(dict(y=round(sp['bbox'][1], 1),
                                          yc=(sp['bbox'][1] + sp['bbox'][3]) / 2,
                                          x0=sp['bbox'][0], x1=sp['bbox'][2],
                                          t=sp['text'], bold='Bold' in sp['font']))
        if not spans:
            continue

        # 이 쪽의 예문 열 시작점. 학년마다 위치가 달라 쪽 단위로 구한다.
        # 그냥 최빈값을 쓰면 번호 열과 개수가 같은 쪽에서 번호 열이 뽑힌다.
        # 자주 나오는 열들 중 가장 오른쪽이 예문 열이다.
        freq = collections.Counter(round(sp['x0'], 1) for sp in spans)
        top = max(freq.values())
        cols = [x for x, n in freq.items() if n >= top * 0.5]
        sent_x = max(cols) - 2

        # 같은 줄 묶기 (조각마다 y가 1pt 안팎으로 어긋난다)
        TOL = 6.0
        rows = {}
        for sp in sorted(spans, key=lambda sp: (sp['yc'], sp['x0'])):
            key = next((k for k in rows if abs(k - sp['yc']) <= TOL), None)
            if key is None:
                key = sp['yc']
                rows[key] = []
            rows[key].append(sp)
        for k in rows:
            rows[k].sort(key=lambda sp: sp['x0'])

        for k in sorted(rows):
            items = rows[k]
            left = [sp for sp in items if sp['x0'] < sent_x]
            sent = [sp for sp in items if sp['x0'] >= sent_x]
            if left and re.fullmatch(r'\d+', left[0]['t'].strip()) and len(left) > 1:
                w = join(left[1:])
                entries.append([int(left[0]['t']), w, hide(join(sent, mark=True), w),
                                'C' if section == 'Challenging Words' else 'B'])
            else:
                line = join(items)
                if re.fullmatch(r'(Basic|Challenging) Words', line):
                    section = line
                m = re.search(r'20\d\d\s+(?:Spring|Fall)\s+(.+?)\s+Spelling Bee List', line)
                if m:
                    g = m.group(1).strip()
                    if g.lower() in ('kinder', 'gk'):
                        g = 'GK'
                    if not titles or titles[-1] != g:
                        titles.append(g)
    return entries, titles


def hide(sent, word):
    """예문 속 정답 단어를 {}로 감싼다.

    이전 학기 파일은 정답이 굵은 글씨였지만 이번 파일은 굵기가 아예 없다.
    표시가 없으면 글자를 맞춰 찾는다. 하나라도 놓치면 문제 화면에
    정답이 그대로 보이므로 나온 곳을 모두 감싼다."""
    if '{' in sent:
        return sent
    for pat in (r'\b{}\b', r'\b{}(?:s|es|ed|ing|d)\b'):
        rx = re.compile(pat.format(re.escape(word)), re.I)
        if rx.search(sent):
            return rx.sub(lambda m: '{' + m.group(0) + '}', sent)
    return sent


def split_by_grade(entries, titles):
    """번호가 1로 돌아가는 곳에서 학년을 나눈다."""
    starts = [i for i, e in enumerate(entries) if e[0] == 1]
    grades = {}
    for k, i in enumerate(starts):
        j = starts[k + 1] if k + 1 < len(starts) else len(entries)
        name = titles[k] if k < len(titles) else 'part%d' % (k + 1)
        grades[name] = entries[i:j]
    return grades


entries, titles = parse_all(WORD_PDF)
by_grade = split_by_grade(entries, titles)
print(f'  학년 구간: ' + ', '.join(f'{g}({len(w)})' for g, w in by_grade.items()))

out = {}
for key, grade, label in USE:
    words = by_grade.get(grade)
    assert words, f'{grade}: 이 학년 목록을 찾지 못했다 (있는 것: {list(by_grade)})'
    assert [w[0] for w in words] == list(range(1, len(words) + 1)), f'{grade}: 번호가 끊긴다'
    bad = [w[1] for w in words if not re.fullmatch(r"[A-Za-z'\-]+", w[1])]
    assert not bad, f'{grade}: 단어 셀이 깨졌다 - {bad[:5]}'
    lost = [w[1] for w in words if '{' not in w[2]]
    assert not lost, f'{grade}: 예문에서 정답을 찾지 못했다 - {lost[:5]}'
    # 가린 부분을 빼고도 정답이 남아 있으면 문제 화면에 답이 그대로 보인다.
    leak = [w[1] for w in words
            if re.search(r'\b' + re.escape(w[1]) + r'\b',
                         re.sub(r'\{.*?\}', '', w[2]), re.I)]
    assert not leak, f'{grade}: 예문에 정답이 남는다 - {leak[:5]}'
    out[key] = {'name': label, 'words': words}
    print(f'  {key:8} {len(words):>3}개  {collections.Counter(w[3] for w in words)}')

data = 'const LISTS=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
tpl = io.open('index.template.html', encoding='utf-8').read()
assert '/*__WORDS__*/' in tpl
cfg = io.open('config.js', encoding='utf-8').read()
body = tpl.replace('/*__WORDS__*/', cfg + chr(10) + data)

# --- 글꼴: 실제로 쓰인 글자만 받아 자체 호스팅한다 (오프라인 대비) ---
font_css, font_files = fonts.build([body])
icon_files = icons.build()

# --- 홈 화면 추가용 정보 ---
manifest = {
    "name": "우리집 스펠링비",
    "short_name": "스펠링비",
    "description": "아이들이 스펠링비 대회 단어를 연습하는 앱",
    "lang": "ko",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#EEF1F5",
    "theme_color": "#EEF1F5",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/maskable-512.png", "sizes": "512x512", "type": "image/png",
         "purpose": "maskable"},
    ],
}
io.open('../manifest.webmanifest', 'w', encoding='utf-8').write(
    json.dumps(manifest, ensure_ascii=False, indent=1))

# 온전한 HTML 문서로 감싼다.
# viewport 메타가 없으면 휴대폰이 980px 가상 화면으로 그린 뒤 축소해버려
# 글자와 버튼이 전부 작아지고 미디어 쿼리도 걸리지 않는다.
SHELL = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#EEF1F5" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#131824" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="스펠링비">
<meta name="description" content="아이들이 스펠링비 대회 단어를 연습하는 앱">
<title>우리집 스펠링비</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/icon-180.png">
<link rel="icon" href="icons/icon-192.png">
<style>
__FONTS__
</style>
</head>
<body>
{BODY}
</body>
</html>
"""
doc = SHELL.replace('__FONTS__', font_css).replace('{BODY}', body)
io.open(OUT, 'w', encoding='utf-8').write(doc)

# --- 서비스 워커: 화면을 기기에 저장해 두어 인터넷 없이도 열리게 한다 ---
core = ['./', './index.html', './manifest.webmanifest'] + font_files + icon_files
version = 'sb-' + hashlib.sha1(
    (doc + json.dumps(core)).encode('utf-8')).hexdigest()[:10]
sw = io.open('sw.template.js', encoding='utf-8').read()
sw = sw.replace('__VERSION__', version).replace('__CORE__', json.dumps(core))
io.open('../sw.js', 'w', encoding='utf-8').write(sw)

print(f'-> {OUT}  ({len(doc):,} bytes)')
print(f'-> ../sw.js  (버전 {version}, {len(core)}개 파일 저장)')
