# Putting Duo Arcade on the App Store and Google Play

## What's already done

The arcade is now ready to be wrapped as a phone app:

- **The pages travel with the app.** Everything except the games themselves is
  bundled, so the app opens instantly instead of waiting for the server.
- **The app can reach the server from anywhere.** `static/app.js` aims its
  requests at `https://duo-arcade.onrender.com` when it detects it is running
  inside an app, and the server now allows requests from other origins.
- **Invite links still point at the website**, so the friend you invite can join
  from a browser whether or not they have the app.
- **App icons exist** at every size the stores want (`static/icons/`), redrawn
  any time with `python3 tools/make_icons.py`.
- **`build-web.sh` assembles `www/`**, which is what gets wrapped.

The same groundwork makes the website installable straight to a phone's home
screen — see "The free alternative" at the bottom.

> **None of the steps below have been run on this machine.** Node, Xcode and
> Android Studio are not installed here, so the wrapper projects have not been
> built or tested. The configuration is standard, but treat the first build as
> the real test.

## What you have to do yourself

These need your identity, your card and your Apple ID, so they can't be done
for you.

| | Apple | Google |
| --- | --- | --- |
| Account | Apple Developer Program | Play Console |
| Cost | **$99 USD a year** | **$25 USD once** |
| Sign up | developer.apple.com/programs | play.google.com/console/signup |
| Verification | ID check, can take days | ID check |
| Build tool | **Xcode** (Mac App Store, ~10 GB) | **Android Studio** (~1 GB) |

Google adds one more hurdle for new personal accounts: before you can publish
publicly you must run a **closed test with at least 12 testers for 14 days**.
Plan for that; it is the slowest part of the whole exercise.

## Getting the projects built

```bash
brew install node                      # not installed on this Mac yet
cd two-player-arcade/mobile
npm install
sh build-web.sh
npx cap add ios
npx cap add android
```

Then for each platform:

```bash
npm run ios        # opens Xcode
npm run android    # opens Android Studio
```

Re-run `npm run sync` after any change to the arcade's pages.

In Xcode: pick your team under **Signing & Capabilities**, set the version, then
**Product → Archive → Distribute App**. In Android Studio: **Build → Generate
Signed Bundle** and keep the keystore somewhere safe — losing it means you can
never update the app again.

## What the store listings need

- A **privacy policy at a public URL**. Both stores require one even though the
  arcade collects almost nothing. It should say what the owner dashboard records:
  the name a player types, which game, the result, and when. No accounts, no
  email addresses, no tracking, no advertising.
- **Screenshots** at each store's required sizes. Take them from a simulator.
- A **description**, and Google additionally wants a 1024×500 feature graphic.
- An **age rating questionnaire**. Answer the gambling questions honestly:
  Poker uses play chips only, with nothing bought, won or cashed out. That is
  allowed on both stores, but it will push the rating up (likely 17+ on Apple,
  Mature on Google) and some countries restrict it regardless.

## Three things likely to bite

1. **Apple guideline 4.2, "minimum functionality."** Apple rejects apps that are
   just a website in a wrapper. Bundling the pages helps, but the safest fix is
   to make the app do something a browser tab can't — a share sheet for invites,
   haptics on your turn, and a push notification when your friend joins would
   each strengthen the case. Worth doing before the first submission rather than
   after a rejection.
2. **The free server sleeps.** After about 15 minutes idle, the first request
   takes up to a minute to wake it. In a browser that reads as a slow site; in
   an app it reads as broken, and reviewers may well fail it. Paying for Render's
   always-on tier is effectively a prerequisite for shipping to the stores.
3. **Updates are slow.** The website updates the moment you push. An app update
   waits for review — usually a day or so on Apple, sometimes longer. Anything
   you might want to change quickly should stay server-side.

## The free alternative, already working

The site can be kept on a phone's home screen right now, with its own icon and
no browser chrome, at no cost and with no review:

- **iPhone:** open the site in Safari → Share → *Add to Home Screen*
- **Android:** open in Chrome → menu → *Install app*

That gets most of what an app gives you — an icon, a full-screen window, instant
launch — without the $99 a year, the review queues or the update lag. It is
worth trying that first and seeing whether the stores are still worth it.
