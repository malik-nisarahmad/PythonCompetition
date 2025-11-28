#!/usr/bin/env python3
"""
test_chrome_forge.py - Comprehensive Test Suite for ChromeForge

Tests all requirements from the JSON specification:
- Part A: Prompt Analysis Engine
- Part B: Manifest Builder
- Part C: Dynamic Code Generation
- Part D: File System Output

Run: python3 test_chrome_forge.py
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

SCRIPT_DIR = Path(__file__).parent
GENERATOR = SCRIPT_DIR / "chrome_forge.py"
OUTPUT_DIR = SCRIPT_DIR / "generated_extension"

# ============================================================================
# TEST CASES - Based on JSON Specification
# ============================================================================

TEST_CASES = [
    # === SCENARIO 1: Popup with date ===
    {
        "id": 1,
        "name": "Popup with today's date",
        "prompt": "Create an extension that shows a popup with today's date.",
        "expect_files": ["manifest.json", "popup.html", "popup.js", "styles.css"],
        "expect_no_files": ["content.js", "background.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "action.default_popup": "popup.html",
        },
        "content_checks": {
            "popup.js": ["Date", "toLocale"],
        },
    },
    
    # === SCENARIO 2: Highlight phone numbers ===
    {
        "id": 2,
        "name": "Highlight phone numbers",
        "prompt": "Make an extension that highlights all phone numbers on any website.",
        "expect_files": ["manifest.json", "content.js", "styles.css"],
        "manifest_checks": {
            "manifest_version": 3,
            "content_scripts": True,
        },
        "content_checks": {
            "content.js": ["PHONE", "highlight"],
        },
    },
    
    # === SCENARIO 3: Block Facebook and TikTok ===
    {
        "id": 3,
        "name": "Block social media sites",
        "prompt": "Block Facebook and TikTok every time the browser opens.",
        "expect_files": ["manifest.json", "background.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "background.service_worker": "background.js",
        },
        "content_checks": {
            "background.js": ["block", "facebook"],
        },
    },
    
    # === SCENARIO 4: Change text to blue via popup ===
    {
        "id": 4,
        "name": "Change text color via popup",
        "prompt": "A tool that changes all webpage text to blue when I click a button in the popup.",
        "expect_files": ["manifest.json", "popup.html", "popup.js", "content.js", "styles.css"],
        "manifest_checks": {
            "manifest_version": 3,
            "action.default_popup": "popup.html",
            "content_scripts": True,
        },
        "content_checks": {
            "popup.js": ["sendMessage", "blue"],
            "content.js": ["onMessage", "color"],
        },
    },
    
    # === SCENARIO 5: Date with refresh timer ===
    {
        "id": 5,
        "name": "Real-time date with refresh",
        "prompt": "Create an extension that shows a popup with today's date and time in a large font, with a button to refresh the time every second.",
        "expect_files": ["manifest.json", "popup.html", "popup.js", "styles.css"],
        "manifest_checks": {
            "manifest_version": 3,
        },
        "content_checks": {
            "popup.js": ["Date", "setInterval"],
        },
    },
    
    # === SCENARIO 6: Email highlighting ===
    {
        "id": 6,
        "name": "Highlight email addresses",
        "prompt": "Make an extension that highlights all email addresses on any website in green color.",
        "expect_files": ["manifest.json", "content.js", "styles.css"],
        "manifest_checks": {
            "manifest_version": 3,
            "content_scripts": True,
        },
        "content_checks": {
            "content.js": ["EMAIL", "highlight"],
        },
    },
    
    # === SCENARIO 7: Time-based blocking ===
    {
        "id": 7,
        "name": "Time-based site blocking",
        "prompt": "Build an extension that blocks access to social media sites during work hours (9 AM to 5 PM).",
        "expect_files": ["manifest.json", "background.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "background.service_worker": "background.js",
        },
        "content_checks": {
            "background.js": ["block", "hour"],
        },
    },
    
    # === SCENARIO 8: Storage permissions ===
    {
        "id": 8,
        "name": "Extension with storage",
        "prompt": "An extension that saves notes to local storage with a popup.",
        "expect_files": ["manifest.json", "popup.html", "popup.js", "styles.css"],
        "manifest_checks": {
            "manifest_version": 3,
            "permissions": lambda p: p is not None and "storage" in p,
        },
    },
    
    # === SCENARIO 9: Alarms/Timer ===
    {
        "id": 9,
        "name": "Extension with alarms",
        "prompt": "Create an alarm that fires every 5 minutes in the background.",
        "expect_files": ["manifest.json", "background.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "permissions": lambda p: p is not None and "alarms" in p,
        },
    },
    
    # === SCENARIO 10: Tabs permission ===
    {
        "id": 10,
        "name": "Extension with tabs",
        "prompt": "Show all open tabs in a popup.",
        "expect_files": ["manifest.json", "popup.html", "popup.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "permissions": lambda p: p is not None and "tabs" in p,
        },
    },
    
    # === SCENARIO 11: Dark mode theme ===
    {
        "id": 11,
        "name": "Dark mode theme",
        "prompt": "A dark mode theme for all webpages.",
        "expect_files": ["manifest.json", "content.js", "styles.css"],
        "manifest_checks": {
            "manifest_version": 3,
            "content_scripts": True,
        },
    },
    
    # === SCENARIO 12: Empty prompt (default) ===
    {
        "id": 12,
        "name": "Empty prompt default behavior",
        "prompt": "",
        "expect_files": ["manifest.json", "popup.html", "popup.js"],
        "manifest_checks": {
            "manifest_version": 3,
        },
    },
    
    # === SCENARIO 13: Extract data ===
    {
        "id": 13,
        "name": "Extract data from page",
        "prompt": "Extract all email addresses from the current webpage.",
        "expect_files": ["manifest.json", "content.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "content_scripts": True,
        },
    },
    
    # === SCENARIO 14: Multiple blocked sites ===
    {
        "id": 14,
        "name": "Block multiple sites",
        "prompt": "Block Facebook, Twitter, and Instagram.",
        "expect_files": ["manifest.json", "background.js"],
        "manifest_checks": {
            "manifest_version": 3,
            "background.service_worker": "background.js",
        },
    },
]


def run_generator(prompt: str) -> bool:
    """Run chrome_forge.py with the given prompt."""
    try:
        cmd = [sys.executable, str(GENERATOR)]
        if prompt:
            cmd.append(prompt)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            input="" if not prompt else None,
        )
        
        if result.returncode != 0:
            print(f"    {RED}Generator failed with code {result.returncode}{RESET}")
            if result.stderr:
                print(f"    STDERR: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        print(f"    {RED}Exception: {e}{RESET}")
        return False


def validate_json(filepath: Path) -> tuple:
    """Validate JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return True, data
    except json.JSONDecodeError as e:
        return False, str(e)


