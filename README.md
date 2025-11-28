# ChromeForge — Prototype Chrome Extension Generator

This repository contains a prototype generator `chrome_forge.py` that accepts an English description of a desired Chrome extension and emits a ready-to-load extension folder at `generated_extension/`.

**Files included**
- `chrome_forge.py` — main generator script. Run with `python3 chrome_forge.py`.
- `generated_extension/` — sample extension (popup showing today's date).
- `README.md` — this file.

**Assumptions**
- The generator uses keyword-based heuristics (simple NLP). It's not an LLM; it uses regex/keywords to detect required components.
- The output targets Chrome Manifest V3.
- For web-request blocking scenarios, the script may include `declarativeNetRequest` hints; runtime behavior may require additional user consent.

**Feature detection logic (summary)**
- Popup: detected if the prompt mentions `popup`, `button`, `menu`, `click`, or similar.
- Content script: detected if the prompt mentions `highlight`, `modify`, `DOM`, `phone number`, `extract`, `on any website`, etc.
- Background: detected if the prompt mentions `background`, `block`, `alarm`, `timer`, `on startup`, `automate`, etc.
- Permissions: inferred from keywords like `tabs`, `storage`, `scripting`, `webRequest`, `activeTab`, `alarms`.
- CSS: detected if the prompt mentions `css`, `style`, `color`, or `theme`.

**How to use**
1. Run the generator:

```bash
python3 chrome_forge.py
```

2. Enter a natural-language description when prompted. The script will analyze the prompt and create/overwrite `generated_extension/`.

3. Load the generated extension in Chrome:
- Open `chrome://extensions`
- Toggle `Developer mode` on
- Click `Load unpacked` and select the `generated_extension/` folder.

**Two sample prompts**
1. "Create an extension that shows a popup with today's date." — Popup with `popup.html` + `popup.js`.
2. "Make an extension that highlights all phone numbers on any website." — Content script (`content.js`) + required permissions; highlights phone numbers.

**Notes**
- The generated code is intentionally simple and readable for teaching and prototyping.
- If `generated_extension/` already exists, the script moves it to `generated_extension_backup/` before writing a new one.
