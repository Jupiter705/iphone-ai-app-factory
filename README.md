# iPhone AI App Factory V1.0

Windows 上由 Codex 維護原生 SwiftUI App；GitHub Actions 標準 macOS runner 執行 iOS 測試與未簽署 IPA 建置，之後在 Windows 以 Sideloadly 做本機簽署及實機驗收。

目前是初始樣板：公開倉庫與標準 macOS CI 已獲本人授權，首次建置待驗證；尚未產生 IPA、尚未實機驗證。本機不需要 Xcode 或 iOS Simulator。

## 第一個 App

`apps/hello-iphone/project.yml` 是 XcodeGen 專案定義。App 顯示歡迎文字、點擊計數與版本；計數透過 UserDefaults 保存，支援直橫向。Bundle ID 固定為 `com.aifactory.helloiphone.a7e4c921`，顯示名稱 `Factory Hello`，最低 iOS 17.0，初版 1.0.0。

單元測試驗證初值、遞增與跨 store 重新載入。UI 測試驗證首頁、按鈕、重開資料與橫向操作；只有測試程序可使用專用隔離儲存區，不會清除一般 App 資料。

## 雲端流程（尚待實跑）

公開授權與 GitHub 設定完成後，手動執行 `iOS build` workflow。設定為標準 `macos-15`、Xcode 16.4、iOS 18.5 iPhone 16 Simulator；缺少指定版本時會失敗而非靜默換版。CI 記錄實際 image、Xcode、SDK、XcodeGen 版本。

測試通過才 archive 裝置 arm64 App，封裝 `Payload/FactoryHello.app`、生成 manifest 與 SHA-256，保存測試結果及符號。此 IPA 未簽署，仍須 Sideloadly 相容性實測，不能直接視為可安裝。

Windows 的專案專用 gh：`.tools/gh/bin/gh.exe`。以 `scripts/github.ps1` 呼叫，使用忽略的 `local-output/gh-config`；帳號授權由本人在 GitHub 官方瀏覽器頁完成。工具不修改全域 PATH 或 Git 設定。

## 實機與維運

手機先不用接電腦。等 IPA 已測試校驗、Sideloadly／Apple 元件準備好，才安排 USB 首次信任、安裝、啟動及資料保留測試。無人值守安裝、Wi-Fi、免費簽署續期均待獨立驗證。

提出新功能時可說：「將首頁文字改為……，保留原計數資料，完成測試後準備更新。」Codex 必須保留 Bundle ID、追蹤 commit／run／hash；實機啟動與覆蓋資料保留需要本人確認。

Apple 帳密、裝置資料、本地 log、工具、IPA 及原始私人需求不得公開。公開檔案以審閱清單為準。
