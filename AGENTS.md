# iPhone AI App Factory

Read README.md, the local original requirements if available, and docs/test-evidence.md before continuing. The original requirements remain the local baseline; do not publish them automatically.

- Windows controls development; iOS compilation and Simulator tests run only on standard GitHub macOS runners. Never install macOS, Xcode or an iOS simulator locally.
- User authorized project-local gh, GitHub authorization, local app/tests/CI, the reviewed public repository and standard macOS builds. User subsequently authorized necessary software installations, including Sideloadly and Apple components: announce each batch before installing, report installed names/versions/results, and honor interruption. Necessary reboots are also authorized: save progress and notify the user with an interruption window before restarting; never force-close unsaved work. This does not authorize uninstalling existing software, phone settings, private-file publication or Apple authentication.
- Delay asking for an iPhone USB connection until the tested IPA and Windows installation tools are ready. Group pairing, installation and device acceptance into a short session. No phone is needed for development or cloud tests.
- Never read or print account passwords, OTPs, tokens, signing keys or real device IDs. Keep local-output and .tools out of Git. Use explicit publication allowlists and content review; never blindly stage the whole directory.
- Keep the app Bundle ID stable. Never delete apps/data, reset/upgrade iOS, change Apple Account, or use paid runners/services without authorization.
- Stop on account verification with NEEDS_USER_ACTION. CI repair limit: five rounds. Preserve failure evidence and record NOT_RUN/NOT_TESTED honestly.
- Recheck the current Computer Use skill before claiming Windows GUI availability; an updated plugin may change prior limitations. Sideloadly automation and unsigned IPA compatibility require real testing, not assumptions. Never automate authentication or Windows security dialogs.
- At handoff report SHA, repo/run, build/unit/UI status, IPA/hash, signing/install, device launch, data retention, renewal, cost and next user action. Never equate build or install-tool success with device acceptance.
