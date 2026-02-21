# Naver Map Skill Guide

A skill that generates Naver Map web URLs to provide clickable place search and route navigation links in Telegram.

## Installation

```bash
cclaw skills install naver-map
```

## Usage

Attach the skill in Telegram and ask place/route related questions.

```
/skills attach naver-map
Search for Gangnam Station
Find cafes near Hongdae
How do I get from Seoul Station to Gangnam Station?
```

The bot generates clickable Naver Map links in its response.

## Supported Features

- **Place Search**: Search Naver Map by keyword (no coordinates needed)
- **Coordinate Place Display**: Show specific location by latitude/longitude
- **Route Navigation**: Car, public transit, and walking routes between origin and destination
- **Search-Based Directions**: Directions by place name without coordinates

## Skill Type

`knowledge` — No CLI tools or external dependencies required. Works solely with URL generation knowledge from SKILL.md.

## Technical Notes

- Telegram does not support `nmap://` custom URL schemes (`<a href>` and InlineKeyboardButton both fail).
- Therefore, `https://map.naver.com` web URLs are used.
- On mobile, if the Naver Maps app is installed, Universal Link/App Link will open the app directly.
