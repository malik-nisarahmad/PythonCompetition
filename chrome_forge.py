#!/usr/bin/env python3
"""
chrome_forge.py - ChromeForge: AI-Powered Chrome Extension Generator

FAST University Tech Society Project
Version: 1.0.0

A pure Python program that generates complete, loadable Chrome extensions
from natural language descriptions using Manifest V3.

Architecture: Modular Pipeline
- Part A: Prompt Analysis Engine
- Part B: Manifest Builder  
- Part C: Dynamic Code Generation
- Part D: File System Output

Run: python3 chrome_forge.py
     python3 chrome_forge.py "Your extension description here"
"""

import os
import json
import re
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple

# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

VERSION = "1.0.0"
MIN_PROMPT_LENGTH = 10
MAX_PROMPT_LENGTH = 1000
OUTPUT_DIR_NAME = "generated_extension"
BACKUP_DIR_NAME = "generated_extension_backup"

# Intent classification with confidence thresholds
INTENT_CATEGORIES = {
    "ui_interaction": {
        "keywords": ["popup", "button", "menu", "interface", "display", "show", "view", "click", "toolbar"],
        "confidence_threshold": 0.7,
        "weight": 1.0
    },
    "content_modification": {
        "keywords": ["modify", "change", "highlight", "extract", "replace", "inject", "webpage", 
                    "website", "page", "dom", "text", "element", "find", "search"],
        "confidence_threshold": 0.6,
        "weight": 1.2
    },
    "background_automation": {
        "keywords": ["background", "automate", "block", "filter", "monitor", "schedule", 
                    "alarm", "timer", "startup", "browser opens", "always running"],
        "confidence_threshold": 0.7,
        "weight": 1.1
    },
    "data_storage": {
        "keywords": ["save", "store", "remember", "persist", "settings", "preferences", "storage"],
        "confidence_threshold": 0.6,
        "weight": 0.8
    },
    "browser_integration": {
        "keywords": ["tabs", "browser", "navigation", "url", "address", "omnibox", "bookmarks"],
        "confidence_threshold": 0.7,
        "weight": 0.9
    }
}

# Entity recognition patterns
ENTITY_PATTERNS = {
    "target_websites": r"(?:on|for|in|from)\s+(?:(?:https?://)?(?:www\.)?)?([a-z0-9\-]+\.(?:com|org|net|io|edu|gov))",
    "social_media": r"\b(facebook|twitter|tiktok|instagram|youtube|reddit|linkedin|snapchat)\b",
    "visual_elements": r"\b(color|style|theme|font|size|highlight|background|border|red|blue|green|yellow|dark|light)\b",
    "interaction_triggers": r"\b(when|after|before|on\s+(?:click|hover|load|open|start))\b",
    "data_elements": r"\b(date|time|phone\s*(?:number)?|email|image|link|url|text|number)\b",
    "time_patterns": r"\b(\d{1,2})\s*(?:am|pm|AM|PM|:00)\b",
    "scheduling": r"\b(every\s+(?:\d+\s+)?(?:second|minute|hour|day)|daily|hourly|periodically)\b"
}

# Permission mapping with triggers
PERMISSION_MAP = {
    "activeTab": {
        "triggers": ["current page", "this page", "active tab", "current tab", "this website", "current website"],
        "description": "Access to the currently active tab"
    },
    "tabs": {
        "triggers": ["all tabs", "browser tabs", "multiple tabs", "switch tab", "tab information", "open tab"],
        "description": "Access to browser tabs"
    },
    "storage": {
        "triggers": ["save", "store", "remember", "persist", "settings", "preferences", "local storage"],
        "description": "Store data locally"
    },
    "scripting": {
        "triggers": ["inject", "execute script", "run script", "modify page"],
        "description": "Execute scripts in web pages"
    },
    "webRequest": {
        "triggers": ["web request", "network", "http request"],
        "description": "Observe and analyze traffic"
    },
    "declarativeNetRequest": {
        "triggers": ["block", "blocking", "filter url", "block website", "block site"],
        "description": "Block or modify network requests"
    },
    "alarms": {
        "triggers": ["alarm", "timer", "schedule", "periodic", "interval", "every minute", "every hour"],
        "description": "Schedule periodic tasks"
    },
    "notifications": {
        "triggers": ["notification", "notify", "alert", "remind"],
        "description": "Show desktop notifications"
    },
    "contextMenus": {
        "triggers": ["right click", "context menu", "right-click menu"],
        "description": "Add items to context menu"
    },
    "history": {
        "triggers": ["history", "browsing history", "visited"],
        "description": "Access browsing history"
    },
    "bookmarks": {
        "triggers": ["bookmark", "bookmarks", "favorite"],
        "description": "Access bookmarks"
    }
}


# ============================================================================
# PART A: PROMPT ANALYSIS ENGINE
# ============================================================================

