// ChromeForge Generated Background Service Worker
console.log('ChromeForge: Background service worker starting');

// Installation handler
chrome.runtime.onInstalled.addListener((details) => {
  console.log('ChromeForge: Extension installed', details.reason);
});

// Startup handler
chrome.runtime.onStartup.addListener(() => {
  console.log('ChromeForge: Browser started with extension');
});

// Site blocking configuration
const BLOCKED_SITES = ["facebook.com", "twitter.com", "instagram.com"];

// Dynamic rule creation for blocking
async function setupBlockingRules() {
  const rules = BLOCKED_SITES.map((site, index) => ({
    id: index + 1,
    priority: 1,
    action: { type: 'block' },
    condition: {
      urlFilter: '*://*.' + site + '/*',
      resourceTypes: ['main_frame', 'sub_frame']
    }
  }));
  
  try {
    // Remove old rules first
    const oldRules = await chrome.declarativeNetRequest.getDynamicRules();
    const oldRuleIds = oldRules.map(rule => rule.id);
    
    await chrome.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: oldRuleIds,
      addRules: rules
    });
    
    console.log('ChromeForge: Blocking rules installed for', BLOCKED_SITES);
  } catch (error) {
    console.error('ChromeForge: Error setting up blocking rules', error);
  }
}

// Setup blocking on install
chrome.runtime.onInstalled.addListener(setupBlockingRules);
chrome.runtime.onStartup.addListener(setupBlockingRules);

