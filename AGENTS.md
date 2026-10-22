# iPhone AI App Factory

Read README.md, the local original requirements if available, and docs/test-evidence.md before continuing. The original requirements remain the local baseline; do not publish them automatically.

- Windows controls development; iOS compilation and Simulator tests run only on standard GitHub macOS runners. Never install macOS, Xcode or an iOS simulator locally.
- User authorized project-local gh installation, interactive GitHub browser authorization, local SwiftUI app/tests/CI preparation, publication of the reviewed template in Jupiter705/iphone-ai-app-factory, and standard macOS cloud builds. Apple component installation/removal, phone settings and publication of other/private files still need separate explicit authorization.
- Delay asking for an iPhone USB connection until the tested IPA and Windows installation tools are ready. Group pairing, installation and device acceptance into a short session. No phone is needed for development or cloud tests.
- Never read or print account passwords, OTPs, tokens, signing keys or real device IDs. Keep local-output and .tools out of Git. Use explicit publication allowlists and content review; never blindly stage the whole directory.
- Keep the app Bundle ID stable. Never delete apps/data, reset/upgrade iOS, change Apple Account, or use paid runners/services without authorization.
- Stop on account verification with NEEDS_USER_ACTION. CI repair limit: five rounds. Preserve failure evidence and record NOT_RUN/NOT_TESTED honestly.
- Windows GUI automation is unavailable in this chat. Sideloadly automation and unsigned IPA compatibility require real testing, not assumptions.
- At handoff report SHA, repo/run, build/unit/UI status, IPA/hash, signing/install, device launch, data retention, renewal, cost and next user action. Never equate build or install-tool success with device acceptance.