class PromptAnalyzer:
    """Natural Language Processing engine for understanding user intent."""
    
    def __init__(self, prompt: str):
        self.raw_prompt = prompt
        self.normalized_prompt = self._normalize(prompt)
        self.tokens = self._tokenize(self.normalized_prompt)
        self.analysis_result = {}
    
    def _normalize(self, text: str) -> str:
        """Normalize text for processing."""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'[^\w\s\-\.\@]', ' ', text)  # Keep alphanumeric, spaces, hyphens, dots, @
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """Split text into tokens."""
        return text.split()
    
    def validate_prompt(self) -> Tuple[bool, str]:
        """Validate prompt meets requirements."""
        if len(self.raw_prompt) < MIN_PROMPT_LENGTH:
            return False, f"Prompt too short. Minimum {MIN_PROMPT_LENGTH} characters required."
        if len(self.raw_prompt) > MAX_PROMPT_LENGTH:
            return False, f"Prompt too long. Maximum {MAX_PROMPT_LENGTH} characters allowed."
        
        # Check for action verb
        action_verbs = ["create", "make", "build", "show", "display", "block", "highlight", 
                       "change", "modify", "extract", "save", "store", "find", "search", "add"]
        has_action = any(verb in self.normalized_prompt for verb in action_verbs)
        if not has_action:
            return False, "Please include an action verb (create, make, show, block, highlight, etc.)"
        
        return True, "Valid prompt"
    
    def classify_intents(self) -> Dict[str, float]:
        """Classify user intent with confidence scores."""
        scores = {}
        
        for intent, config in INTENT_CATEGORIES.items():
            matches = sum(1 for kw in config["keywords"] if kw in self.normalized_prompt)
            if matches > 0:
                # Calculate confidence based on keyword matches and weight
                base_confidence = min(matches / len(config["keywords"]) * 2, 1.0)
                weighted_confidence = base_confidence * config["weight"]
                scores[intent] = min(weighted_confidence, 1.0)
        
        return scores
    
    def extract_entities(self) -> Dict[str, List[str]]:
        """Extract named entities from prompt."""
        entities = {}
        
        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, self.normalized_prompt, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
        
        return entities
    
    def detect_permissions(self) -> Set[str]:
        """Detect required permissions based on triggers."""
        permissions = set()
        
        for perm, config in PERMISSION_MAP.items():
            for trigger in config["triggers"]:
                if trigger in self.normalized_prompt:
                    permissions.add(perm)
                    break
        
        return permissions
    
    def detect_color_scheme(self) -> Optional[str]:
        """Detect color preferences from prompt."""
        color_map = {
            "red": "#ff4444",
            "blue": "#4285f4",
            "green": "#34a853",
            "yellow": "#fbbc05",
            "orange": "#ff9800",
            "purple": "#9c27b0",
            "dark": "#2d2d2d",
            "light": "#ffffff",
            "black": "#000000",
            "white": "#ffffff"
        }
        
        for color, hex_val in color_map.items():
            if color in self.normalized_prompt:
                return hex_val
        
        return None
    
    def analyze(self) -> Dict[str, Any]:
        """Perform complete analysis of the prompt."""
        # Validate first
        is_valid, message = self.validate_prompt()
        
        # Intent classification
        intents = self.classify_intents()
        
        # Entity extraction  
        entities = self.extract_entities()
        
        # Permission detection
        permissions = self.detect_permissions()
        
        # Color detection
        color = self.detect_color_scheme()
        
        # Determine required components
        needs_popup = intents.get("ui_interaction", 0) > 0.3 or \
                     any(w in self.normalized_prompt for w in ["popup", "button", "menu", "click"])
        
        needs_content_script = intents.get("content_modification", 0) > 0.3 or \
                              any(w in self.normalized_prompt for w in ["highlight", "modify", "change", "webpage", 
                                                                        "page", "website", "extract", "find", "dom"])
        
        needs_background = intents.get("background_automation", 0) > 0.3 or \
                          any(w in self.normalized_prompt for w in ["block", "background", "alarm", "timer", 
                                                                    "startup", "browser opens", "schedule"])
        
        needs_storage = "storage" in permissions or intents.get("data_storage", 0) > 0.4
        
        needs_css = color is not None or \
                   any(w in self.normalized_prompt for w in ["style", "css", "theme", "color", "highlight"])
        
        # Specific feature detection
        features = {
            "show_date": any(w in self.normalized_prompt for w in ["date", "today", "current date", "time", "clock"]),
            "highlight_phone": "phone" in self.normalized_prompt and \
                              any(w in self.normalized_prompt for w in ["highlight", "find", "extract", "show"]),
            "highlight_email": "email" in self.normalized_prompt and \
                              any(w in self.normalized_prompt for w in ["highlight", "find", "extract", "show"]),
            "block_sites": "block" in self.normalized_prompt and \
                          ("social_media" in entities or "social media" in self.normalized_prompt or 
                           any(site in self.normalized_prompt 
                           for site in ["facebook", "tiktok", "twitter", "instagram", "youtube"])),
            "change_color": any(w in self.normalized_prompt for w in ["text to blue", "change color", "text color"]),
            "time_based": bool(entities.get("time_patterns")) or \
                         any(w in self.normalized_prompt for w in ["work hours", "during", "between"]),
            "refresh_timer": any(w in self.normalized_prompt for w in ["refresh", "update", "every second", "real-time"]),
            "copy_feature": "copy" in self.normalized_prompt,
            "dark_mode": "dark" in self.normalized_prompt and any(w in self.normalized_prompt for w in ["mode", "theme"]),
        }
        
        # Build blocked sites list
        blocked_sites = []
        if features["block_sites"]:
            social_sites = {"facebook": "facebook.com", "tiktok": "tiktok.com", "twitter": "twitter.com",
                          "instagram": "instagram.com", "youtube": "youtube.com", "reddit": "reddit.com",
                          "linkedin": "linkedin.com", "snapchat": "snapchat.com"}
            for site, domain in social_sites.items():
                if site in self.normalized_prompt:
                    blocked_sites.append(domain)
            if not blocked_sites and "social media" in self.normalized_prompt:
                blocked_sites = ["facebook.com", "twitter.com", "tiktok.com", "instagram.com"]
        
        self.analysis_result = {
            "valid": is_valid,
            "validation_message": message,
            "raw_prompt": self.raw_prompt,
            "normalized_prompt": self.normalized_prompt,
            "intents": intents,
            "entities": entities,
            "permissions": permissions,
            "color_scheme": color,
            "components": {
                "popup": needs_popup,
                "content_script": needs_content_script,
                "background": needs_background,
                "storage": needs_storage,
                "css": needs_css or needs_popup  # Always include CSS with popup
            },
            "features": features,
            "blocked_sites": blocked_sites
        }
        
        return self.analysis_result


# ============================================================================
# PART B: MANIFEST BUILDER
# ============================================================================

