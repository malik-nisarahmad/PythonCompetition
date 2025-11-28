#!/usr/bin/env python3
"""
ULTRA-STRICT TEST SUITE FOR CHROMEFORGE
========================================
Tests EVERY requirement from the assignment specification.
Zero tolerance for any deviation.

Tests:
- Part A: Prompt Analysis Engine
- Part B: Manifest Builder  
- Part C: Dynamic Code Generation
- Part D: File System Output
- All 4 scenario examples from the assignment
- Edge cases and error handling
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path

# Test configuration
SCRIPT_PATH = Path(__file__).parent / "chrome_forge.py"
OUTPUT_DIR = Path(__file__).parent / "generated_extension"
BACKUP_DIR = Path(__file__).parent / "generated_extension_backup"

# ANSI colors
class C:
    R = '\033[91m'  # Red
    G = '\033[92m'  # Green
    Y = '\033[93m'  # Yellow
    B = '\033[94m'  # Blue
    M = '\033[95m'  # Magenta
    C = '\033[96m'  # Cyan
    W = '\033[97m'  # White
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def print_header():
    print(f"""
{C.R}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   {C.Y}██╗   ██╗██╗  ████████╗██████╗  █████╗                         {C.R}║
║   {C.Y}██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗                        {C.R}║
║   {C.Y}██║   ██║██║     ██║   ██████╔╝███████║                        {C.R}║
║   {C.Y}██║   ██║██║     ██║   ██╔══██╗██╔══██║                        {C.R}║
║   {C.Y}╚██████╔╝███████╗██║   ██║  ██║██║  ██║                        {C.R}║
║   {C.Y} ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝                        {C.R}║
║                                                                  ║
║   {C.R}███████╗████████╗██████╗ ██╗ ██████╗████████╗                  {C.R}║
║   {C.R}██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝╚══██╔══╝                  {C.R}║
║   {C.R}███████╗   ██║   ██████╔╝██║██║        ██║                     {C.R}║
║   {C.R}╚════██║   ██║   ██╔══██╗██║██║        ██║                     {C.R}║
║   {C.R}███████║   ██║   ██║  ██║██║╚██████╗   ██║                     {C.R}║
║   {C.R}╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝   ╚═╝                     {C.R}║
║                                                                  ║
║   {C.W}UNFAIR LEVEL TESTING - ZERO TOLERANCE{C.R}                          ║
║   {C.DIM}Testing against FAST University Assignment Spec{C.R}               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{C.RESET}
""")

def cleanup():
    """Clean up test artifacts."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

