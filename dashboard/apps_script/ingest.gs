function doPost(e) {
  var key = e.headers['X-RDS-Key'];
  if (!key) {
    return ContentService.createTextOutput('missing key').setResponseCode(401);
  }
  var payload = Utilities.newBlob(e.postData.contents).getDataAsString();
  var json = JSON.parse(payload);
  var sheet = SpreadsheetApp.getActive().getSheetByName('health');
  sheet.appendRow([new Date(), json.store, JSON.stringify(json.targets)]);
  return ContentService.createTextOutput('ok');
}

function doGet(e) {
  var path = e.pathInfo || '';
  if (path.indexOf('watchlist') !== -1) {
    return ContentService.createTextOutput(JSON.stringify({"stores":{}}));
  }
  if (path.indexOf('trigger') !== -1) {
    return ContentService.createTextOutput(JSON.stringify({"refresh":false}));
  }
  return ContentService.createTextOutput('{}');
}