class ManifestBuilder:
    """Generate Manifest V3 compliant JSON."""
    
    def __init__(self, analysis: Dict[str, Any]):
        self.analysis = analysis
        self.manifest = {}
    
    def build(self) -> Dict[str, Any]:
        """Build complete manifest.json structure."""
        # Required fields (MV3)
        name = self.analysis["raw_prompt"][:50].strip() or "ChromeForge Extension"
        # Clean name for manifest
        name = re.sub(r'[^\w\s\-]', '', name).strip()
        
        self.manifest = {
            "manifest_version": 3,
            "name": name,
            "version": "1.0.0",
            "description": f"Auto-generated extension: {self.analysis['raw_prompt'][:100]}"
        }
        
        # Action (popup)
        if self.analysis["components"]["popup"]:
            self.manifest["action"] = {
                "default_popup": "popup.html",
                "default_title": name[:30]
            }
        else:
            self.manifest["action"] = {}
        
        # Background service worker
        if self.analysis["components"]["background"]:
            self.manifest["background"] = {
                "service_worker": "background.js"
            }
        
        # Content scripts
        if self.analysis["components"]["content_script"]:
            content_script_config = {
                "matches": ["<all_urls>"],
                "js": ["content.js"],
                "run_at": "document_idle"
            }
            if self.analysis["components"]["css"]:
                content_script_config["css"] = ["styles.css"]
            self.manifest["content_scripts"] = [content_script_config]
        
        # Permissions
        permissions = set(self.analysis["permissions"])
        
        # Add implicit permissions based on components
        if self.analysis["components"]["content_script"]:
            permissions.add("activeTab")
        if self.analysis["components"]["storage"]:
            permissions.add("storage")
        if self.analysis["features"]["block_sites"]:
            permissions.add("declarativeNetRequest")
            permissions.add("declarativeNetRequestWithHostAccess")
        if self.analysis["features"]["time_based"] or self.analysis["features"]["refresh_timer"]:
            permissions.add("alarms")
        
        if permissions:
            self.manifest["permissions"] = sorted(list(permissions))
        
        # Host permissions for blocking
        if self.analysis["blocked_sites"]:
            host_perms = [f"*://*.{site}/*" for site in self.analysis["blocked_sites"]]
            host_perms.append("<all_urls>")
            self.manifest["host_permissions"] = list(set(host_perms))
        
        # DeclarativeNetRequest rules for blocking
        if self.analysis["features"]["block_sites"]:
            self.manifest["declarative_net_request"] = {
                "rule_resources": [{
                    "id": "ruleset_1",
                    "enabled": True,
                    "path": "rules.json"
                }]
            }
        
        return self.manifest
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate manifest structure."""
        errors = []
        
        # Check required fields
        required = ["manifest_version", "name", "version"]
        for field in required:
            if field not in self.manifest:
                errors.append(f"Missing required field: {field}")
        
        # Check manifest version
        if self.manifest.get("manifest_version") != 3:
            errors.append("manifest_version must be 3")
        
        # Validate JSON serialization
        try:
            json.dumps(self.manifest)
        except (TypeError, ValueError) as e:
            errors.append(f"Invalid JSON structure: {e}")
        
        return len(errors) == 0, errors


# ============================================================================
# PART C: DYNAMIC CODE GENERATION
# ============================================================================

class CodeGenerator:
    """Generate extension code files based on analysis."""
    
    def __init__(self, analysis: Dict[str, Any]):
        self.analysis = analysis
        self.files = {}
    
    def generate_popup_html(self) -> str:
        """Generate popup.html file."""
        features = self.analysis["features"]
        color = self.analysis["color_scheme"] or "#4285f4"
        
        title = "Extension Popup"
        button_text = "Run Action"
        
        if features["show_date"]:
            title = "Date & Time"
            button_text = "Refresh"
        elif features["change_color"]:
            title = "Page Modifier"
            button_text = "Change Color"
        elif features["highlight_phone"]:
            title = "Phone Finder"
            button_text = "Find Phones"
        elif features["highlight_email"]:
            title = "Email Finder"
            button_text = "Find Emails"
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <div class="popup-container">
    <h2 class="popup-title">{title}</h2>
    <div id="output" class="output-area"></div>
    <button id="actionBtn" class="btn-primary">{button_text}</button>
    <div id="status" class="status-message"></div>
  </div>
  <script src="popup.js"></script>
</body>
</html>'''
        return html
    
    def generate_popup_js(self) -> str:
        """Generate popup.js file."""
        features = self.analysis["features"]
        
        base_code = '''// ChromeForge Generated Popup Script
document.addEventListener('DOMContentLoaded', function() {
  const actionBtn = document.getElementById('actionBtn');
  const output = document.getElementById('output');
  const status = document.getElementById('status');
  
'''
        
        if features["show_date"]:
            # Date/time display with optional refresh
            action_code = '''  function updateDateTime() {
    const now = new Date();
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    output.innerHTML = '<div class="date-display">' + now.toLocaleDateString('en-US', options) + '</div>';
  }
  
  updateDateTime();
'''
            if features["refresh_timer"]:
                action_code += '''  setInterval(updateDateTime, 1000);
'''
            action_code += '''
  actionBtn.addEventListener('click', updateDateTime);
'''
        
        elif features["change_color"] or "blue" in self.analysis["normalized_prompt"]:
            action_code = '''  actionBtn.addEventListener('click', async () => {
    try {
      const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
      await chrome.tabs.sendMessage(tab.id, {action: 'changeColor', color: 'blue'});
      status.textContent = 'Color changed!';
      status.className = 'status-message success';
    } catch (error) {
      status.textContent = 'Error: ' + error.message;
      status.className = 'status-message error';
    }
  });
'''
        
        elif features["highlight_phone"] or features["highlight_email"]:
            data_type = "phones" if features["highlight_phone"] else "emails"
            action_code = f'''  actionBtn.addEventListener('click', async () => {{
    try {{
      const [tab] = await chrome.tabs.query({{active: true, currentWindow: true}});
      const response = await chrome.tabs.sendMessage(tab.id, {{action: 'highlight{data_type.title()}'}});
      if (response && response.count !== undefined) {{
        output.textContent = 'Found ' + response.count + ' {data_type}';
        status.textContent = 'Highlighting complete!';
        status.className = 'status-message success';
      }}
    }} catch (error) {{
      status.textContent = 'Error: ' + error.message;
      status.className = 'status-message error';
    }}
  }});
'''
        
        else:
            # Generic action
            action_code = '''  actionBtn.addEventListener('click', async () => {
    try {
      const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
      await chrome.tabs.sendMessage(tab.id, {action: 'execute'});
      status.textContent = 'Action executed!';
      status.className = 'status-message success';
    } catch (error) {
      status.textContent = 'Action completed';
      status.className = 'status-message success';
    }
  });
'''
        
        return base_code + action_code + '});\n'
    
    def generate_content_js(self) -> str:
        """Generate content.js file."""
        features = self.analysis["features"]
        color = self.analysis["color_scheme"] or "blue"
        
        base_code = '''// ChromeForge Generated Content Script
(function() {
  'use strict';
  
'''
        
        if features["highlight_phone"]:
            specific_code = '''  // Phone number highlighting
  const PHONE_REGEX = /(?:\\+?1[-.]?)?(?:\\(?\\d{3}\\)?[-.]?)?\\d{3}[-.]?\\d{4}\\b/g;
  
  function highlightPhones() {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    const textNodes = [];
    let node;
    while (node = walker.nextNode()) {
      if (node.nodeValue.match(PHONE_REGEX)) {
        textNodes.push(node);
      }
    }
    
    let count = 0;
    textNodes.forEach(textNode => {
      const span = document.createElement('span');
      span.innerHTML = textNode.nodeValue.replace(PHONE_REGEX, match => {
        count++;
        return '<mark class="cf-highlight cf-phone">' + match + '</mark>';
      });
      textNode.parentNode.replaceChild(span, textNode);
    });
    
    return count;
  }
  
  // Auto-run on page load
  const phoneCount = highlightPhones();
  console.log('ChromeForge: Found', phoneCount, 'phone numbers');
'''
        
        elif features["highlight_email"]:
            specific_code = '''  // Email address highlighting
  const EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g;
  
  function highlightEmails() {
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    const textNodes = [];
    let node;
    while (node = walker.nextNode()) {
      if (node.nodeValue.match(EMAIL_REGEX)) {
        textNodes.push(node);
      }
    }
    
    let count = 0;
    textNodes.forEach(textNode => {
      const span = document.createElement('span');
      span.innerHTML = textNode.nodeValue.replace(EMAIL_REGEX, match => {
        count++;
        return '<mark class="cf-highlight cf-email">' + match + '</mark>';
      });
      textNode.parentNode.replaceChild(span, textNode);
    });
    
    return count;
  }
  
  // Auto-run on page load
  const emailCount = highlightEmails();
  console.log('ChromeForge: Found', emailCount, 'email addresses');
'''
        
        elif features["change_color"] or features["dark_mode"]:
            target_color = color if isinstance(color, str) and color.startswith('#') else 'blue'
            specific_code = f'''  // Page color modification
  function changePageColor(color) {{
    document.documentElement.style.setProperty('color', color, 'important');
    document.body.style.setProperty('color', color, 'important');
    
    // Also apply to common text elements
    const elements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, a, li, td, th');
    elements.forEach(el => {{
      el.style.setProperty('color', color, 'important');
    }});
    
    console.log('ChromeForge: Changed page color to', color);
  }}
'''
        
        else:
            specific_code = '''  // Generic content script
  console.log('ChromeForge: Content script loaded');
  
  function executeAction() {
    console.log('ChromeForge: Executing action');
    return { success: true };
  }
'''
        
        # Message listener for popup communication
        message_handler = '''
  // Message handler for popup communication
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('ChromeForge: Received message', request);
    
    if (request.action === 'changeColor') {
      changePageColor(request.color || 'blue');
      sendResponse({success: true});
    }
    else if (request.action === 'highlightPhones') {
      const count = typeof highlightPhones === 'function' ? highlightPhones() : 0;
      sendResponse({success: true, count: count});
    }
    else if (request.action === 'highlightEmails') {
      const count = typeof highlightEmails === 'function' ? highlightEmails() : 0;
      sendResponse({success: true, count: count});
    }
    else if (request.action === 'execute') {
      const result = typeof executeAction === 'function' ? executeAction() : {success: true};
      sendResponse(result);
    }
    
    return true; // Keep message channel open for async response
  });
'''
        
        # Add changePageColor function if not already present
        if 'changePageColor' not in specific_code:
            specific_code += '''
  function changePageColor(color) {
    document.documentElement.style.setProperty('color', color, 'important');
    document.body.style.setProperty('color', color, 'important');
  }
'''
        
        return base_code + specific_code + message_handler + '\n})();\n'
    
    def generate_background_js(self) -> str:
        """Generate background.js service worker."""
        features = self.analysis["features"]
        blocked_sites = self.analysis["blocked_sites"]
        
        base_code = '''// ChromeForge Generated Background Service Worker
console.log('ChromeForge: Background service worker starting');

// Installation handler
chrome.runtime.onInstalled.addListener((details) => {
  console.log('ChromeForge: Extension installed', details.reason);
});

// Startup handler
chrome.runtime.onStartup.addListener(() => {
  console.log('ChromeForge: Browser started with extension');
});

'''
        
        if features["block_sites"] and blocked_sites:
            sites_list = ', '.join([f'"{s}"' for s in blocked_sites])
            block_code = f'''// Site blocking configuration
const BLOCKED_SITES = [{sites_list}];

// Dynamic rule creation for blocking
async function setupBlockingRules() {{
  const rules = BLOCKED_SITES.map((site, index) => ({{
    id: index + 1,
    priority: 1,
    action: {{ type: 'block' }},
    condition: {{
      urlFilter: '*://*.' + site + '/*',
      resourceTypes: ['main_frame', 'sub_frame']
    }}
  }}));
  
  try {{
    // Remove old rules first
    const oldRules = await chrome.declarativeNetRequest.getDynamicRules();
    const oldRuleIds = oldRules.map(rule => rule.id);
    
    await chrome.declarativeNetRequest.updateDynamicRules({{
      removeRuleIds: oldRuleIds,
      addRules: rules
    }});
    
    console.log('ChromeForge: Blocking rules installed for', BLOCKED_SITES);
  }} catch (error) {{
    console.error('ChromeForge: Error setting up blocking rules', error);
  }}
}}

// Setup blocking on install
chrome.runtime.onInstalled.addListener(setupBlockingRules);
chrome.runtime.onStartup.addListener(setupBlockingRules);

'''
            base_code += block_code
            
            # Time-based blocking
            if features["time_based"]:
                time_code = '''
// Time-based blocking (work hours: 9 AM - 5 PM)
function isWorkHours() {
  const now = new Date();
  const hour = now.getHours();
  return hour >= 9 && hour < 17;
}

// Check and update blocking based on time
async function updateTimeBasedBlocking() {
  if (isWorkHours()) {
    await setupBlockingRules();
    console.log('ChromeForge: Work hours - blocking enabled');
  } else {
    // Remove all blocking rules outside work hours
    const oldRules = await chrome.declarativeNetRequest.getDynamicRules();
    const oldRuleIds = oldRules.map(rule => rule.id);
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: oldRuleIds,
      addRules: []
    });
    console.log('ChromeForge: Outside work hours - blocking disabled');
  }
}

// Check every minute
chrome.alarms.create('checkWorkHours', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'checkWorkHours') {
    updateTimeBasedBlocking();
  }
});

// Initial check
updateTimeBasedBlocking();
'''
                base_code += time_code
        
        elif features["time_based"]:
            # Generic alarm/timer functionality
            timer_code = '''
// Periodic alarm setup
chrome.alarms.create('periodicTask', { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'periodicTask') {
    console.log('ChromeForge: Periodic task executed at', new Date().toISOString());
    // Add your periodic task logic here
  }
});
'''
            base_code += timer_code
        
        return base_code
    
    def generate_styles_css(self) -> str:
        """Generate CYBERPUNK styles.css file."""
        color = self.analysis["color_scheme"] or "#00ffff"
        
        css = f'''/* ChromeForge CYBERPUNK Edition */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');

/* CSS Variables for Cyberpunk Theme */
:root {{
  --neon-cyan: #00ffff;
  --neon-pink: #ff00ff;
  --neon-purple: #bf00ff;
  --neon-blue: #00bfff;
  --neon-green: #00ff00;
  --dark-bg: #0a0a0f;
  --darker-bg: #050508;
  --glass-bg: rgba(10, 10, 20, 0.85);
  --border-glow: rgba(0, 255, 255, 0.3);
  --text-primary: #ffffff;
  --text-secondary: #a0a0b0;
}}

/* Popup Styles */
* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

body {{
  font-family: 'Rajdhani', 'Segoe UI', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  background: linear-gradient(135deg, var(--dark-bg) 0%, #0d0d1a 50%, #1a0a1a 100%);
  min-height: 100%;
  position: relative;
  overflow: hidden;
}}

/* Animated background grid */
body::before {{
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
  z-index: 0;
}}

/* Glowing orb effect */
body::after {{
  content: '';
  position: fixed;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 30%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 70% 70%, rgba(255, 0, 255, 0.08) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: pulse 8s ease-in-out infinite;
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 0.5; transform: scale(1); }}
  50% {{ opacity: 0.8; transform: scale(1.1); }}
}}

.popup-container {{
  position: relative;
  z-index: 1;
  min-width: 320px;
  max-width: 380px;
  padding: 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-glow);
  border-radius: 16px;
  box-shadow: 
    0 0 30px rgba(0, 255, 255, 0.15),
    0 0 60px rgba(255, 0, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}}

/* Corner accents */
.popup-container::before,
.popup-container::after {{
  content: '';
  position: absolute;
  width: 30px;
  height: 30px;
  border: 2px solid var(--neon-cyan);
}}

.popup-container::before {{
  top: -2px;
  left: -2px;
  border-right: none;
  border-bottom: none;
  border-radius: 16px 0 0 0;
}}

.popup-container::after {{
  bottom: -2px;
  right: -2px;
  border-left: none;
  border-top: none;
  border-radius: 0 0 16px 0;
}}

.popup-title {{
  font-family: 'Orbitron', sans-serif;
  font-size: 20px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 3px;
  margin-bottom: 20px;
  text-align: center;
  background: linear-gradient(90deg, var(--neon-cyan) 0%, var(--neon-pink) 50%, var(--neon-cyan) 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
  text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
}}

@keyframes shimmer {{
  0% {{ background-position: 0% center; }}
  100% {{ background-position: 200% center; }}
}}

.output-area {{
  min-height: 60px;
  padding: 16px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.05) 0%, rgba(255, 0, 255, 0.05) 100%);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 12px;
  font-family: 'Rajdhani', monospace;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.6;
  color: var(--neon-cyan);
  position: relative;
  overflow: hidden;
}}

.output-area::before {{
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
  animation: scan 3s linear infinite;
}}

@keyframes scan {{
  0% {{ left: -100%; }}
  100% {{ left: 100%; }}
}}

.btn-primary {{
  width: 100%;
  padding: 14px 24px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--neon-cyan) 0%, var(--neon-purple) 100%);
  color: var(--dark-bg);
  font-family: 'Orbitron', sans-serif;
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 
    0 0 20px rgba(0, 255, 255, 0.4),
    0 0 40px rgba(0, 255, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
}}

.btn-primary::before {{
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s ease;
}}

.btn-primary:hover {{
  transform: translateY(-2px) scale(1.02);
  box-shadow: 
    0 0 30px rgba(0, 255, 255, 0.6),
    0 0 60px rgba(255, 0, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}}

.btn-primary:hover::before {{
  left: 100%;
}}

.btn-primary:active {{
  transform: translateY(0) scale(0.98);
}}

.status-message {{
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 1px;
  border: 1px solid transparent;
}}

.status-message.success {{
  background: rgba(0, 255, 0, 0.1);
  border-color: rgba(0, 255, 0, 0.3);
  color: var(--neon-green);
  box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
}}

.status-message.error {{
  background: rgba(255, 0, 100, 0.1);
  border-color: rgba(255, 0, 100, 0.3);
  color: #ff0064;
  box-shadow: 0 0 20px rgba(255, 0, 100, 0.2);
}}

.date-display {{
  font-family: 'Orbitron', sans-serif;
  font-size: 18px;
  font-weight: 500;
  text-align: center;
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}}

/* Content Script Styles - CYBERPUNK */
.cf-highlight {{
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
  position: relative;
  animation: neon-pulse 2s ease-in-out infinite;
}}

@keyframes neon-pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.8; }}
}}

.cf-phone {{
  background: linear-gradient(135deg, rgba(0, 255, 255, 0.2), rgba(0, 191, 255, 0.2));
  border: 1px solid rgba(0, 255, 255, 0.5);
  color: #00ffff !important;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3), inset 0 0 10px rgba(0, 255, 255, 0.1);
  text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
}}

.cf-email {{
  background: linear-gradient(135deg, rgba(255, 0, 255, 0.2), rgba(191, 0, 255, 0.2));
  border: 1px solid rgba(255, 0, 255, 0.5);
  color: #ff00ff !important;
  box-shadow: 0 0 10px rgba(255, 0, 255, 0.3), inset 0 0 10px rgba(255, 0, 255, 0.1);
  text-shadow: 0 0 5px rgba(255, 0, 255, 0.5);
}}

.cf-link {{
  background: linear-gradient(135deg, rgba(0, 255, 0, 0.2), rgba(0, 191, 0, 0.2));
  border: 1px solid rgba(0, 255, 0, 0.5);
  color: #00ff00 !important;
  box-shadow: 0 0 10px rgba(0, 255, 0, 0.3), inset 0 0 10px rgba(0, 255, 0, 0.1);
  text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
}}
'''
        return css
    
    def generate_rules_json(self) -> str:
        """Generate declarativeNetRequest rules.json for blocking."""
        blocked_sites = self.analysis["blocked_sites"]
        
        if not blocked_sites:
            return "[]"
        
        rules = []
        for i, site in enumerate(blocked_sites, start=1):
            rules.append({
                "id": i,
                "priority": 1,
                "action": {"type": "block"},
                "condition": {
                    "urlFilter": f"||{site}",
                    "resourceTypes": ["main_frame", "sub_frame"]
                }
            })
        
        return json.dumps(rules, indent=2)
    
    def generate_all(self) -> Dict[str, str]:
        """Generate all required files."""
        components = self.analysis["components"]
        
        if components["popup"]:
            self.files["popup.html"] = self.generate_popup_html()
            self.files["popup.js"] = self.generate_popup_js()
        
        if components["content_script"]:
            self.files["content.js"] = self.generate_content_js()
        
        if components["background"]:
            self.files["background.js"] = self.generate_background_js()
        
        if components["css"] or components["popup"] or components["content_script"]:
            self.files["styles.css"] = self.generate_styles_css()
        
        if self.analysis["features"]["block_sites"]:
            self.files["rules.json"] = self.generate_rules_json()
        
        return self.files


# ============================================================================
# PART D: FILE SYSTEM OUTPUT
# ============================================================================

class FileSystemManager:
    """Manage extension directory structure and file output."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.backup_dir = output_dir.parent / BACKUP_DIR_NAME
        self.files_written = []
    
    def prepare_directory(self) -> bool:
        """Prepare output directory, backing up if exists."""
        try:
            if self.output_dir.exists():
                # Backup existing
                if self.backup_dir.exists():
                    shutil.rmtree(self.backup_dir)
                shutil.move(str(self.output_dir), str(self.backup_dir))
                print(f"  -> Existing extension backed up to {BACKUP_DIR_NAME}/")
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"  X Error preparing directory: {e}")
            return False
    
    def write_file(self, filename: str, content: str) -> bool:
        """Write a file to the output directory."""
        try:
            filepath = self.output_dir / filename
            filepath.write_text(content, encoding='utf-8')
            self.files_written.append(filename)
            return True
        except Exception as e:
            print(f"  X Error writing {filename}: {e}")
            return False
    
    def write_manifest(self, manifest: Dict[str, Any]) -> bool:
        """Write manifest.json with proper formatting."""
        try:
            content = json.dumps(manifest, indent=2, ensure_ascii=False)
            return self.write_file("manifest.json", content)
        except Exception as e:
            print(f"  X Error writing manifest.json: {e}")
            return False
    
    def write_all_files(self, manifest: Dict[str, Any], code_files: Dict[str, str]) -> bool:
        """Write all extension files."""
        success = True
        
        # Write manifest first
        if not self.write_manifest(manifest):
            success = False
        
        # Write code files
        for filename, content in code_files.items():
            if not self.write_file(filename, content):
                success = False
        
        return success
    
    def validate_extension(self) -> Tuple[bool, List[str]]:
        """Validate the generated extension structure."""
        errors = []
        
        # Check manifest exists
        manifest_path = self.output_dir / "manifest.json"
        if not manifest_path.exists():
            errors.append("manifest.json not found")
        else:
            # Validate JSON
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Check MV3
                if manifest.get("manifest_version") != 3:
                    errors.append("manifest_version must be 3")
                
                # Check referenced files exist
                if "action" in manifest and "default_popup" in manifest["action"]:
                    popup_file = self.output_dir / manifest["action"]["default_popup"]
                    if not popup_file.exists():
                        errors.append(f"Referenced popup file not found: {manifest['action']['default_popup']}")
                
                if "background" in manifest and "service_worker" in manifest["background"]:
                    bg_file = self.output_dir / manifest["background"]["service_worker"]
                    if not bg_file.exists():
                        errors.append(f"Referenced background file not found: {manifest['background']['service_worker']}")
                
                if "content_scripts" in manifest:
                    for cs in manifest["content_scripts"]:
                        for js_file in cs.get("js", []):
                            if not (self.output_dir / js_file).exists():
                                errors.append(f"Referenced content script not found: {js_file}")
                
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in manifest.json: {e}")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> str:
        """Get a summary of written files."""
        return f"Files written: {', '.join(self.files_written)}"


