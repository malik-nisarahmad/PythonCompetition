# ChromeForge - AI-Powered Chrome Extension Generator

**FAST University Tech Society Project**  
**Version:** 1.0.0

A pure Python program that generates complete, loadable Chrome extensions from natural language descriptions using Manifest V3.

---

## 📁 Deliverables

| File | Description |
|------|-------------|
| `chrome_forge.py` | Main generator script (Parts A–D implementation) |
| `generated_extension/` | Sample generated extension (popup with today's date) |
| `README.md` | This documentation file |
| `test_chrome_forge.py` | Comprehensive test suite (14 test cases, 100% pass rate) |

---

## 🎯 Assumptions

1. **Keyword-based NLP**: The generator uses deterministic keyword matching with confidence scoring for reproducibility.
2. **Manifest V3**: All generated extensions target Chrome Manifest V3 (current standard).
3. **Single prompt input**: The system takes one English prompt and generates all required files automatically.
4. **Permissions inference**: Based on detected keywords like `tabs`, `storage`, `block`, `alarm`, etc.
5. **Modular architecture**: Four-part pipeline (Analysis → Manifest → Code → Files).

---

## 🧠 Feature Detection Logic

### Part A: Prompt Analysis Engine

The system analyzes prompts using:

#### Intent Classification (with confidence scoring)
| Intent | Keywords | Threshold |
|--------|----------|-----------|
| UI Interaction | popup, button, menu, display, show, click | 70% |
| Content Modification | highlight, modify, change, webpage, extract, find | 60% |
| Background Automation | block, alarm, timer, schedule, automate | 70% |
| Data Storage | save, store, remember, settings, preferences | 60% |
| Browser Integration | tabs, navigation, url, bookmarks | 70% |

#### Entity Recognition Patterns
- **Target websites**: Regex for domain names (facebook.com, etc.)
- **Visual elements**: color, style, theme, highlight
- **Data elements**: date, time, phone, email
- **Time patterns**: 9 AM, work hours, every minute

#### Permission Mapping
| Permission | Trigger Keywords |
|------------|------------------|
| `activeTab` | current page, this website |
| `tabs` | all tabs, browser tabs |
| `storage` | save, store, remember |
| `declarativeNetRequest` | block, blocking, filter |
| `alarms` | alarm, timer, schedule |
| `scripting` | inject, execute script |

---

## 🔧 How to Test the Extension

### Step 1: Run the Generator

```bash
# Interactive mode
python3 chrome_forge.py

# Or with command-line argument
python3 chrome_forge.py "Create an extension that shows a popup with today's date."
```

### Step 2: Load in Chrome

1. Open Chrome and navigate to `chrome://extensions`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `generated_extension/` folder
5. The extension icon appears in your toolbar — click to test!

### Step 3: Run Automated Tests

```bash
python3 test_chrome_forge.py
```

This runs 14 comprehensive test cases covering all scenarios from the specification.

---

## 📝 Sample Prompts

### Sample 1: Popup with Today's Date
```
Create an extension that shows a popup with today's date.
```
**Generated files**: `manifest.json`, `popup.html`, `popup.js`, `styles.css`  
**Behavior**: Clicking the extension icon shows a popup with formatted date/time.

### Sample 2: Highlight Phone Numbers
```
Make an extension that highlights all phone numbers on any website.
```
**Generated files**: `manifest.json`, `content.js`, `styles.css`  
**Behavior**: Automatically highlights phone numbers (yellow background) on every webpage.

### Sample 3: Block Social Media
```
Block Facebook and TikTok every time the browser opens.
```
**Generated files**: `manifest.json`, `background.js`, `rules.json`  
**Permissions**: `declarativeNetRequest`, `declarativeNetRequestWithHostAccess`  
**Behavior**: Blocks access to specified sites using declarativeNetRequest API.

### Sample 4: Change Text Color via Popup
```
A tool that changes all webpage text to blue when I click a button in the popup.
```
**Generated files**: `manifest.json`, `popup.html`, `popup.js`, `content.js`, `styles.css`  
**Behavior**: Popup button sends message to content script → content script changes page text color.

### Sample 5: Time-Based Blocking
```
Build an extension that blocks access to social media sites during work hours (9 AM to 5 PM).
```
**Generated files**: `manifest.json`, `background.js`, `rules.json`  
**Permissions**: `declarativeNetRequest`, `alarms`  
**Behavior**: Uses alarms API to enable/disable blocking based on time of day.

---

## 🏗️ Technical Architecture

### Four-Part Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PART A        │     │   PART B        │     │   PART C        │     │   PART D        │
│ Prompt Analysis │ --> │ Manifest Build  │ --> │ Code Generation │ --> │ File Output     │
│                 │     │                 │     │                 │     │                 │
│ - Tokenization  │     │ - MV3 Schema    │     │ - popup.html    │     │ - Directory     │
│ - Intent Class. │     │ - Permissions   │     │ - popup.js      │     │ - Write Files   │
│ - Entity Recog. │     │ - Validation    │     │ - content.js    │     │ - Validation    │
│ - Feature Det.  │     │                 │     │ - background.js │     │ - Backup        │
└─────────────────┘     └─────────────────┘     │ - styles.css    │     └─────────────────┘
                                                └─────────────────┘
```

### Generated Manifest Structure (Manifest V3)
```json
{
  "manifest_version": 3,
  "name": "<derived from prompt>",
  "version": "1.0.0",
  "description": "Auto-generated extension",
  "action": { "default_popup": "popup.html" },
  "permissions": ["<inferred>"],
  "background": { "service_worker": "background.js" },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "run_at": "document_idle"
  }]
}
```

---

## ✅ Test Results

```
=================================================================
   ChromeForge v1.0.0 - COMPREHENSIVE TEST SUITE
=================================================================

[TEST 01] Popup with today's date              ✓ PASSED
[TEST 02] Highlight phone numbers              ✓ PASSED
[TEST 03] Block social media sites             ✓ PASSED
[TEST 04] Change text color via popup          ✓ PASSED
[TEST 05] Real-time date with refresh          ✓ PASSED
[TEST 06] Highlight email addresses            ✓ PASSED
[TEST 07] Time-based site blocking             ✓ PASSED
[TEST 08] Extension with storage               ✓ PASSED
[TEST 09] Extension with alarms                ✓ PASSED
[TEST 10] Extension with tabs                  ✓ PASSED
[TEST 11] Dark mode theme                      ✓ PASSED
[TEST 12] Empty prompt default behavior        ✓ PASSED
[TEST 13] Extract data from page               ✓ PASSED
[TEST 14] Block multiple sites                 ✓ PASSED

=================================================================
   ✓ ALL 14 TESTS PASSED (100%)
=================================================================
```

---

## 📋 Notes

- The generator is deterministic — same prompt always produces same output.
- All generated code is minimal, readable, and suitable for learning.
- Extensions are immediately loadable in Chrome without modification.
- Existing `generated_extension/` folders are backed up before regeneration.
- The test suite validates JSON syntax, file presence, and content correctness.

---

## 🚀 Quick Start

```bash
# Clone and navigate
cd /path/to/project

# Generate an extension
python3 chrome_forge.py "Show a popup with today's date"

# Load in Chrome: chrome://extensions → Developer mode → Load unpacked
```
