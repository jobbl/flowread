// For cross-browser compatibility (Firefox uses browser, Chrome uses chrome)
if (typeof browser === "undefined") {
  var browser = chrome;
}

browser.runtime.onInstalled.addListener(() => {
  browser.contextMenus.create({
    id: "flowread-selection",
    title: "FlowRead Highlight",
    contexts: ["selection"]
  });
  
  browser.contextMenus.create({
    id: "flowread-page",
    title: "FlowRead Entire Page",
    contexts: ["page"]
  });
});

browser.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "flowread-selection") {
    // Send a message to the content script asking it to grab the selection and replace it
    browser.tabs.sendMessage(tab.id, {
      action: "flowread_selection",
      text: info.selectionText
    });
  } else if (info.menuItemId === "flowread-page") {
    browser.tabs.sendMessage(tab.id, {
      action: "flowread_page"
    });
  }
});

browser.commands.onCommand.addListener((command) => {
  if (command === "flowread-page") {
    browser.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (tabs[0]) {
        browser.tabs.sendMessage(tabs[0].id, {
          action: "flowread_page"
        });
      }
    });
  }
});
