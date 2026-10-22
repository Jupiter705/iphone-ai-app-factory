# iPhone AI App Factory V1.0

Windows 上由 Codex 維護原生 SwiftUI App；GitHub Actions 標準 macOS runner 執行 iOS 測試與未簽署 IPA 建置，之後在 Windows 以 Sideloadly 做本機簽署及實機驗收。

首次雲端建置已通過：3 個單元測試與 1 個 UI 測試實際執行成功，已產生並下載校驗裝置用未簽署 IPA。簽署、安裝與實機驗證仍未執行。本機不需要 Xcode 或 iOS Simulator。

## 第一個 App

`apps/hello-iphone/project.yml` 是 XcodeGen 專案定義。App 顯示歡迎文字、點擊計數與版本；計數透過 UserDefaults 保存，支援直橫向。Bundle ID 固定為 `com.aifactory.helloiphone.a7e4c921`，顯示名稱 `Factory Hello`，最低 iOS 17.0，初版 1.0.0。

單元測試驗證初值、遞增與跨 store 重新載入。UI 測試驗證首頁、按鈕、重開資料與橫向操作；只有測試程序可使用專用隔離儲存區，不會清除一般 App 資料。

## 雲端流程

公開授權與 GitHub 設定完成後，手動執行 `iOS build` workflow。設定為標準 `macos-15`、Xcode 16.4、iOS 18.5 iPhone 16 Simulator；缺少指定版本時會失敗而非靜默換版。CI 記錄實際 image、Xcode、SDK、XcodeGen 版本。

測試通過才 archive 裝置 arm64 App，封裝 `Payload/FactoryHello.app`、生成 manifest 與 SHA-256，保存測試結果及符號。此 IPA 未簽署，仍須 Sideloadly 相容性實測，不能直接視為可安裝。

首次成功證據：[run 39760776675](https://github.com/Jupiter705/iphone-ai-app-factory/actions/runs/39760776675)，來源 `bc89451aec78c004ac00ceefd15867dd3f7c11ad`。已驗證組合為 Xcode 16.4 (16F6)、XcodeGen 2.46.0、macos15 image 20260907.0337.1、iPhone 16 iOS 18.5 Simulator。共 4 項測試 PASS，0 failed／skipped；UI 測試包括點擊、重開保存與橫向操作。

產物 `FactoryHello-1.0.0-1-unsigned.ipa`；SHA-256 `c54abb3682e9c09d8eaefad8d76e14e47bbdd58bf8012182e869acd4d36ca4e0`。Windows 端已核對 checksum、來源、Payload、Info.plist、版號與 Mach-O iOS device arm64。首次 workflow 無需修正即成功；尚未進行故意破壞編譯的修復回歸測試。Actions 提示舊 Node 20 action 在 runner 上改以 Node 24 執行，本次已成功；後續更新 actions 時須另做回歸。

Windows 的專案專用 gh：`.tools/gh/bin/gh.exe`。以 `scripts/github.ps1` 呼叫，使用忽略的 `local-output/gh-config`；帳號授權由本人在 GitHub 官方瀏覽器頁完成。工具不修改全域 PATH 或 Git 設定。

為縮短首次手機接線，已預先準備更新驗收版 1.0.1 (build 2)：來源 `aab178cc6a4cdb2d4e5cd351ca255f4553cd6621`、[run 39768880907](https://github.com/Jupiter705/iphone-ai-app-factory/actions/runs/39768880907)。同樣 4 項測試 PASS、0 failed/skipped，裝置 IPA 已下載校驗。檔案 `FactoryHello-1.0.1-2-unsigned.ipa`，SHA-256 `5218026c005f71c38121aadeb6aba87d4ed98c975bdbdbd8ed3a41615b32f715`。這版只改副標題與版號，保留 Bundle ID 和儲存 key，實機覆蓋與資料保留仍待驗證。

本地工作區、來源、產物與安裝包使用 D 槽。可選安裝位置的軟體優先 D 槽；Windows 管理的驅動、Apple 共用元件與 Installer cache 維持官方支援位置，不用直接搬資料夾或 junction 取代正式安裝。

## 實機與維運

手機先不用接電腦。等 IPA 已測試校驗、Sideloadly／Apple 元件準備好，才安排 USB 首次信任、安裝、啟動及資料保留測試。無人值守安裝、Wi-Fi、免費簽署續期均待獨立驗證。

提出新功能時可說：「將首頁文字改為……，保留原計數資料，完成測試後準備更新。」Codex 必須保留 Bundle ID、追蹤 commit／run／hash；實機啟動與覆蓋資料保留需要本人確認。

Apple 帳密、裝置資料、本地 log、工具、IPA 及原始私人需求不得公開。公開檔案以審閱清單為準。