# ============================================================================
# MAIN ORCHESTRATOR - CYBERPUNK EDITION 🌆
# ============================================================================

import time

# ANSI color codes + 256 color support for gradients
class Colors:
    # Basic colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    
    # Cyberpunk gradient colors (256 color mode)
    NEON_PINK = '\033[38;5;198m'
    NEON_CYAN = '\033[38;5;51m'
    NEON_PURPLE = '\033[38;5;129m'
    NEON_BLUE = '\033[38;5;39m'
    NEON_GREEN = '\033[38;5;46m'
    NEON_YELLOW = '\033[38;5;226m'
    NEON_ORANGE = '\033[38;5;208m'
    NEON_RED = '\033[38;5;196m'
    
    # Background colors
    BG_DARK = '\033[48;5;234m'
    BG_DARKER = '\033[48;5;232m'
    
    # Standard colors
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Gradient helpers
    @staticmethod
    def gradient_text(text, colors):
        """Apply gradient colors to text."""
        result = ""
        color_count = len(colors)
        for i, char in enumerate(text):
            color = colors[i % color_count]
            result += f"{color}{char}"
        return result + Colors.RESET
    
    @staticmethod
    def rgb(r, g, b):
        """Generate 24-bit color code."""
        return f'\033[38;2;{r};{g};{b}m'
    
    @staticmethod
    def bg_rgb(r, g, b):
        """Generate 24-bit background color code."""
        return f'\033[48;2;{r};{g};{b}m'


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_cyberpunk_banner():
    """Print epic cyberpunk animated banner with gradients."""
    clear_screen()
    
    # Gradient colors for the logo
    pink = Colors.NEON_PINK
    cyan = Colors.NEON_CYAN
    purple = Colors.NEON_PURPLE
    
    # Epic ASCII art with color gradient
    print(f"""
{pink}   ╔══════════════════════════════════════════════════════════════╗
   ║                                                              ║
   ║{cyan}  ░█████╗░██╗░░██╗██████╗░░█████╗░███╗░░░███╗███████╗         {pink}║
   ║{cyan}  ██╔══██╗██║░░██║██╔══██╗██╔══██╗████╗░████║██╔════╝         {pink}║
   ║{cyan}  ██║░░╚═╝███████║██████╔╝██║░░██║██╔████╔██║█████╗░░         {pink}║
   ║{cyan}  ██║░░██╗██╔══██║██╔══██╗██║░░██║██║╚██╔╝██║██╔══╝░░         {pink}║
   ║{cyan}  ╚█████╔╝██║░░██║██║░░██║╚█████╔╝██║░╚═╝░██║███████╗         {pink}║
   ║{cyan}  ░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝╚══════╝         {pink}║
   ║                                                              ║
   ║{purple}  ███████╗░█████╗░██████╗░░██████╗░███████╗                    {pink}║
   ║{purple}  ██╔════╝██╔══██╗██╔══██╗██╔════╝░██╔════╝                    {pink}║
   ║{purple}  █████╗░░██║░░██║██████╔╝██║░░██╗░█████╗░░                    {pink}║
   ║{purple}  ██╔══╝░░██║░░██║██╔══██╗██║░░╚██╗██╔══╝░░                    {pink}║
   ║{purple}  ██║░░░░░╚█████╔╝██║░░██║╚██████╔╝███████╗                    {pink}║
   ║{purple}  ╚═╝░░░░░░╚════╝░╚═╝░░╚═╝░╚═════╝░╚══════╝                    {pink}║
   ║                                                              ║
   ╠══════════════════════════════════════════════════════════════╣
   ║  {Colors.NEON_YELLOW}⚡{pink} {Colors.WHITE}CHROME EXTENSION GENERATOR{Colors.RESET}                {pink}║
   ║  {Colors.NEON_CYAN}🌐{pink} {Colors.GRAY}FAST University Tech Society{Colors.RESET}              {pink}║
   ║  {Colors.NEON_GREEN}📦{pink} {Colors.GRAY}Version {VERSION} │ Pure Python │ No APIs{Colors.RESET}          {pink}║
   ╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")


def print_glowing_divider():
    """Print a glowing cyberpunk divider."""
    gradient = [Colors.NEON_CYAN, Colors.NEON_BLUE, Colors.NEON_PURPLE, Colors.NEON_PINK]
    line = "═" * 64
    print(f"\n   {Colors.gradient_text(line, gradient)}\n")


def print_step_cyberpunk(step_num, total_steps, title):
    """Print cyberpunk styled step indicator."""
    progress = "●" * step_num + "○" * (total_steps - step_num)
    colors = [Colors.NEON_PINK, Colors.NEON_PURPLE, Colors.NEON_CYAN, Colors.NEON_BLUE]
    
    print(f"""
   {Colors.NEON_PINK}┌─────────────────────────────────────────────────────────────┐{Colors.RESET}
   {Colors.NEON_PINK}│{Colors.RESET}  {Colors.NEON_YELLOW}⚡{Colors.RESET} {Colors.BOLD}STEP {step_num}/{total_steps}{Colors.RESET}  {Colors.GRAY}│{Colors.RESET}  {colors[step_num-1]}{title}{Colors.RESET}
   {Colors.NEON_PINK}│{Colors.RESET}  {Colors.NEON_CYAN}{progress}{Colors.RESET}
   {Colors.NEON_PINK}└─────────────────────────────────────────────────────────────┘{Colors.RESET}""")


def animate_cyber_loader(message, duration=0.8):
    """Cyberpunk loading animation with neon effect."""
    frames = [
        "▰▱▱▱▱▱▱", "▰▰▱▱▱▱▱", "▰▰▰▱▱▱▱", "▰▰▰▰▱▱▱",
        "▰▰▰▰▰▱▱", "▰▰▰▰▰▰▱", "▰▰▰▰▰▰▰", "▱▰▰▰▰▰▰",
        "▱▱▰▰▰▰▰", "▱▱▱▰▰▰▰", "▱▱▱▱▰▰▰", "▱▱▱▱▱▰▰",
        "▱▱▱▱▱▱▰", "▱▱▱▱▱▱▱"
    ]
    colors = [Colors.NEON_CYAN, Colors.NEON_BLUE, Colors.NEON_PURPLE, Colors.NEON_PINK]
    
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        color = colors[i % len(colors)]
        frame = frames[i % len(frames)]
        print(f"\r   {color}{frame}{Colors.RESET} {Colors.GRAY}{message}{Colors.RESET}", end='', flush=True)
        time.sleep(0.06)
        i += 1
    print(f"\r   {Colors.NEON_GREEN}▰▰▰▰▰▰▰{Colors.RESET} {Colors.WHITE}{message}{Colors.RESET} {Colors.NEON_GREEN}✓{Colors.RESET}           ")


def print_neon_progress_bar(progress, total, label=""):
    """Print a neon-styled progress bar."""
    width = 40
    filled = int(width * progress / total)
    empty = width - filled
    
    # Gradient effect on filled portion
    bar_filled = ""
    for i in range(filled):
        if i < filled // 3:
            bar_filled += f"{Colors.NEON_CYAN}█"
        elif i < 2 * filled // 3:
            bar_filled += f"{Colors.NEON_PURPLE}█"
        else:
            bar_filled += f"{Colors.NEON_PINK}█"
    
    bar_empty = f"{Colors.GRAY}{'░' * empty}{Colors.RESET}"
    percent = int(100 * progress / total)
    
    print(f"\r   {Colors.NEON_PINK}[{Colors.RESET}{bar_filled}{bar_empty}{Colors.NEON_PINK}]{Colors.RESET} {Colors.NEON_YELLOW}{percent}%{Colors.RESET} {Colors.GRAY}{label}{Colors.RESET}", end='', flush=True)


def print_analysis_cyberpunk(analysis: Dict[str, Any]):
    """Print analysis in cyberpunk holographic card style."""
    
    print(f"""
   {Colors.NEON_CYAN}╔══════════════════════════════════════════════════════════╗{Colors.RESET}
   {Colors.NEON_CYAN}║{Colors.RESET}  {Colors.NEON_YELLOW}◈{Colors.RESET} {Colors.BOLD}{Colors.WHITE}NEURAL ANALYSIS COMPLETE{Colors.RESET}                             {Colors.NEON_CYAN}║{Colors.RESET}
   {Colors.NEON_CYAN}╠══════════════════════════════════════════════════════════╣{Colors.RESET}""")
    
    # Status
    status_icon = f"{Colors.NEON_GREEN}◉ VALID{Colors.RESET}" if analysis['valid'] else f"{Colors.NEON_RED}◉ INVALID{Colors.RESET}"
    print(f"   {Colors.NEON_CYAN}║{Colors.RESET}  {Colors.GRAY}Status:{Colors.RESET} {status_icon}                                        {Colors.NEON_CYAN}║{Colors.RESET}")
    
    # Intent
    if analysis['intents']:
        top_intent = max(analysis['intents'].items(), key=lambda x: x[1])
        intent_bar = "█" * int(top_intent[1] * 10) + "░" * (10 - int(top_intent[1] * 10))
        print(f"   {Colors.NEON_CYAN}║{Colors.RESET}  {Colors.GRAY}Intent:{Colors.RESET} {Colors.NEON_PURPLE}{top_intent[0]:<20}{Colors.RESET} {Colors.NEON_CYAN}{intent_bar}{Colors.RESET} {Colors.NEON_YELLOW}{top_intent[1]:.0%}{Colors.RESET}   {Colors.NEON_CYAN}║{Colors.RESET}")
    
    print(f"   {Colors.NEON_CYAN}╠══════════════════════════════════════════════════════════╣{Colors.RESET}")
    print(f"   {Colors.NEON_CYAN}║{Colors.RESET}  {Colors.NEON_PINK}◈{Colors.RESET} {Colors.BOLD}DETECTED COMPONENTS{Colors.RESET}                                  {Colors.NEON_CYAN}║{Colors.RESET}")
    
    # Components with icons
    comp_icons = {
        "popup": "🎯", "content_script": "📜", "background": "⚙️",
        "storage": "💾", "css": "🎨"
    }
    
    for comp, needed in analysis['components'].items():
        icon = comp_icons.get(comp, "•")
        status = f"{Colors.NEON_GREEN}◉ ENABLED{Colors.RESET}" if needed else f"{Colors.GRAY}○ disabled{Colors.RESET}"
        print(f"   {Colors.NEON_CYAN}║{Colors.RESET}    {icon} {comp:<15} {status}                      {Colors.NEON_CYAN}║{Colors.RESET}")
    
    # Features
    active_features = [k for k, v in analysis['features'].items() if v]
    if active_features:
        print(f"   {Colors.NEON_CYAN}╠══════════════════════════════════════════════════════════╣{Colors.RESET}")
        print(f"   {Colors.NEON_CYAN}║{Colors.RESET}  {Colors.NEON_YELLOW}⚡{Colors.RESET} {Colors.BOLD}FEATURES ACTIVATED{Colors.RESET}                                   {Colors.NEON_CYAN}║{Colors.RESET}")
        for feat in active_features[:4]:
            feat_name = feat.replace('_', ' ').title()
            print(f"   {Colors.NEON_CYAN}║{Colors.RESET}    {Colors.NEON_GREEN}▸{Colors.RESET} {feat_name:<50}   {Colors.NEON_CYAN}║{Colors.RESET}")
    
    # Blocked sites
    if analysis['blocked_sites']:
        print(f"   {Colors.NEON_CYAN}╠══════════════════════════════════════════════════════════╣{Colors.RESET}")
        print(f"   {Colors.NEON_CYAN}║{Colors.RESET}  {Colors.NEON_RED}🚫{Colors.RESET} {Colors.BOLD}SITES TO BLOCK{Colors.RESET}                                       {Colors.NEON_CYAN}║{Colors.RESET}")
        for site in analysis['blocked_sites'][:3]:
            print(f"   {Colors.NEON_CYAN}║{Colors.RESET}    {Colors.NEON_RED}✖{Colors.RESET} {site:<50}   {Colors.NEON_CYAN}║{Colors.RESET}")
    
    print(f"   {Colors.NEON_CYAN}╚══════════════════════════════════════════════════════════╝{Colors.RESET}")


def print_success_cyberpunk(output_dir: Path):
    """Print epic cyberpunk success message with baby step instructions."""
    
    print(f"""
   {Colors.NEON_GREEN}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}                                                              {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}   {Colors.NEON_YELLOW}★ ═══════════════════════════════════════════════════ ★{Colors.RESET}   {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}   {Colors.NEON_YELLOW}║{Colors.RESET}                                                     {Colors.NEON_YELLOW}║{Colors.RESET}   {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}   {Colors.NEON_YELLOW}║{Colors.RESET}    {Colors.BOLD}{Colors.NEON_CYAN}✨ EXTENSION FORGED SUCCESSFULLY! ✨{Colors.RESET}        {Colors.NEON_YELLOW}║{Colors.RESET}   {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}   {Colors.NEON_YELLOW}║{Colors.RESET}                                                     {Colors.NEON_YELLOW}║{Colors.RESET}   {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}   {Colors.NEON_YELLOW}★ ═══════════════════════════════════════════════════ ★{Colors.RESET}   {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}║{Colors.RESET}                                                              {Colors.NEON_GREEN}║{Colors.RESET}
   {Colors.NEON_GREEN}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}

   {Colors.NEON_PURPLE}📁 YOUR EXTENSION IS READY AT:{Colors.RESET}
   {Colors.NEON_CYAN}   {output_dir}{Colors.RESET}

   {Colors.NEON_PINK}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_YELLOW}🚀{Colors.RESET} {Colors.BOLD}{Colors.WHITE}LOAD YOUR EXTENSION IN CHROME - BABY STEPS{Colors.RESET}           {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}╠══════════════════════════════════════════════════════════════╣{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_CYAN}STEP 1:{Colors.RESET} {Colors.WHITE}Open Google Chrome browser{Colors.RESET}                       {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}(The browser with the colorful circle icon){Colors.RESET}        {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_CYAN}STEP 2:{Colors.RESET} {Colors.WHITE}Type this in the address bar:{Colors.RESET}                    {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.NEON_YELLOW}chrome://extensions{Colors.RESET}                               {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}(Where you normally type website URLs){Colors.RESET}              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_CYAN}STEP 3:{Colors.RESET} {Colors.WHITE}Turn ON "Developer mode"{Colors.RESET}                          {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}(Toggle switch in the TOP RIGHT corner){Colors.RESET}             {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.NEON_GREEN}[====●]{Colors.RESET} {Colors.GRAY}<-- Make it look like this{Colors.RESET}                 {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_CYAN}STEP 4:{Colors.RESET} {Colors.WHITE}Click the "Load unpacked" button{Colors.RESET}                  {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}(It appears after enabling Developer mode){Colors.RESET}          {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.NEON_PURPLE}┌─────────────────┐{Colors.RESET}                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.NEON_PURPLE}│  Load unpacked  │{Colors.RESET} {Colors.GRAY}<-- Click this{Colors.RESET}                 {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.NEON_PURPLE}└─────────────────┘{Colors.RESET}                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_CYAN}STEP 5:{Colors.RESET} {Colors.WHITE}Navigate to this folder:{Colors.RESET}                         {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.NEON_YELLOW}generated_extension{Colors.RESET}                               {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}(It's in the same folder as chrome_forge.py){Colors.RESET}         {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_CYAN}STEP 6:{Colors.RESET} {Colors.WHITE}Click "Select Folder" button{Colors.RESET}                      {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}(Bottom right of the folder picker window){Colors.RESET}           {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}  {Colors.NEON_GREEN}✓ DONE!{Colors.RESET} {Colors.WHITE}Your extension is now installed!{Colors.RESET}                 {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}Look for the puzzle piece icon 🧩 in Chrome{Colors.RESET}          {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}          {Colors.GRAY}Click it to see and use your extension!{Colors.RESET}              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}║{Colors.RESET}                                                              {Colors.NEON_PINK}║{Colors.RESET}
   {Colors.NEON_PINK}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}

   {Colors.NEON_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}
   {Colors.NEON_PURPLE}🎮{Colors.RESET} {Colors.GRAY}Built with{Colors.RESET} {Colors.NEON_PINK}♥{Colors.RESET} {Colors.GRAY}by ChromeForge │ FAST University Tech Society{Colors.RESET}
   {Colors.NEON_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}
