# Translate

`translatecli`로 텍스트/파일 번역. Gemini 기반, 원본 형식(Markdown, SRT, JSON, 텍스트) 보존.

## Commands

```bash
translatecli "Hello, world!" -t ko
translatecli "안녕하세요" -t en
echo "번역할 텍스트" | translatecli -t en
translatecli notes.txt -t ko [-o notes_ko.txt]
translatecli transcript.md -t ko --sttcli [-o transcript_ja.md]    # sttcli 전사 파일 (타임스탬프·화자 보존)
```

## Options
- `-t LANG`: 대상 언어 — ISO 코드(`ko`, `en`, `ja`) 또는 이름(`Korean`) [필수]
- `--sttcli`: sttcli 출력 형식 자동 감지 (Markdown/SRT/JSON/text)
- `-o FILE`: 출력 파일 (기본: stdout)

## Notes
- 텔레그램 파일 번역 시 파일 경로 직접 전달
- 긴 텍스트는 파일로 저장 후 번역
