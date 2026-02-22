# Image Processing

A skill for image format conversion, optimization, resizing, cropping, and canvas extension using the `slimg` CLI.

## Available Commands

### Format Conversion

Convert images between formats (JPEG, PNG, WebP, AVIF, QOI, JPEG XL).

```bash
slimg convert <input> --format <format>
slimg convert <input> --format webp --quality 80
slimg convert <input> --format avif --output <output>
```

Supported formats: `jpeg`, `png`, `webp`, `avif`, `jxl`, `qoi`

### Image Optimization

Re-encode in the same format to reduce file size.

```bash
slimg optimize <input>
slimg optimize <input> --quality 70
slimg optimize <input> --output <output>
```

### Resize

Scale images by width, height, or scale factor. Aspect ratio is always preserved.

```bash
slimg resize <input> --width 800
slimg resize <input> --height 600
slimg resize <input> --width 800 --height 600
slimg resize <input> --scale 0.5
slimg resize <input> --width 800 --format webp --output <output>
```

### Crop

Extract a region by pixel coordinates or crop to a specific aspect ratio (center-anchored).

```bash
slimg crop <input> --region 100,50,800,600
slimg crop <input> --aspect 16:9
slimg crop <input> --aspect 1:1 --output <output>
```

`--region` format: `x,y,width,height`. `--region` and `--aspect` are mutually exclusive.

### Extend (Add Padding/Canvas)

Add padding around an image to reach a target aspect ratio or size.

```bash
slimg extend <input> --aspect 1:1
slimg extend <input> --aspect 1:1 --transparent
slimg extend <input> --size 1920x1080 --color ff0000
slimg extend <input> --size 1920x1080 --output <output>
```

`--transparent` works with PNG, WebP, AVIF only (not JPEG). `--aspect` and `--size` are mutually exclusive.

### Batch Processing

All commands support directory input with `--recursive` and parallel processing with `--jobs`.

```bash
slimg convert ./images --format webp --recursive --output ./output
slimg optimize ./images --recursive --jobs 4
```

## Common Options

| Option | Description |
|--------|-------------|
| `--format`, `-f` | Target format (jpeg, png, webp, avif, jxl, qoi) |
| `--quality`, `-q` | Encoding quality 0-100 (default: 80) |
| `--output`, `-o` | Output path (file or directory) |
| `--recursive` | Process subdirectories |
| `--jobs`, `-j` | Number of parallel jobs |
| `--overwrite` | Replace existing files |

## Usage Guidelines

- Input and output files should be in the workspace/ directory.
- When the user sends an image, it is saved to the workspace automatically. Use that path as input.
- Always use `--output` to save results to workspace/ rather than overwriting the original unless the user explicitly asks to overwrite.
- After processing, inform the user of the output file path so they can retrieve it with `/send`.
- When the user does not specify quality, use the default (80). Only adjust quality when explicitly requested.
- For format conversion, recommend WebP for general web use and AVIF for maximum compression.
