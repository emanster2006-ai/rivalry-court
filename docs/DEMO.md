# Portfolio demo

The public [case study](https://github.com/emanster2006-ai/emanster2006-ai/blob/main/projects/rivalry-court.md) contains screenshots, an animated preview, a 60-second captioned walkthrough, architecture, ownership, and verification limits. It makes the project inspectable while source stays private.

The media shows the actual React UI with synthetic players, scores, and API responses. No production accounts, emails, or records are used. It is not an end-to-end backend verification.

## Reproduce screenshots

From `apps/web`, run `npm ci` then `npm run dev -- --host 127.0.0.1`. In a second terminal, use a Python environment containing Playwright and Chromium, then run from the repository root:

```sh
python scripts/capture_portfolio.py /tmp/rivalry-demo
```

The script uses `/usr/bin/chromium`; adjust the executable path for your machine. It captures five desktop scenes and a 390px mobile layout, checks browser errors and horizontal overflow, and writes a capture manifest. This is a mobile viewport check, not a real-phone test.

The five scenes are: sealed prediction, deadline reveal, score review, confirmation, and calibration. The fixture supports prediction and confirmation only; it is not a standalone demo backend. The 60-second MP4 is a captioned sequence of these screenshots, not a recording of real gameplay.
