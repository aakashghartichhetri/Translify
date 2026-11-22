# PR 5 — fix: reliable Flutter authentication, consent, and translation workflows

**Head:** `fix/flutter-user-workflows`  
**Base:** `test/backend-integration`

**Problem / evidence:** Signup called neither `context.pop()` nor navigation after a successful 200, a now-201 gateway response would be interpreted as failure, API failures were printed or surfaced as raw server content, and an unset history preference could be treated as enabled. Speech errors could leave progress indicators stuck.

**Solution / reasoning:** Fix signup/login feedback and 201 support, provide bounded networking and predictable errors, clear stored preferences across logout/expired sessions, make history opt-in explicit, add personal-history deletion, add text translation UI, use temporary speech recordings with cleanup, and simplify responsive home and recording interfaces. Add widget, service and permission-policy tests.

**Tests:** New Flutter test files included. `flutter analyze`, `flutter test`, builds and permission testing on a physical device **not run** in the available environment (Flutter SDK absent).

**Risks / follow-up:** Navigation, microphone/camera prompts, Android permissions, screen-reader semantics, responsive behavior, and iOS startup need real-device validation. Token expiration does not invalidate already-issued JWTs server-side. Verify Flutter version compatibility before merge.
