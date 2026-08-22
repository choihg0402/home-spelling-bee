"""템플릿에 단어 데이터를 주입해 index.html 생성."""
import io, json, re, collections, sys
import pymupdf

PDF = '../docs/samples/G2-3_Spelling_Bee_List_1.pdf'
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
                                          x0=s['bbox'][0], x1=s['bbox'][2],
                                          t=s['text'], bold='Bold' in s['font']))
    rows = collections.defaultdict(list)
    for s in spans:
        rows[(s['pg'], s['y'])].append(s)
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

words = parse(PDF)
assert len(words) == 200, len(words)
assert all(w[2].count('{') == 1 for w in words)
data = 'const WORDS=' + json.dumps(words, ensure_ascii=False, separators=(',', ':')) + ';'
tpl = io.open('index.template.html', encoding='utf-8').read()
io.open(OUT, 'w', encoding='utf-8').write(tpl.replace('/*__WORDS__*/', data))
print(f'{len(words)} words -> {OUT}')
