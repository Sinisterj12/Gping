# Apps Script Contract

All outbound calls use HTTPS with the header `X-RDS-Key` for authentication and an `X-Idempotency-Key` per upload.

## POST /ingest
Uploads health or inventory payloads as gzip-compressed JSON.

```bash
curl -X POST "https://script.google.com/macros/s/app-id/ingest" \
  -H "Content-Type: application/json" \
  -H "Content-Encoding: gzip" \
  -H "X-RDS-Key: demo-key" \
  -H "X-Idempotency-Key: health-STORE-2024-01-01T12:00:00Z" \
  --data-binary @payload.json.gz
```

## GET /watchlist
Returns stores requiring elevated cadence until a date.

```bash
curl -H "X-RDS-Key: demo-key" \
  "https://script.google.com/macros/s/app-id/watchlist"
```

Example response:

```json
{"stores":{"KS-218":{"mode":"watch","until":"2024-04-01"}}}
```

## GET /trigger/<store>
Fetches and clears refresh-now flags.

```bash
curl -H "X-RDS-Key: demo-key" \
  "https://script.google.com/macros/s/app-id/trigger/KS-218"
```

Response body:

```json
{"refresh":true}
```

When the agent sees `refresh: true` it immediately uploads the latest health payload then clears the trigger via:

```bash
curl -X POST "https://script.google.com/macros/s/app-id/trigger/KS-218" \
  -H "X-RDS-Key: demo-key" \
  -H "Content-Type: application/json" \
  -H "Content-Encoding: gzip" \
  -H "X-Idempotency-Key: clear-KS-218" \
  --data-binary @clear.json.gz
```
