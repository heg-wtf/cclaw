# Image Processing Skill Guide

A guide to installing and using the built-in Image Processing skill for cclaw.

## Overview

The Image skill is a CLI-based skill that lets you convert, optimize, resize, crop, and extend images through your Telegram bot.
It uses the [slimg](https://github.com/clroot/slimg) CLI, a fast Rust-based image optimization tool.

### Key Features

- Format conversion (JPEG, PNG, WebP, AVIF, JPEG XL, QOI)
- Image optimization (re-encode to reduce file size)
- Resize by width, height, or scale factor
- Crop by pixel region or aspect ratio
- Extend canvas with padding (solid color or transparent)
- Batch processing with parallel jobs

## Prerequisites

### Install slimg

Install via Homebrew:

```bash
brew install clroot/tap/slimg
```

Verify the installation:

```bash
slimg --help
```

## Installation & Setup

### 1. Install the Built-in Skill

```bash
cclaw skills install image
```

This creates `SKILL.md` and `skill.yaml` in `~/.cclaw/skills/image/`.

### 2. Setup (Activate)

```bash
cclaw skills setup image
```

This checks if `slimg` is available in your PATH. If requirements are met, the skill status changes to `active`.

### 3. Attach the Skill to a Bot

Via Telegram:
```
/skills attach image
```

### 4. Verify

```bash
cclaw skills
```

Expected output:
```
image (cli) <- my-bot
```

## Usage

After attaching the skill to a bot, send images to the bot and request transformations via natural language.

### Convert Format

```
Convert this photo to WebP
Convert the image to AVIF for maximum compression
```

### Optimize

```
Optimize this image for smaller file size
Optimize with quality 60
```

### Resize

```
Resize the image to 800px width
Scale this image to 50%
Resize to 1200x800
```

### Crop

```
Crop this image to 16:9
Crop to a square
```

### Extend Canvas

```
Add padding to make this image square
Extend to 1920x1080 with a white background
```

### Retrieve Results

After processing, the bot will tell you the output file path. Use `/send` to retrieve:

```
/send output.webp
```

## How It Works

### allowed_tools

The `allowed_tools` configuration in skill.yaml:

```yaml
allowed_tools:
  - "Bash(slimg:*)"
```

This is passed to Claude Code via the `--allowedTools` flag, allowing `slimg` commands to run without permission prompts.

### SKILL.md Instructions

SKILL.md contains guidelines for Claude to follow:

- Use workspace/ directory for input and output files
- Preserve original files by default (use `--output` for results)
- Inform users of the output path so they can retrieve files with `/send`
- Use sensible defaults (quality 80) unless explicitly overridden

### File Workflow

1. User sends a photo/document to the bot (saved to workspace automatically)
2. User requests a transformation in natural language
3. Claude runs `slimg` with appropriate options
4. Bot reports the output file path
5. User retrieves the result with `/send <filename>`

## Troubleshooting

### slimg command not found

```
cclaw skills setup image
# Error: required command 'slimg' not found
```

**Solution**: Install via Homebrew:

```bash
brew install clroot/tap/slimg
which slimg
# Should output: /opt/homebrew/bin/slimg
```

### Bot responds with "permission denied" or hangs

**Cause**: Claude Code requires user approval before running `slimg`, but the bot runs in a non-interactive environment.

**Solution**: Verify that `Bash(slimg:*)` is included in `allowed_tools` in skill.yaml.

```bash
cat ~/.cclaw/skills/image/skill.yaml
```

If `allowed_tools` is present, re-activate with `cclaw skills setup image`.

### Output file not found

**Cause**: The output was saved outside the workspace directory.

**Solution**: Always use `/files` to list workspace files, then `/send <filename>` to retrieve.
