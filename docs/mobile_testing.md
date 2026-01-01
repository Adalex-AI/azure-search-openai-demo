# Mobile Testing Guide for Legal RAG Application

This guide explains how to test the mobile UI on various devices before deploying.

## Quick Start

```bash
# Terminal 1: Start the backend
cd app/backend
source ../../.venv/bin/activate
quart run -p 50505

# Terminal 2: Start the frontend with network access
cd app/frontend
npm run dev:mobile
```

The frontend will display:
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/   ← Use this for phone testing
```

**Alternative (use regular dev for localhost only):**
```bash
npm run dev   # localhost only
```

## Testing Options

### Option 1: Browser DevTools (Fastest)

1. Open Chrome/Edge and go to `http://localhost:5173/`
2. Press **F12** to open DevTools
3. Click the **device toolbar icon** (or press `Ctrl+Shift+M` / `Cmd+Shift+M`)
4. Select a phone model (iPhone 14, Pixel 7, Galaxy S20, etc.)
5. Test different orientations and screen sizes

**Recommended device presets:**
- iPhone SE (375x667) - Small phone
- iPhone 14 Pro (393x852) - Standard iPhone
- Pixel 7 (412x915) - Standard Android
- Galaxy S20 Ultra (412x915) - Large Android

### Option 2: Your Real Phone (Same WiFi Network)

1. Ensure your phone and computer are on the **same WiFi network**
2. Find your computer's local IP:
   - **Mac**: `ipconfig getifaddr en0`
   - **Windows**: `ipconfig` → Look for IPv4 Address
   - **Linux**: `hostname -I`
3. On your phone, open the browser and go to: `http://<your-ip>:5173/`

**Example:** `http://192.168.1.100:5173/`

**Troubleshooting:**
- Disable Windows Firewall temporarily if blocked
- On Mac: Allow incoming connections in Security preferences
- Some corporate networks block device-to-device connections

### Option 3: ngrok (Public URL for Remote Testing)

[ngrok](https://ngrok.com/) creates a public tunnel to your local server.

```bash
# Install ngrok
brew install ngrok  # Mac
# or download from https://ngrok.com/download

# Create a tunnel to your frontend
ngrok http 5173
```

This gives you a public URL like: `https://abc123.ngrok-free.app`

**Benefits:**
- Test on any device, anywhere
- Share with colleagues for feedback
- Works through firewalls

### Option 4: Android Emulator (Full Device Simulation)

**Requirements:** Android Studio

```bash
# Install Android Studio from https://developer.android.com/studio
# Open AVD Manager and create a virtual device
# Start the emulator

# Access localhost from emulator using special IP:
# http://10.0.2.2:5173/
```

### Option 5: iOS Simulator (Mac only)

**Requirements:** Xcode (free from App Store)

```bash
# Install Xcode from App Store
# Open Simulator: Xcode → Open Developer Tool → Simulator
# Choose a device: File → Open Device

# Access via localhost:
# http://localhost:5173/
```

### Option 6: Chrome Remote Debugging (Android)

Connect your Android phone via USB for real device debugging:

1. Enable **Developer Options** on your phone:
   - Settings → About Phone → Tap "Build Number" 7 times
2. Enable **USB Debugging** in Developer Options
3. Connect phone via USB
4. Open Chrome on your phone and navigate to the app
5. On your computer, open Chrome and go to: `chrome://inspect`
6. Click "inspect" under your device

This allows you to:
- See console logs from phone
- Inspect elements
- Debug CSS issues
- Profile performance

## Mobile UI Features

### What Regular Users See (Default)
- ✅ Chat interface with answer cards
- ✅ Source category dropdown
- ✅ Search depth selector
- ✅ Inline citations [1], [2], [3]
- ✅ Citation list below answers
- ✅ "Supporting Content" button (sources)
- ✅ Copy button
- ✅ Follow-up questions
- ✅ AI disclaimer

### What's Hidden for Regular Users
- ❌ Thought Process button (developer feature)
- ❌ Settings panel toggle (developer feature)
- ❌ History panel toggle (developer feature)

### Admin Mode (for developers)
Add `?admin=true` to the URL to see all features:
```
http://localhost:5173/?admin=true
http://192.168.1.100:5173/?admin=true
```

## Mobile-Specific CSS

Mobile styles are in: `app/frontend/src/customizations/mobile.css`

Key breakpoints:
- `768px` - Tablet/phone breakpoint
- `375px` - Very small phones
- Landscape orientation handling

## Testing Checklist

### Basic Functionality
- [ ] Chat loads without errors
- [ ] Can type and submit questions
- [ ] Answers display correctly
- [ ] Citations are tappable
- [ ] Supporting content panel opens
- [ ] Category dropdown works
- [ ] Search depth dropdown works

### Visual Layout
- [ ] Header fits and is readable
- [ ] No horizontal scrolling
- [ ] Text is readable (16px+ for inputs)
- [ ] Touch targets are 44px+ minimum
- [ ] Answer cards don't overflow
- [ ] Citations wrap properly

### Usability
- [ ] Input doesn't zoom on iOS
- [ ] Keyboard doesn't cover input
- [ ] Scrolling is smooth
- [ ] Dropdowns are usable
- [ ] Panels close properly

### Edge Cases
- [ ] Long answers display correctly
- [ ] Many citations wrap properly
- [ ] Error messages are visible
- [ ] Loading states work
- [ ] Landscape orientation works

## Performance Tips

1. **Test on real devices** - Emulators are faster than real phones
2. **Test on lower-end devices** - Not everyone has the latest phone
3. **Test on 3G/4G** - Add network throttling in DevTools
4. **Check battery usage** - Long-running animations drain battery

## Troubleshooting

### "Can't connect from phone"
- Check firewall settings
- Ensure same WiFi network
- Try turning off VPN
- Check if port 5173 is accessible

### "App zooms when typing"
- Input font size should be 16px+ (already set in mobile.css)

### "Elements too small to tap"
- Touch targets should be 44px+ (already set in mobile.css)

### "Horizontal scroll"
- Check for fixed-width elements
- Use DevTools to find overflow

## PWA (Progressive Web App) - Future Enhancement

For offline support and "Add to Home Screen", add a service worker:

```typescript
// This would go in src/sw.ts
// Not implemented yet, but planned for production
```

## Related Files

- `app/frontend/src/customizations/mobile.css` - Mobile styles
- `app/frontend/vite.config.ts` - Dev server config (host: true)
- `app/frontend/index.html` - Viewport and mobile meta tags
- `app/frontend/src/customizations/config.ts` - Feature flags (adminMode)
