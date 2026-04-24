# Image Processing

`slimg` CLI로 이미지 포맷 변환, 최적화, 리사이즈, 크롭, 캔버스 확장.

## Commands

```bash
# 포맷 변환 (jpeg, png, webp, avif, jxl, qoi)
slimg convert <input> --format webp [--quality 80] [--output <out>]

# 최적화 (동일 포맷 재인코딩)
slimg optimize <input> [--quality 70] [--output <out>]

# 리사이즈 (비율 유지)
slimg resize <input> --width 800 [--height 600] [--scale 0.5] [--format webp] [--output <out>]

# 크롭 (--region x,y,w,h 또는 --aspect 16:9, 상호 배타)
slimg crop <input> --region 100,50,800,600 [--output <out>]
slimg crop <input> --aspect 1:1 [--output <out>]

# 캔버스 확장 (--aspect 또는 --size, 상호 배타)
slimg extend <input> --aspect 1:1 [--transparent] [--color ff0000] [--output <out>]
slimg extend <input> --size 1920x1080 [--output <out>]

# 배치 처리
slimg convert ./images --format webp --recursive [--jobs 4] --output ./output
```

## Notes
- 입출력 파일은 workspace/ 디렉토리 사용
- 사용자가 보낸 이미지는 workspace/에 자동 저장됨, 해당 경로를 input으로 사용
- 원본 덮어쓰기 방지: `--output`으로 별도 저장 (사용자가 덮어쓰기 요청 시에만 `--overwrite`)
- 처리 후 출력 경로 안내 → `/send`로 전송
- `--transparent`: PNG, WebP, AVIF만 지원 (JPEG 불가)
- quality 미지정 시 기본값 80 사용
