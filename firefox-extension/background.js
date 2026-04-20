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
});

browser.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "flowread-selection") {
    // We send a message to the content script asking it to grab the selection and replace it
    browser.tabs.sendMessage(tab.id, {
      action: "flowread_selection",
      text: info.selectionText
    });
  }
});
