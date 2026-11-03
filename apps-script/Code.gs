/**
 * Room Sensor - receiver for the Google Sheet.
 *
 * Paste this whole file into Extensions > Apps Script of your Google Sheet,
 * change SECRET below, then Deploy > New deployment > Web app
 * (Execute as: Me, Who has access: Anyone).
 */

var SECRET = 'change-me-to-something-only-you-know';
var SHEET_NAME = 'Readings';
var HEADERS = ['time', 'room', 'event', 'motion_avg', 'motion_max', 'moving_secs',
               'noise_avg', 'noise_max', 'light', 'battery', 'charging', 'received_at'];

function doPost(e) {
  var data;
  try {
    data = JSON.parse(e.postData.contents);
  } catch (err) {
    return json_({ ok: false, error: 'bad json' });
  }
  if (data.key !== SECRET) return json_({ ok: false, error: 'wrong key' });

  var rows = data.rows || [];
  if (!rows.length) return json_({ ok: true, added: 0 });

  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sheet = getSheet_();
    var now = new Date();
    var values = rows.map(function (r) {
      return HEADERS.map(function (h) { return h === 'received_at' ? now : (r[h] === undefined ? '' : r[h]); });
    });
    sheet.getRange(sheet.getLastRow() + 1, 1, values.length, HEADERS.length).setValues(values);
  } finally {
    lock.releaseLock();
  }
  return json_({ ok: true, added: rows.length });
}

// Open the web-app URL in a browser to check it is deployed.
function doGet() {
  return ContentService.createTextOutput('Room Sensor receiver is running. Rows so far: ' +
    Math.max(0, getSheet_().getLastRow() - 1));
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
