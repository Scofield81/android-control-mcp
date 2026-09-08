# Android 13 / MIUI test notes

Validated device:

- Model: Xiaomi M2101K9G
- Android: 13 / SDK 33
- MIUI: Global 14.0.9
- Resolution: 1080x2400
- ADB transport: Wi-Fi ADB

## Control model

- Use `scrcpy` primarily as a live visual mirror.
- Do not use host mouse coordinates for automation. They depend on the scrcpy
  window position, DPI scaling, and the user's physical mouse.
- Prefer Android device coordinates from `uiautomator dump` bounds and ADB
  input commands.
- When a gesture must be continuous, send the full gesture in one ADB shell
  command chain with `input touchscreen motionevent DOWN/MOVE/UP`. Multiple
  separate ADB calls can be too slow over Wi-Fi.

## Pattern unlock

- Only unlock a phone with explicit user authorization and user-provided lock
  method.
- Never log the user's pattern, PIN, or password.
- First bring up the real pattern view and verify it with UI dump.
- On this device the pattern view appeared as:

```text
com.android.systemui:id/lockPatternView bounds=[141,1263][939,2061]
```

- Compute grid points from the detected bounds. Do not hardcode points from a
  screenshot unless there is no structured UI available.
- Verify unlock with foreground and lockscreen state. A MIUI wallpaper or
  `fashiongallery` activity is not enough; a real unlocked state should show
  the launcher/app focus and `mDreamingLockscreen=false`.

## Timed install prompt

MIUI may show `Telepites USB-n keresztul` for a short time during `adb install`.
On this tested device the successful pattern was:

1. Start `adb install` in the background.
2. Wait about 4.2 seconds.
3. Tap the remember/confirmation checkbox.
4. Wait about 250 ms.
5. Tap `Telepites`.

This timing and the button coordinates are device/ROM dependent. Prefer UI dump
or visual verification when time allows.

## WhatsApp Business messaging

- Open the app by package name: `com.whatsapp.w4b`.
- Do not rely on home screen icon positions.
- `HOME` only backgrounds the app. The next launch may resume the last chat, so
  it is not a representative "find recipient" workflow.
- In a chat with the keyboard open, one `BACK` closes the keyboard, the next
  `BACK` returns to the conversation list, and another `BACK` exits/backgrounds
  the app.
- Before sending, verify the chat header in UI dump:

```text
com.whatsapp.w4b:id/conversation_contact_name
```

- If a requested contact name appears more than once, stop and ask the user
  which exact recipient to use.
- Verify the message field:

```text
com.whatsapp.w4b:id/entry
```

- Verify the send button:

```text
com.whatsapp.w4b:id/send
content-desc="Kuldes" or localized equivalent
```

- Conservative mode: tap send only after both the recipient and exact message
  text are visible in the UI dump.
- Fast mode: verify the recipient once, type the message, and tap send with a
  cached send-button coordinate for the tested device layout. This is faster,
  but depends on the keyboard and screen layout staying unchanged.

Measured on this device:

- Warm resume to already open target chat: 14.859 s.
- Fresh app start, full UI verification: 17.036 s.
- Fresh app start, single recipient verification: 9.945 s.

## Wi-Fi toggle

- If the only active ADB transport is Wi-Fi ADB, do not automate Wi-Fi OFF unless
  there is a tested fallback path, such as USB ADB.
- Otherwise the control channel is lost before the agent can turn Wi-Fi back on.
- It is safe to observe the quick settings panel and document the current Wi-Fi
  tile state via UI dump.

## Multiple ADB entries

The same Wi-Fi ADB device may appear more than once through mDNS. Use an explicit
serial for every command when multiple entries are visible.
