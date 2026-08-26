-- 도우미가 받은 질문과 내놓은 답을 남긴다.
-- 무엇을 자주 묻는지, 무엇을 못 답했는지 보고 사이트와 프롬프트를 고치기 위한 것이다.
-- 적용: npx wrangler d1 execute hai-ask-log --remote --file tools/ask_log_schema.sql
CREATE TABLE IF NOT EXISTS ask (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  at       TEXT    NOT NULL,          -- ISO8601 UTC
  question TEXT    NOT NULL,
  answer   TEXT,
  ms       INTEGER,                   -- 답하는 데 걸린 시간
  turn     INTEGER,                   -- 그 대화의 몇 번째 질문인지
  ok       INTEGER NOT NULL DEFAULT 1,-- 1 정상, 0 오류
  punt     INTEGER NOT NULL DEFAULT 0 -- 이메일로 넘긴 답이면 1 (못 답한 질문 찾기용)
);
CREATE INDEX IF NOT EXISTS ask_at   ON ask(at);
CREATE INDEX IF NOT EXISTS ask_punt ON ask(punt, at);
