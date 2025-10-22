"use strict";

const SHEET_NAME = "health";
const EXPECTED_KEY = "demo-key";

function ensureSheet_() {
  const ss = SpreadsheetApp.getActive();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(["timestamp", "store", "payload"]);
  }
  return sheet;
}

function doPost(e) {
  const headers = (e && e.headers) || {};
  const key = headers["X-RDS-Key"];
  if (key !== EXPECTED_KEY) {
    return ContentService.createTextOutput("unauthorized");
  }
  try {
    const base64 = e && e.postData ? e.postData.contents : "";
    const binary = Utilities.base64Decode(base64);
    const compressed = Utilities.newBlob(binary, "application/octet-stream", "payload.gz");
    const uncompressed = Utilities.gunzip(compressed).getDataAsString("utf-8");
    const payload = JSON.parse(uncompressed);
    const sheet = ensureSheet_();
    sheet.appendRow([new Date(), payload.store || "unknown", JSON.stringify(payload.targets || [])]);
    return ContentService.createTextOutput("ok");
  } catch (err) {
    console.error(err);
    return ContentService.createTextOutput("invalid payload");
  }
}

function doGet(e) {
  const path = (e && e.pathInfo) || "";
  if (path.indexOf("watchlist") !== -1) {
    return ContentService.createTextOutput(JSON.stringify({ stores: {} }));
  }
  if (path.indexOf("trigger") !== -1) {
    return ContentService.createTextOutput(JSON.stringify({ refresh: false }));
  }
  return ContentService.createTextOutput("{}");
}