def check_manifest(manifest: dict, checks: dict) -> list:
    """Check manifest against expected values."""
    errors = []
    for key, expected in checks.items():
        # Handle nested keys
        parts = key.split('.')
        val = manifest
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                val = None
                break
        
        if callable(expected):
            if not expected(val):
                errors.append(f"manifest[{key}] failed custom check (value: {val})")
        elif expected is True:
            if val is None:
                errors.append(f"manifest[{key}] expected to exist but missing")
        elif val != expected:
            errors.append(f"manifest[{key}] = {val}, expected {expected}")
    return errors


def check_file_content(filepath: Path, must_contain: list) -> list:
    """Check file contains required strings."""
    if not filepath.exists():
        return [f"File {filepath.name} does not exist"]
    content = filepath.read_text()
    missing = []
    for item in must_contain:
        if item.lower() not in content.lower():
            missing.append(f"'{item}' not found in {filepath.name}")
    return missing


def run_test(test: dict) -> tuple:
    """Run a single test case."""
    errors = []
    
    # Clean output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    # Run generator
    if not run_generator(test["prompt"]):
        return False, ["Generator execution failed"]
    
    # Check output directory exists
    if not OUTPUT_DIR.exists():
        return False, ["Output directory not created"]
    
    # Check expected files exist
    for fname in test.get("expect_files", []):
        fpath = OUTPUT_DIR / fname
        if not fpath.exists():
            errors.append(f"Expected file missing: {fname}")
    
    # Check unexpected files do NOT exist
    for fname in test.get("expect_no_files", []):
        fpath = OUTPUT_DIR / fname
        if fpath.exists():
            errors.append(f"Unexpected file present: {fname}")
    
    # Validate manifest.json
    manifest_path = OUTPUT_DIR / "manifest.json"
    if manifest_path.exists():
        valid, data = validate_json(manifest_path)
        if not valid:
            errors.append(f"manifest.json invalid JSON: {data}")
        else:
            # Check manifest fields
            manifest_errors = check_manifest(data, test.get("manifest_checks", {}))
            errors.extend(manifest_errors)
            
            # CRITICAL: manifest_version MUST be 3
            if data.get("manifest_version") != 3:
                errors.append(f"CRITICAL: manifest_version is {data.get('manifest_version')}, must be 3")
            
            # CRITICAL: name and version must exist
            if not data.get("name"):
                errors.append("CRITICAL: manifest missing 'name'")
            if not data.get("version"):
                errors.append("CRITICAL: manifest missing 'version'")
    else:
        errors.append("manifest.json not found")
    
    # Check file contents
    for fname, must_contain in test.get("content_checks", {}).items():
        fpath = OUTPUT_DIR / fname
        content_errors = check_file_content(fpath, must_contain)
        errors.extend(content_errors)
    
    # Validate JS files have balanced braces
    for js_file in OUTPUT_DIR.glob("*.js"):
        content = js_file.read_text()
        if content.count('{') != content.count('}'):
            errors.append(f"{js_file.name}: Unbalanced curly braces")
        if content.count('(') != content.count(')'):
            errors.append(f"{js_file.name}: Unbalanced parentheses")
    
    # Validate HTML files
    for html_file in OUTPUT_DIR.glob("*.html"):
        content = html_file.read_text()
        if "<!DOCTYPE html>" not in content and "<!doctype html>" not in content:
            errors.append(f"{html_file.name}: Missing DOCTYPE")
        if "</html>" not in content:
            errors.append(f"{html_file.name}: Missing closing </html> tag")
    
    return len(errors) == 0, errors


