# Gemini Web Skill — Self Tests (executed)

Date: 2026-02-03

## Test 1 — Mode switch: Pro
- Action: Open mode picker, select Pro, re-open menu to verify ✅.
- Result: PASS. Menu shows `Pro` checked.

## Test 2 — Tool: Deep Research enable/disable
- Action: Tools → Deep Research, verify input placeholder becomes "What do you want to research?" and chip shows `Deselect Deep Research`.
- Result: PASS. Deep Research chip appeared.
- Note: Deep Research may open a "Start a new chat?" dialog; toggle ON and click New chat.

## Test 3 — Tool: Create images
- Action: Tools → Create images, verify input placeholder becomes "Describe your image" and chip shows `Deselect Image`.
- Result: PASS.

## Test 4 — Copy image → Clipboard export
- Action: Click `Copy image` on generated image; export clipboard PNG via `export_clipboard_png.scpt`.
- Output: `~/Downloads/gemini_web_test_copy_image.png` (1024×1024)
- Result: PASS.

## Test 5 — Download full size image → Extract from temp artifacts
- Action: Click `Download full size image`; run `grab_latest_openclaw_download.py` to copy to Downloads.
- Output: `~/Downloads/gemini_web_test_fullsize.png` (2816×1536)
- Result: PASS.

## Operational note
- OpenClaw-controlled Chrome downloads typically land in `/var/folders/.../T/playwright-artifacts-*/<uuid>`; copy out quickly.
