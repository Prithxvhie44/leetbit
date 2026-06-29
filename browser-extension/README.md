# Leetbit Browser Helper

This optional extension reads the active `LEETCODE_SESSION` cookie after you sign in to LeetCode and sends it to the backend.

It can also start the GitHub OAuth device flow through the backend, so the user does not need to paste a long-lived token.

## Load it locally

1. Open Chrome or Edge extensions.
2. Enable developer mode.
3. Load the `browser-extension/` folder as an unpacked extension.
4. Set the backend URL in the popup.

## What it does

- Captures the current LeetCode session cookie.
- Stores the LeetCode session in SQLite through `/auth/leetcode/connect`.
- Starts and completes GitHub OAuth device login through `/auth/github/device/start` and `/auth/github/device/complete`.

The extension is optional. Manual env vars still work for advanced users.