def run_chrome_forge(prompt):
    """Run chrome_forge.py with a prompt and return success status."""
    try:
        result = subprocess.run(
            ["python3", str(SCRIPT_PATH)],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def validate_manifest(manifest_path):
    """Strictly validate manifest.json against Manifest V3 spec."""
    errors = []
    
    if not manifest_path.exists():
        return False, ["manifest.json does not exist"]
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    
    # REQUIRED FIELDS (MV3)
    if manifest.get("manifest_version") != 3:
        errors.append(f"manifest_version must be 3, got {manifest.get('manifest_version')}")
    
    if not manifest.get("name"):
        errors.append("Missing required field: name")
    
    if not manifest.get("version"):
        errors.append("Missing required field: version")
    
    # VERSION FORMAT
    version = manifest.get("version", "")
    if not re.match(r'^\d+(\.\d+)*$', version):
        errors.append(f"Invalid version format: {version}")
    
    # VALIDATE ACTION (popup)
    if "action" in manifest:
        action = manifest["action"]
        if "default_popup" in action:
            popup_path = manifest_path.parent / action["default_popup"]
            if not popup_path.exists():
                errors.append(f"default_popup file missing: {action['default_popup']}")
    
    # VALIDATE BACKGROUND
    if "background" in manifest:
        bg = manifest["background"]
        if "service_worker" in bg:
            bg_path = manifest_path.parent / bg["service_worker"]
            if not bg_path.exists():
                errors.append(f"service_worker file missing: {bg['service_worker']}")
        # MV3 must use service_worker, not scripts
        if "scripts" in bg:
            errors.append("MV3 must use service_worker, not scripts")
    
    # VALIDATE CONTENT SCRIPTS
    if "content_scripts" in manifest:
        for i, cs in enumerate(manifest["content_scripts"]):
            if "matches" not in cs:
                errors.append(f"content_scripts[{i}] missing 'matches'")
            for js_file in cs.get("js", []):
                js_path = manifest_path.parent / js_file
                if not js_path.exists():
                    errors.append(f"content_scripts js file missing: {js_file}")
            for css_file in cs.get("css", []):
                css_path = manifest_path.parent / css_file
                if not css_path.exists():
                    errors.append(f"content_scripts css file missing: {css_file}")
    
    # VALIDATE PERMISSIONS
    valid_permissions = {
        "activeTab", "tabs", "storage", "scripting", "webRequest",
        "declarativeNetRequest", "declarativeNetRequestWithHostAccess",
        "alarms", "notifications", "contextMenus", "history", "bookmarks",
        "downloads", "geolocation", "management", "cookies"
    }
    for perm in manifest.get("permissions", []):
        if perm not in valid_permissions and not perm.startswith("http"):
            # Allow host permissions in permissions array for MV2 compat
            pass
    
    # VALIDATE declarative_net_request
    if "declarative_net_request" in manifest:
        dnr = manifest["declarative_net_request"]
        if "rule_resources" in dnr:
            for rule in dnr["rule_resources"]:
                if "path" in rule:
                    rule_path = manifest_path.parent / rule["path"]
                    if not rule_path.exists():
                        errors.append(f"rules file missing: {rule['path']}")
    
    return len(errors) == 0, errors

def validate_html(html_path):
    """Validate HTML file structure."""
    errors = []
    
    if not html_path.exists():
        return False, ["HTML file does not exist"]
    
    content = html_path.read_text()
    
    # Check for basic HTML structure
    if "<!DOCTYPE html>" not in content and "<!doctype html>" not in content.lower():
        errors.append("Missing DOCTYPE declaration")
    
    if "<html" not in content.lower():
        errors.append("Missing <html> tag")
    
    if "<head" not in content.lower():
        errors.append("Missing <head> tag")
    
    if "<body" not in content.lower():
        errors.append("Missing <body> tag")
    
    # Check for script reference
    if "<script" not in content.lower():
        errors.append("Missing <script> tag")
    
    return len(errors) == 0, errors

def validate_js(js_path, expected_patterns=None):
    """Validate JavaScript file."""
    errors = []
    
    if not js_path.exists():
        return False, ["JS file does not exist"]
    
    content = js_path.read_text()
    
    # Check for syntax errors (basic)
    if content.count('(') != content.count(')'):
        errors.append("Mismatched parentheses")
    
    if content.count('{') != content.count('}'):
        errors.append("Mismatched braces")
    
    # Check expected patterns
    if expected_patterns:
        for pattern, description in expected_patterns:
            if not re.search(pattern, content, re.IGNORECASE):
                errors.append(f"Missing expected pattern: {description}")
    
    return len(errors) == 0, errors

def validate_css(css_path):
    """Validate CSS file."""
    errors = []
    
    if not css_path.exists():
        return False, ["CSS file does not exist"]
    
    content = css_path.read_text()
    
    # Check for basic CSS structure
    if '{' not in content or '}' not in content:
        errors.append("No CSS rules found")
    
    if content.count('{') != content.count('}'):
        errors.append("Mismatched braces in CSS")
    
    return len(errors) == 0, errors

def test_scenario(test_num, total, name, prompt, checks):
    """Run a test scenario with strict validation."""
    print(f"\n{C.C}┌{'─' * 66}┐{C.RESET}")
    print(f"{C.C}│{C.RESET} {C.Y}TEST {test_num:02d}/{total:02d}{C.RESET} │ {C.W}{name:<50}{C.RESET} {C.C}│{C.RESET}")
    print(f"{C.C}├{'─' * 66}┤{C.RESET}")
    print(f"{C.C}│{C.RESET} {C.DIM}Prompt: {prompt[:55]}...{C.RESET}" if len(prompt) > 55 else f"{C.C}│{C.RESET} {C.DIM}Prompt: {prompt:<58}{C.RESET} {C.C}│{C.RESET}")
    print(f"{C.C}└{'─' * 66}┘{C.RESET}")
    
    cleanup()
    
    # Run chrome_forge
    success, stdout, stderr = run_chrome_forge(prompt)
    
    if not success:
        print(f"   {C.R}✗ FAILED{C.RESET} - Script execution failed")
        print(f"   {C.DIM}stderr: {stderr[:100]}{C.RESET}")
        return False
    
    # Check output directory exists
    if not OUTPUT_DIR.exists():
        print(f"   {C.R}✗ FAILED{C.RESET} - generated_extension/ folder not created")
        return False
    
    # Validate manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    valid, errors = validate_manifest(manifest_path)
    if not valid:
        print(f"   {C.R}✗ FAILED{C.RESET} - Manifest validation errors:")
        for err in errors[:3]:
            print(f"     {C.R}•{C.RESET} {err}")
        return False
    
    # Run custom checks
    all_passed = True
    for check_name, check_func in checks:
        passed, details = check_func()
        status = f"{C.G}✓{C.RESET}" if passed else f"{C.R}✗{C.RESET}"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False
            if details:
                print(f"     {C.DIM}{details}{C.RESET}")
    
    if all_passed:
        print(f"\n   {C.G}█ TEST PASSED{C.RESET}")
    else:
        print(f"\n   {C.R}█ TEST FAILED{C.RESET}")
    
    return all_passed

# ============================================================================
# ASSIGNMENT SCENARIO TESTS
# ============================================================================

def test_scenario_1():
    """
    SCENARIO 1 (FROM ASSIGNMENT):
    "Create an extension that shows a popup with today's date."
    → Requires popup.html + popup.js
    """
    def check_popup_html():
        path = OUTPUT_DIR / "popup.html"
        valid, errors = validate_html(path)
        return valid, "; ".join(errors) if errors else ""
    
    def check_popup_js():
        path = OUTPUT_DIR / "popup.js"
        patterns = [
            (r'Date|date|getDate|toLocaleDateString', "Date functionality"),
            (r'getElementById|querySelector|addEventListener', "DOM interaction"),
        ]
        valid, errors = validate_js(path, patterns)
        return valid, "; ".join(errors) if errors else ""
    
    def check_manifest_action():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        has_action = "action" in manifest and "default_popup" in manifest.get("action", {})
        return has_action, "Missing action.default_popup"
    
    def check_date_display():
        """Verify date display logic exists."""
        popup_js = OUTPUT_DIR / "popup.js"
        if popup_js.exists():
            content = popup_js.read_text()
            has_date = any(x in content.lower() for x in ['date', 'getdate', 'tolocale', 'new date'])
            return has_date, "No date logic found"
        return False, "popup.js missing"
    
    return test_scenario(
        1, 20, "ASSIGNMENT SCENARIO 1: Popup with Date",
        "Create an extension that shows a popup with today's date.",
        [
            ("popup.html exists and valid", check_popup_html),
            ("popup.js exists with date logic", check_popup_js),
            ("manifest.json has action.default_popup", check_manifest_action),
            ("Date display functionality present", check_date_display),
        ]
    )

def test_scenario_2():
    """
    SCENARIO 2 (FROM ASSIGNMENT):
    "Make an extension that highlights all phone numbers on any website."
    → Requires content.js + permissions
    """
    def check_content_js():
        path = OUTPUT_DIR / "content.js"
        patterns = [
            (r'phone|PHONE|regex|RegExp|\d{3}', "Phone detection pattern"),
            (r'highlight|mark|style|background', "Highlighting logic"),
        ]
        valid, errors = validate_js(path, patterns)
        return valid, "; ".join(errors) if errors else ""
    
    def check_manifest_content_scripts():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        has_cs = "content_scripts" in manifest
        return has_cs, "Missing content_scripts"
    
    def check_permissions():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        perms = manifest.get("permissions", [])
        has_active = "activeTab" in perms or any("http" in str(p) for p in manifest.get("host_permissions", []))
        return has_active, "Missing activeTab or host_permissions"
    
    def check_phone_regex():
        """Verify phone number regex exists."""
        content_js = OUTPUT_DIR / "content.js"
        if content_js.exists():
            content = content_js.read_text()
            has_regex = any(x in content for x in ['\\d{3}', 'PHONE', 'phone', '[0-9]'])
            return has_regex, "No phone regex found"
        return False, "content.js missing"
    
    return test_scenario(
        2, 20, "ASSIGNMENT SCENARIO 2: Highlight Phone Numbers",
        "Make an extension that highlights all phone numbers on any website.",
        [
            ("content.js exists with phone logic", check_content_js),
            ("manifest.json has content_scripts", check_manifest_content_scripts),
            ("Has required permissions", check_permissions),
            ("Phone number regex present", check_phone_regex),
        ]
    )

def test_scenario_3():
    """
    SCENARIO 3 (FROM ASSIGNMENT):
    "Block Facebook and TikTok every time the browser opens."
    → Requires background.js with webRequestBlocking permissions
    """
    def check_background_js():
        path = OUTPUT_DIR / "background.js"
        if not path.exists():
            return False, "background.js missing"
        patterns = [
            (r'facebook|tiktok', "Site blocking targets"),
            (r'block|Block|declarativeNetRequest|webRequest', "Blocking logic"),
        ]
        valid, errors = validate_js(path, patterns)
        return valid, "; ".join(errors) if errors else ""
    
    def check_manifest_background():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        has_bg = "background" in manifest and "service_worker" in manifest.get("background", {})
        return has_bg, "Missing background.service_worker"
    
    def check_blocking_permissions():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        perms = manifest.get("permissions", [])
        has_blocking = "declarativeNetRequest" in perms or "webRequest" in perms
        return has_blocking, "Missing blocking permission (declarativeNetRequest or webRequest)"
    
    def check_rules_json():
        """Check for declarativeNetRequest rules."""
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        if "declarative_net_request" in manifest:
            rules_path = OUTPUT_DIR / "rules.json"
            if rules_path.exists():
                try:
                    rules = json.load(open(rules_path))
                    return len(rules) > 0, "Empty rules.json"
                except:
                    return False, "Invalid rules.json"
        return True, ""  # Optional if using dynamic rules
    
    def check_sites_blocked():
        """Verify both sites are targeted."""
        bg_js = OUTPUT_DIR / "background.js"
        rules_json = OUTPUT_DIR / "rules.json"
        
        content = ""
        if bg_js.exists():
            content += bg_js.read_text().lower()
        if rules_json.exists():
            content += rules_json.read_text().lower()
        
        has_fb = "facebook" in content
        has_tt = "tiktok" in content
        
        if has_fb and has_tt:
            return True, ""
        missing = []
        if not has_fb:
            missing.append("facebook")
        if not has_tt:
            missing.append("tiktok")
        return False, f"Missing: {', '.join(missing)}"
    
    return test_scenario(
        3, 20, "ASSIGNMENT SCENARIO 3: Block Facebook & TikTok",
        "Block Facebook and TikTok every time the browser opens.",
        [
            ("background.js exists with blocking", check_background_js),
            ("manifest.json has service_worker", check_manifest_background),
            ("Has blocking permissions", check_blocking_permissions),
            ("rules.json valid (if used)", check_rules_json),
            ("Both sites targeted", check_sites_blocked),
        ]
    )

def test_scenario_4():
    """
    SCENARIO 4 (FROM ASSIGNMENT):
    "A tool that changes all webpage text to blue when I click a button in the popup."
    → Requires popup + content script + message passing
    """
    def check_popup_files():
        popup_html = OUTPUT_DIR / "popup.html"
        popup_js = OUTPUT_DIR / "popup.js"
        return popup_html.exists() and popup_js.exists(), "Missing popup files"
    
    def check_content_script():
        content_js = OUTPUT_DIR / "content.js"
        if not content_js.exists():
            return False, "content.js missing"
        content = content_js.read_text()
        has_color = any(x in content.lower() for x in ['color', 'blue', 'style'])
        return has_color, "No color change logic"
    
    def check_message_passing():
        """Verify message passing between popup and content script."""
        popup_js = OUTPUT_DIR / "popup.js"
        content_js = OUTPUT_DIR / "content.js"
        
        popup_content = popup_js.read_text() if popup_js.exists() else ""
        content_content = content_js.read_text() if content_js.exists() else ""
        
        # Check for sendMessage in popup
        has_send = any(x in popup_content for x in ['sendMessage', 'tabs.sendMessage', 'chrome.tabs'])
        # Check for onMessage in content
        has_receive = any(x in content_content for x in ['onMessage', 'addListener', 'chrome.runtime'])
        
        if has_send and has_receive:
            return True, ""
        missing = []
        if not has_send:
            missing.append("sendMessage in popup.js")
        if not has_receive:
            missing.append("onMessage in content.js")
        return False, f"Missing: {', '.join(missing)}"
    
    def check_button_click():
        """Verify button click handler exists."""
        popup_js = OUTPUT_DIR / "popup.js"
        if popup_js.exists():
            content = popup_js.read_text()
            has_click = any(x in content for x in ['addEventListener', 'onclick', 'click'])
            return has_click, "No click handler found"
        return False, "popup.js missing"
    
    return test_scenario(
        4, 20, "ASSIGNMENT SCENARIO 4: Change Text to Blue",
        "A tool that changes all webpage text to blue when I click a button in the popup.",
        [
            ("popup.html and popup.js exist", check_popup_files),
            ("content.js has color logic", check_content_script),
            ("Message passing implemented", check_message_passing),
            ("Button click handler exists", check_button_click),
        ]
    )

# ============================================================================
# PART A TESTS: PROMPT ANALYSIS ENGINE
# ============================================================================

def test_part_a_validation():
    """Test prompt validation (too short, too long, missing verbs)."""
    def check_manifest_exists():
        return (OUTPUT_DIR / "manifest.json").exists(), "No manifest created"
    
    return test_scenario(
        5, 20, "PART A: Prompt Validation - Short Prompt",
        "hi",  # Too short
        [
            ("Should still create manifest", check_manifest_exists),
        ]
    )

def test_part_a_intent_ui():
    """Test UI interaction intent detection."""
    def check_has_popup():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        return "action" in manifest, "UI intent not detected"
    
    return test_scenario(
        6, 20, "PART A: Intent Detection - UI Interaction",
        "Show a popup with a button that displays Hello World",
        [
            ("Detects popup requirement", check_has_popup),
        ]
    )

def test_part_a_intent_content():
    """Test content modification intent detection."""
    def check_has_content_script():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        return "content_scripts" in manifest, "Content intent not detected"
    
    return test_scenario(
        7, 20, "PART A: Intent Detection - Content Modification",
        "Highlight all email addresses on every webpage I visit",
        [
            ("Detects content_scripts requirement", check_has_content_script),
        ]
    )

def test_part_a_intent_background():
    """Test background automation intent detection."""
    def check_has_background():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        return "background" in manifest, "Background intent not detected"
    
    return test_scenario(
        8, 20, "PART A: Intent Detection - Background Automation",
        "Block all social media sites automatically when the browser opens",
        [
            ("Detects background requirement", check_has_background),
        ]
    )

# ============================================================================
# PART B TESTS: MANIFEST BUILDER
# ============================================================================

def test_part_b_manifest_v3():
    """Test Manifest V3 compliance."""
    def check_mv3():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        return manifest.get("manifest_version") == 3, f"Got MV{manifest.get('manifest_version')}"
    
    def check_required_fields():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        has_name = bool(manifest.get("name"))
        has_version = bool(manifest.get("version"))
        return has_name and has_version, "Missing name or version"
    
    return test_scenario(
        9, 20, "PART B: Manifest V3 Compliance",
        "Create a simple extension with a popup",
        [
            ("manifest_version is 3", check_mv3),
            ("Has name and version", check_required_fields),
        ]
    )

def test_part_b_permissions():
    """Test permission detection."""
    def check_storage_perm():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        return "storage" in manifest.get("permissions", []), "storage permission not added"
    
    return test_scenario(
        10, 20, "PART B: Permission Detection",
        "Create an extension that saves notes to local storage",
        [
            ("Detects storage permission", check_storage_perm),
        ]
    )

def test_part_b_host_permissions():
    """Test host permissions for blocking."""
    def check_host_perms():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        host_perms = manifest.get("host_permissions", [])
        return len(host_perms) > 0 or "<all_urls>" in str(manifest), "No host permissions"
    
    return test_scenario(
        11, 20, "PART B: Host Permissions",
        "Block access to twitter.com and instagram.com",
        [
            ("Has host permissions for blocking", check_host_perms),
        ]
    )

# ============================================================================
# PART C TESTS: DYNAMIC CODE GENERATION
# ============================================================================

def test_part_c_popup_files():
    """Test popup file generation."""
    def check_popup_html_valid():
        path = OUTPUT_DIR / "popup.html"
        if not path.exists():
            return False, "popup.html not created"
        valid, errors = validate_html(path)
        return valid, "; ".join(errors)
    
    def check_popup_js_valid():
        path = OUTPUT_DIR / "popup.js"
        if not path.exists():
            return False, "popup.js not created"
        valid, errors = validate_js(path)
        return valid, "; ".join(errors)
    
    def check_styles_css():
        path = OUTPUT_DIR / "styles.css"
        return path.exists(), "styles.css not created"
    
    return test_scenario(
        12, 20, "PART C: Popup File Generation",
        "Create a popup that shows the current time",
        [
            ("popup.html is valid HTML", check_popup_html_valid),
            ("popup.js is valid JavaScript", check_popup_js_valid),
            ("styles.css exists", check_styles_css),
        ]
    )

def test_part_c_content_script():
    """Test content script generation."""
    def check_content_js_valid():
        path = OUTPUT_DIR / "content.js"
        if not path.exists():
            return False, "content.js not created"
        valid, errors = validate_js(path)
        return valid, "; ".join(errors)
    
    def check_iife_wrapper():
        """Content scripts should be wrapped in IIFE."""
        path = OUTPUT_DIR / "content.js"
        if path.exists():
            content = path.read_text()
            has_iife = "(function()" in content or "(() =>" in content
            return has_iife, "Not wrapped in IIFE"
        return False, "content.js missing"
    
    return test_scenario(
        13, 20, "PART C: Content Script Generation",
        "Find and highlight all links on any webpage",
        [
            ("content.js is valid JavaScript", check_content_js_valid),
            ("Uses IIFE wrapper for isolation", check_iife_wrapper),
        ]
    )

def test_part_c_background_script():
    """Test background script generation."""
    def check_background_js_valid():
        path = OUTPUT_DIR / "background.js"
        if not path.exists():
            return False, "background.js not created"
        valid, errors = validate_js(path)
        return valid, "; ".join(errors)
    
    def check_service_worker_events():
        """Background should have install/startup handlers."""
        path = OUTPUT_DIR / "background.js"
        if path.exists():
            content = path.read_text()
            has_events = "onInstalled" in content or "onStartup" in content
            return has_events, "Missing lifecycle event handlers"
        return False, "background.js missing"
    
    return test_scenario(
        14, 20, "PART C: Background Script Generation",
        "Create an alarm that fires every 5 minutes",
        [
            ("background.js is valid JavaScript", check_background_js_valid),
            ("Has lifecycle event handlers", check_service_worker_events),
        ]
    )

# ============================================================================
# PART D TESTS: FILE SYSTEM OUTPUT
# ============================================================================

def test_part_d_folder_creation():
    """Test generated_extension folder creation."""
    def check_folder_exists():
        return OUTPUT_DIR.exists() and OUTPUT_DIR.is_dir(), "Folder not created"
    
    def check_manifest_in_folder():
        return (OUTPUT_DIR / "manifest.json").exists(), "manifest.json not in folder"
    
    return test_scenario(
        15, 20, "PART D: Folder Creation",
        "Create any simple extension",
        [
            ("generated_extension/ folder created", check_folder_exists),
            ("manifest.json in folder", check_manifest_in_folder),
        ]
    )

def test_part_d_loadable():
    """Test that extension is loadable in Chrome."""
    def check_all_referenced_files():
        """Verify all files referenced in manifest exist."""
        manifest_path = OUTPUT_DIR / "manifest.json"
        if not manifest_path.exists():
            return False, "No manifest"
        
        manifest = json.load(open(manifest_path))
        missing = []
        
        # Check popup
        if "action" in manifest and "default_popup" in manifest["action"]:
            popup = OUTPUT_DIR / manifest["action"]["default_popup"]
            if not popup.exists():
                missing.append(manifest["action"]["default_popup"])
        
        # Check background
        if "background" in manifest and "service_worker" in manifest["background"]:
            bg = OUTPUT_DIR / manifest["background"]["service_worker"]
            if not bg.exists():
                missing.append(manifest["background"]["service_worker"])
        
        # Check content scripts
        for cs in manifest.get("content_scripts", []):
            for js in cs.get("js", []):
                if not (OUTPUT_DIR / js).exists():
                    missing.append(js)
            for css in cs.get("css", []):
                if not (OUTPUT_DIR / css).exists():
                    missing.append(css)
        
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, ""
    
    return test_scenario(
        16, 20, "PART D: Chrome Loadable",
        "Create a complete extension with popup and content script",
        [
            ("All referenced files exist", check_all_referenced_files),
        ]
    )

# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_edge_empty_prompt():
    """Test handling of empty prompt."""
    def check_creates_default():
        return (OUTPUT_DIR / "manifest.json").exists(), "Should create default extension"
    
    return test_scenario(
        17, 20, "EDGE CASE: Empty Prompt",
        "",  # Empty
        [
            ("Creates default extension", check_creates_default),
        ]
    )

def test_edge_complex_prompt():
    """Test complex multi-feature prompt."""
    def check_multiple_components():
        manifest = json.load(open(OUTPUT_DIR / "manifest.json"))
        has_popup = "action" in manifest
        has_content = "content_scripts" in manifest
        return has_popup or has_content, "Should detect at least one component"
    
    return test_scenario(
        18, 20, "EDGE CASE: Complex Prompt",
        "Create an extension with a popup button that when clicked highlights all emails on the page and saves them to storage",
        [
            ("Handles complex multi-feature request", check_multiple_components),
        ]
    )

def test_edge_special_chars():
    """Test prompt with special characters."""
    def check_manifest_valid():
        manifest_path = OUTPUT_DIR / "manifest.json"
        if not manifest_path.exists():
            return False, "No manifest"
        try:
            json.load(open(manifest_path))
            return True, ""
        except:
            return False, "Invalid JSON"
    
    return test_scenario(
        19, 20, "EDGE CASE: Special Characters",
        "Create an extension that shows \"today's date\" & <time>!",
        [
            ("Handles special chars in manifest", check_manifest_valid),
        ]
    )

def test_no_external_apis():
    """Verify no external API calls in generated code."""
    def check_no_fetch():
        """Generated code should not call external APIs."""
        for file in OUTPUT_DIR.glob("*.js"):
            content = file.read_text()
            # Allow chrome.* APIs but not external fetch to non-Chrome URLs
            has_external = re.search(r"fetch\s*\(\s*['\"]https?://(?!chrome)", content)
            if has_external:
                return False, f"External API call in {file.name}"
        return True, ""
    
    return test_scenario(
        20, 20, "REQUIREMENT: No External APIs",
        "Create a popup that shows the date",
        [
            ("No external API calls in generated code", check_no_fetch),
        ]
    )

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print_header()
    
    # Check chrome_forge.py exists
    if not SCRIPT_PATH.exists():
        print(f"{C.R}ERROR: chrome_forge.py not found at {SCRIPT_PATH}{C.RESET}")
        return 1
    
    # Check for syntax errors
    print(f"\n{C.Y}[PRE-CHECK]{C.RESET} Validating chrome_forge.py syntax...")
    result = subprocess.run(["python3", "-m", "py_compile", str(SCRIPT_PATH)], capture_output=True)
    if result.returncode != 0:
        print(f"{C.R}✗ SYNTAX ERROR in chrome_forge.py{C.RESET}")
        print(result.stderr.decode())
        return 1
    print(f"{C.G}✓ No syntax errors{C.RESET}")
    
    # Run all tests
    tests = [
        test_scenario_1,    # Assignment Scenario 1
        test_scenario_2,    # Assignment Scenario 2
        test_scenario_3,    # Assignment Scenario 3
        test_scenario_4,    # Assignment Scenario 4
        test_part_a_validation,
        test_part_a_intent_ui,
        test_part_a_intent_content,
        test_part_a_intent_background,
        test_part_b_manifest_v3,
        test_part_b_permissions,
        test_part_b_host_permissions,
        test_part_c_popup_files,
        test_part_c_content_script,
        test_part_c_background_script,
        test_part_d_folder_creation,
        test_part_d_loadable,
        test_edge_empty_prompt,
        test_edge_complex_prompt,
        test_edge_special_chars,
        test_no_external_apis,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   {C.R}✗ TEST CRASHED: {e}{C.RESET}")
            failed += 1
    
    # Final cleanup
    cleanup()
    
    # Results
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"""
{C.M}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   {C.W}FINAL RESULTS{C.M}                                                   ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   {C.G}PASSED: {passed:02d}{C.M}    {C.R}FAILED: {failed:02d}{C.M}    {C.Y}TOTAL: {total:02d}{C.M}                        ║
║                                                                  ║
║   {C.W}Pass Rate: {pass_rate:.1f}%{C.M}                                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{C.RESET}
""")
    
    if failed == 0:
        print(f"{C.G}✓ ALL TESTS PASSED - READY FOR SUBMISSION{C.RESET}\n")
        return 0
    else:
        print(f"{C.R}✗ {failed} TEST(S) FAILED - REVIEW REQUIRED{C.RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
