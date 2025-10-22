# Apps Script Stub

This folder contains a minimal Google Apps Script example for the GPING NEXT telemetry bridge.

* `doPost` handles `/ingest` uploads, expecting gzip JSON with the header `X-RDS-Key`.
* `doGet` returns empty watchlists and triggers so the agent has a contract to integrate with.

Update the script to write to real Sheets tabs (`health`, `inventory`) and enforce authentication in production.
