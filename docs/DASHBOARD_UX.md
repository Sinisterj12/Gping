# Dashboard UX Notes

The in-store agent exposes data for a future dashboard but keeps the runtime headless unless an unlock token exists.

## Role-aware Behaviors
- **Locked (default)**: `web_local` emits `{locked: true}` so no local UI is rendered.
- **Unlocked**: JSON snapshot includes calm R/A/G pulse status, “Last failure reason”, last upload timestamp, and a 24-hour summary stub.

## Label & Tooltip Rules
- Buttons use plain labels such as “Check Internet” and “Send Status Now”.
- Tooltips are capped at 12 words. Example: “Runs current probes without delay”.

## Accessibility
- High-contrast color palette (green/amber/red) with steady pulses; no CPU-intensive animation.
- Keyboard navigation is supported by exposing actions as discrete commands in the future REST shim.

## Future Work
- Bind the JSON snapshot to a local Electron/WebView shell when the unlock token is present.
- Enforce role-based limits by mapping Google accounts to the manager vs. technician scopes.