""")


def get_user_prompt_cyberpunk() -> str:
    """Get prompt from user with cyberpunk UI."""
    
    print(f"""
   {Colors.NEON_PURPLE}╔══════════════════════════════════════════════════════════════╗{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.NEON_YELLOW}💡{Colors.RESET} {Colors.BOLD}{Colors.WHITE}DESCRIBE YOUR EXTENSION{Colors.RESET}                                {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}                                                              {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.GRAY}Tell me what you want your Chrome extension to do.{Colors.RESET}        {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.GRAY}Just describe it in plain English - like talking to a{Colors.RESET}     {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.GRAY}friend! I'll handle all the coding.{Colors.RESET}                       {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}                                                              {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}╠══════════════════════════════════════════════════════════════╣{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.NEON_CYAN}💭 EXAMPLE IDEAS:{Colors.RESET}                                          {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}                                                              {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.NEON_GREEN}▸{Colors.RESET} {Colors.WHITE}"Show popup with today's date"{Colors.RESET}                      {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.NEON_GREEN}▸{Colors.RESET} {Colors.WHITE}"Highlight all phone numbers on any website"{Colors.RESET}         {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.NEON_GREEN}▸{Colors.RESET} {Colors.WHITE}"Block Facebook and TikTok"{Colors.RESET}                          {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}  {Colors.NEON_GREEN}▸{Colors.RESET} {Colors.WHITE}"Change all text to blue when I click a button"{Colors.RESET}      {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}║{Colors.RESET}                                                              {Colors.NEON_PURPLE}║{Colors.RESET}
   {Colors.NEON_PURPLE}╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")
    
    try:
        prompt = input(f"   {Colors.NEON_PINK}▶{Colors.RESET} {Colors.NEON_CYAN}Your idea:{Colors.RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        prompt = ""
    
    return prompt


def main():
    """Main entry point with cyberpunk UX."""
    print_cyberpunk_banner()
    
    # Get prompt
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:]).strip()
        print(f"\n   {Colors.NEON_PURPLE}▶{Colors.RESET} {Colors.GRAY}Using prompt:{Colors.RESET} {Colors.WHITE}{prompt}{Colors.RESET}\n")
    else:
        prompt = get_user_prompt_cyberpunk()
    
    if not prompt:
        print(f"\n   {Colors.NEON_YELLOW}ℹ{Colors.RESET} {Colors.GRAY}No prompt provided. Creating default date extension.{Colors.RESET}\n")
        prompt = "Show a popup with today's date"
    
    print_glowing_divider()
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: PART A - Analyze prompt
    # ═══════════════════════════════════════════════════════════════
    print_step_cyberpunk(1, 4, "ANALYZING YOUR IDEA")
    animate_cyber_loader("Scanning keywords...", 0.5)
    animate_cyber_loader("Detecting intent...", 0.4)
    animate_cyber_loader("Mapping components...", 0.4)
    
    analyzer = PromptAnalyzer(prompt)
    analysis = analyzer.analyze()
    
    print_neon_progress_bar(1, 1, "Analysis complete!")
    print("\n")
    
    print_analysis_cyberpunk(analysis)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: PART B - Build manifest
    # ═══════════════════════════════════════════════════════════════
    print_step_cyberpunk(2, 4, "BUILDING MANIFEST V3")
    animate_cyber_loader("Creating manifest structure...", 0.5)
    animate_cyber_loader("Adding permissions...", 0.3)
    animate_cyber_loader("Validating JSON...", 0.3)
    
    manifest_builder = ManifestBuilder(analysis)
    manifest = manifest_builder.build()
    is_valid, errors = manifest_builder.validate()
    
    if not is_valid:
        print(f"\n   {Colors.NEON_RED}✗ Manifest validation failed:{Colors.RESET} {errors}")
        return 1
    
    print(f"\n   {Colors.NEON_GREEN}✓{Colors.RESET} {Colors.WHITE}Manifest V3 validated successfully{Colors.RESET}")
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: PART C - Generate code
    # ═══════════════════════════════════════════════════════════════
    print_step_cyberpunk(3, 4, "GENERATING EXTENSION CODE")
    
    code_generator = CodeGenerator(analysis)
    code_files = code_generator.generate_all()
    
    total_files = len(code_files)
    for i, filename in enumerate(code_files.keys(), 1):
        animate_cyber_loader(f"Forging {filename}...", 0.3)
        print_neon_progress_bar(i, total_files, filename)
        time.sleep(0.1)
    
    print(f"\n\n   {Colors.NEON_GREEN}✓{Colors.RESET} {Colors.WHITE}Generated {total_files} files{Colors.RESET}")
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: PART D - Write files
    # ═══════════════════════════════════════════════════════════════
    print_step_cyberpunk(4, 4, "WRITING EXTENSION FILES")
    
    output_dir = Path.cwd() / OUTPUT_DIR_NAME
    fs_manager = FileSystemManager(output_dir)
    
    animate_cyber_loader("Preparing output directory...", 0.3)
    
    if not fs_manager.prepare_directory():
        return 1
    
    animate_cyber_loader("Writing files to disk...", 0.4)
    
    if not fs_manager.write_all_files(manifest, code_files):
        return 1
    
    animate_cyber_loader("Validating extension structure...", 0.3)
    
    # Validate final output
    is_valid, errors = fs_manager.validate_extension()
    if is_valid:
        print(f"\n   {Colors.NEON_GREEN}✓{Colors.RESET} {Colors.WHITE}Extension validated and ready!{Colors.RESET}")
    else:
        print(f"\n   {Colors.NEON_YELLOW}⚠{Colors.RESET} {Colors.GRAY}Warnings: {errors}{Colors.RESET}")
    
    # Success!
    print_glowing_divider()
    print_success_cyberpunk(output_dir)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
