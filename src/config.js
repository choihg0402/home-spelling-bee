/* 서버 설정. 빌드할 때 index.html 안으로 들어간다.
   공개 키는 원래 브라우저에 노출되는 값이라 저장소에 있어도 안전하다.
   실제 보호는 서버 쪽 행 단위 보안(docs/서버-설정.sql)이 한다.
   비밀번호는 절대 여기 넣지 않는다. 기기마다 부모가 직접 입력한다. */
const SB = {
  url:   'https://hwkhejwrvoktovpnorrr.supabase.co',
  key:   'sb_publishable_oS-NdqYr7dCersdJPmF1Lg_9vKviTFf',
  email: 'family@spellingbee.home'    // 가족 계정. 실제로 메일을 받지 않는다
};
