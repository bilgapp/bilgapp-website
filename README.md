# Bilgapp website

A responsive company website for Bilgapp, with a separate, unlisted Multiplying Panda app section. The company homepage describes mobile and web software development. The app section retains its existing icon, Nunito typeface, cream/navy/green palette, actual practice screenshot, install page, and legal documents.

This is a separate repository from the Flutter app. No app files are changed. No runtime JavaScript, tracking scripts, external fonts, cookies, or frontend dependencies are required.

## Build and preview

Requires Python 3.10 or newer.

```sh
python3 scripts/build.py
python3 -m http.server 4187 --directory dist
```

Open <http://localhost:4187>. The generated pages are:

- `/` — Bilgapp software-development company homepage
- `/multiplying-panda/` — app overview and iPhone/Android installation links
- `/multiplying-panda/privacy-policy/` — app and companion-website privacy policy
- `/multiplying-panda/terms/` — app terms & conditions

The company homepage does not link to, mention, or advertise the app section. The app section is omitted from the sitemap and uses `noindex, follow`. It remains directly accessible by URL; this is discoverability control, not authentication.

`dist/` and local screenshots under `artifacts/` are generated and ignored by Git. The source of truth is in `src/`, `assets/`, and `config/site.json`.

## Configure before publishing

Edit `config/site.json`:

| Setting | Purpose |
| --- | --- |
| `appStoreUrl` | Verified `https://apps.apple.com/…` listing URL |
| `googlePlayUrl` | Verified `https://play.google.com/…` listing URL |
| `operatorName` | Public developer or business legal name |
| `operatorAddress` | Public operator postal address |
| `operatorPhone` | Public operator telephone contact |
| `supportEmail` | Public support and privacy email |
| `siteUrl` | Final HTTPS site URL, including a path prefix when applicable |
| `updatedDate` | Policy revision date in ISO format |
| `hostingPrivacy` | Actual hosting provider, log processing, retention, and privacy information |

Missing store links deliberately show **Coming soon** rather than an invented or incorrect store destination. Setting a verified URL turns its card into an ordinary install link, without relying on JavaScript or device detection. Both platforms stay visible on every device.

Until operator details are supplied, app legal pages have an explicit draft notice. The company homepage can be indexed once `siteUrl` is set; all app pages remain unlisted regardless of policy readiness. `python3 scripts/build.py --release` checks that operator contacts, the canonical site URL, and hosting information have been supplied. It does not perform legal review or certify compliance. No publication or remote repository is created automatically.

Before using these pages as official policies, the operator should confirm the text against the release app and actual service configuration. In particular, confirm child-directed-app obligations and any consent requirements; RevenueCat configuration, integrations, retention and deletion handling; store privacy declarations; business contact details; and hosting/email-provider practices. The current draft does not claim COPPA/GDPR certification or that the app processes no data.

## Content basis

The draft was prepared against the app source as reviewed on 27 November 2026:

- Local practice and settings: `lib/game/game_state.dart`, `lib/game/persistence/preferences_game_repository.dart`, and `lib/l10n/language_controller.dart`.
- Purchases: `lib/purchases/panda_purchases.dart`; RevenueCat is initialized on app launch and resumed with anonymous app user IDs. No app account is created.
- Optional local reminders: `lib/game/device_services.dart` and native platform handlers.
- Android backup restrictions: `android/app/src/main/AndroidManifest.xml`.
- The current dependency list does not include advertising or third-party gameplay analytics SDKs. RevenueCat’s purchase-service reporting is disclosed separately.

External primary references checked when drafting:

- [RevenueCat customer identifiers](https://www.revenuecat.com/docs/customers/identifying-customers)
- [RevenueCat Apple App Privacy guidance](https://www.revenuecat.com/docs/platform-resources/apple-platform-resources/apple-app-privacy)
- [RevenueCat privacy policy](https://www.revenuecat.com/privacy-policy)
- [FTC COPPA FAQs](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)
- [Apple standard EULA](https://www.apple.com/legal/internet-services/itunes/dev/stdeula/)

## Hosting

Run the release build, then serve the contents of `dist/` on any static HTTPS host. No server application, database, or API keys are required. Directory-style routes must serve their own `index.html`. Keep `/multiplying-panda/privacy-policy/` and `/multiplying-panda/terms/` public and stable for app-store submissions. The files also work under a subdirectory; internal navigation and assets use relative paths. When publishing under a prefix, include it in `siteUrl`.

The website itself adds no cookies or analytics. A host may still process IP addresses and request logs; document its actual practices in the policy before publication.

## Validation

```sh
python3 scripts/build.py
python3 scripts/check.py
```

The checks verify page structure, internal files/anchors, local asset references, draft behavior, store URL validation, and required publication details. Desktop/mobile screenshots and browser results are kept locally under `artifacts/` when captured.

## Artwork and fonts

The icon, screenshot, and design are supplied from the Multiplying Panda project and remain the property of their respective rights holders. Nunito is bundled under the SIL Open Font License; see `assets/fonts/Nunito-OFL.txt`. Assets are self-hosted and are not loaded from third-party CDNs.
