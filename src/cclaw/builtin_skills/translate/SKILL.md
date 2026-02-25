# Translate

Text and transcript translation via `translatecli`. Uses Google Gemini to translate while preserving the original format structure (Markdown, SRT, JSON, plain text).

## Prerequisites

- `translatecli` installed (`uv tool install git+https://github.com/seapy/translatecli.git`)
- Gemini API key (https://aistudio.google.com/apikey)
- `GEMINI_API_KEY` environment variable set during skill setup

## Available Commands

### Translate Plain Text

```bash
translatecli "Hello, world!" -t ko
translatecli "안녕하세요" -t en
translatecli "Bonjour le monde" -t ja
```

### Translate from stdin

```bash
echo "번역할 텍스트" | translatecli -t en
```

### Translate a File

```bash
translatecli notes.txt -t ko
translatecli document.md -t ja
```

### Translate sttcli Transcript

`--sttcli` 옵션으로 sttcli 출력 형식(Markdown, SRT, JSON, text)을 자동 감지하여 타임스탬프와 화자 정보를 보존한 채 번역합니다.

```bash
translatecli transcript.md -t ko --sttcli
translatecli recording.srt -t en --sttcli
```

### Save to File

```bash
translatecli notes.txt -t ko -o notes_ko.txt
translatecli transcript.md -t ja --sttcli -o transcript_ja.md
```

## Options

- `-t, --target LANG`: Target language — ISO code or natural name (e.g. `en`, `ko`, `Japanese`) [required]
- `--sttcli`: Input is sttcli output format (auto-detects Markdown/SRT/JSON/text)
- `-o, --output FILE`: Output file (default: stdout)

## Usage Guidelines

- 사용자가 번역을 요청하면 이 스킬을 사용합니다.
- `-t` 옵션에는 ISO 코드(`ko`, `en`, `ja`, `zh`, `es`, `fr` 등) 또는 언어 이름(`Korean`, `Japanese` 등) 모두 사용 가능합니다.
- 텔레그램에서 받은 파일의 번역이 필요하면, 파일 경로를 직접 전달합니다.
- sttcli로 생성된 음성 전사 파일을 번역할 때는 반드시 `--sttcli` 옵션을 붙여 형식을 보존합니다.
- 긴 텍스트는 파일로 저장 후 번역하는 것이 안정적입니다.
