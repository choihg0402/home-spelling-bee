# 우리집 스펠링비

아이들이 스펠링비 대회 단어를 연습하는 웹앱. 아이패드에서 쓰도록 만들었다.

**앱 열기 → https://choihg0402.github.io/home-spelling-bee/**

## 구조

- 연습장 — 퍼즐(글자 타일), 쓰기. 자유롭게, 감점 없이
- 시험장 — 실제 대회처럼 알파벳을 소리 내어 말하는 테스트
- 마스터 판정은 말하기 테스트로만 올라간다

## 파일

    index.html              배포되는 앱 (단어 데이터 내장, 단일 파일)
    src/index.template.html 원본 템플릿
    src/build.py            PDF에서 단어를 뽑아 index.html 생성

## 다시 빌드

    cd src && python build.py

단어 목록 PDF를 바꾸면 `src/build.py` 의 `PDF` 경로만 고치고 다시 실행하면 된다.