def main():
    print(f"\n{BOLD}{'='*65}{RESET}")
    print(f"{BOLD}   ChromeForge v1.0.0 - COMPREHENSIVE TEST SUITE{RESET}")
    print(f"{BOLD}   JSON Specification Validation{RESET}")
    print(f"{BOLD}{'='*65}{RESET}\n")
    
    # Check generator exists
    if not GENERATOR.exists():
        print(f"{RED}ERROR: chrome_forge.py not found!{RESET}")
        sys.exit(1)
    
    # Check generator has no syntax errors
    print(f"{YELLOW}[PRE-CHECK] Validating chrome_forge.py syntax...{RESET}")
    result = subprocess.run([sys.executable, "-m", "py_compile", str(GENERATOR)], capture_output=True)
    if result.returncode != 0:
        print(f"{RED}SYNTAX ERROR in chrome_forge.py:{RESET}")
        print(result.stderr.decode())
        sys.exit(1)
    print(f"{GREEN}✓ No syntax errors{RESET}\n")
    
    passed = 0
    failed = 0
    
    for test in TEST_CASES:
        test_id = test["id"]
        test_name = test["name"]
        prompt_preview = test["prompt"][:40] + "..." if len(test["prompt"]) > 40 else test["prompt"]
        if not prompt_preview:
            prompt_preview = "(empty prompt - default)"
        
        print(f"{BOLD}[TEST {test_id:02d}]{RESET} {test_name}")
        print(f"         {BLUE}Prompt: {prompt_preview}{RESET}")
        
        success, errors = run_test(test)
        
        if success:
            print(f"         {GREEN}✓ PASSED{RESET}")
            passed += 1
        else:
            print(f"         {RED}✗ FAILED{RESET}")
            for err in errors[:3]:  # Show max 3 errors
                print(f"           - {err}")
            if len(errors) > 3:
                print(f"           - ...and {len(errors) - 3} more errors")
            failed += 1
        print()
    
    # Summary
    print(f"{BOLD}{'='*65}{RESET}")
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    if failed == 0:
        print(f"{BOLD}   {GREEN}✓ ALL {passed} TESTS PASSED ({pass_rate:.0f}%){RESET}")
    else:
        print(f"{BOLD}   RESULTS: {GREEN}{passed} PASSED{RESET}, {RED}{failed} FAILED{RESET} ({pass_rate:.0f}%)")
    print(f"{BOLD}{'='*65}{RESET}")
    
    if failed > 0:
        print(f"\n{YELLOW}⚠ Some tests failed. Review and fix issues above.{RESET}")
        sys.exit(1)
    else:
        print(f"\n{GREEN}✓ ChromeForge is fully validated and ready for submission!{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
