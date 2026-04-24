# Gmail

`gog` CLI로 Gmail 조작. **Always confirm with user before sending** (수신자·제목·본문 확인 후 승인). 삭제 금지 (archive 사용).

## Commands

```
gog gmail search 'query' [--limit N] [--json]
  query: newer_than:1d, from:email, subject:keyword, is:unread, has:attachment, label:name
gog gmail message get <messageId> [--json]
gog gmail thread get <threadId> [--json]
gog gmail send --to 'email' --subject 'sub' --body 'body' [--cc] [--bcc] [--attach path]
gog gmail send --to 'email' --subject 'Re: ...' --body 'text' --thread <threadId> --in-reply-to <messageId>
gog gmail labels list [--json]
gog gmail message label <messageId> --add|--remove 'LabelName'
gog gmail message label <messageId> --remove 'INBOX'   # archive
gog gmail drafts list [--limit N] [--json]
gog gmail drafts create --to 'email' --subject 'sub' --body 'body'
```

## Notes
- `--json`: 구조화된 파싱 필요시
- 최근 메일: `newer_than:1d` 또는 `newer_than:7d`
- 필터/위임 설정 변경 금지
- 전달/답장 시 수신자 재확인
