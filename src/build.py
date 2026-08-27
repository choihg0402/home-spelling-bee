"""템플릿에 단어 데이터를 주입해 index.html 생성."""
import io, json, re, collections, sys
import pymupdf

LISTS = [
    ('g23',    '2026 Spring G2–G3', '../docs/samples/G2-3_Spelling_Bee_List_1.pdf'),
    ('kinder', '2026 Spring Kinder',      '../docs/samples/Kinder_Spelling_Bee_List.pdf'),
]
OUT = '../index.html'
def parse(path):
    doc = pymupdf.open(path)
    spans = []
    for pno, page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for s in line['spans']:
                    if s['text'].strip():
                        spans.append(dict(pg=pno, y=round(s['bbox'][1], 1),
                                          yc=(s['bbox'][1] + s['bbox'][3]) / 2,
                                          x0=s['bbox'][0], x1=s['bbox'][2],
                                          t=s['text'], bold='Bold' in s['font']))
    # 같은 줄이라도 조각마다 y가 1pt 안팎으로 어긋난다(번호가 단어보다 살짝 내려앉는 PDF가 있다).
    # 정확히 같은 y로 묶으면 번호가 떨어져 나가므로 허용 오차를 두고 묶는다.
    TOL = 6.0
    rows = {}
    for s in sorted(spans, key=lambda s: (s['pg'], s['yc'], s['x0'])):
        key = next((k for k in rows
                    if k[0] == s['pg'] and abs(k[1] - s['yc']) <= TOL), None)
        if key is None:
            key = (s['pg'], s['yc'])
            rows[key] = []
        rows[key].append(s)
    for k in rows:
        rows[k].sort(key=lambda s: s['x0'])

    # 예문 열의 왼쪽 끝을 문서에서 직접 구한다 (기획서 §4.5-1)
    sent_x = collections.Counter(round(s['x0'], 1) for s in spans).most_common(1)[0][0] - 2

    def join(items, mark=False):
        out = ''
        for i, s in enumerate(items):
            if i and (s['x0'] - items[i - 1]['x1']) > 0.8:
                out += ' '
            t = s['t']
            out += ('{' + t.strip() + '}') if (mark and s['bold'] and t.strip()) else t
        return re.sub(r'\s+', ' ', out).strip()

    entries, section = [], None
    for key in sorted(rows):
        items = rows[key]
        left = [s for s in items if s['x0'] < sent_x]
        sent = [s for s in items if s['x0'] >= sent_x]
        if left and re.fullmatch(r'\d+', left[0]['t'].strip()) and len(left) > 1:
            entries.append([int(left[0]['t']), join(left[1:]), join(sent, mark=True),
                            'C' if section == 'Challenging Words' else 'B'])
        else:
            line = join(items)
            if re.fullmatch(r'(Basic|Challenging) Words', line):
                section = line
    return entries

out = {}
for key, label, path in LISTS:
    words = parse(path)
    assert words, f'{key}: 단어를 하나도 뽑지 못했다'
    assert [w[0] for w in words] == list(range(1, len(words) + 1)), f'{key}: 번호가 끊긴다'
    assert all(re.fullmatch(r"[A-Za-z'\-]+", w[1]) for w in words), f'{key}: 단어 셀이 깨졌다'
    assert all(w[2].count('{') == 1 for w in words), f'{key}: 예문 강조 표시가 맞지 않는다'
    out[key] = {'name': label, 'words': words}
    print(f'  {key:8} {len(words):>3}개  {collections.Counter(w[3] for w in words)}')

data = 'const LISTS=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';'
tpl = io.open('index.template.html', encoding='utf-8').read()
assert '/*__WORDS__*/' in tpl

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
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%90%9D%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jua&family=Gowun+Dodum&family=Fredoka:wght@400;500;600&display=swap">
</head>
<body>
{BODY}
</body>
</html>
"""
doc = SHELL.replace('{BODY}', tpl.replace('/*__WORDS__*/', data))
io.open(OUT, 'w', encoding='utf-8').write(doc)
print(f'-> {OUT}  ({len(doc):,} bytes)')
