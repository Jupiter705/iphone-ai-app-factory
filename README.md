# iPhone AI App Factory V1.0

Windows 上由 Codex 維護原生 SwiftUI App；GitHub Actions 標準 macOS runner 執行 iOS 測試與未簽署 IPA 建置，之後在 Windows 做本機簽署及實機驗收。已驗證的安裝路徑為 iLoader 2.4.0；原定 Sideloadly 0.71.1 的 Local/Fake 登入均遇到 -80046，保留失敗紀錄。

首次端到端 MVP 與覆蓋更新已驗證：兩版各 3 個單元測試與 1 個 UI 測試通過；本人確認 1.0.0 可操作且關閉重開保留計數，正確匯入 1.0.1 後版號正確、計數 4 保留。新版關閉重開的獨立確認、自動化選檔及到期續簽仍待驗證。本機不需要 Xcode 或 iOS Simulator。

## 第一個 App

`apps/hello-iphone/project.yml` 是 XcodeGen 專案定義。App 顯示歡迎文字、點擊計數與版本；計數透過 UserDefaults 保存，支援直橫向。Bundle ID 固定為 `com.aifactory.helloiphone.a7e4c921`，顯示名稱 `Factory Hello`，最低 iOS 17.0，初版 1.0.0。

單元測試驗證初值、遞增與跨 store 重新載入。UI 測試驗證首頁、按鈕、重開資料與橫向操作；只有測試程序可使用專用隔離儲存區，不會清除一般 App 資料。

## 雲端流程

公開授權與 GitHub 設定完成後，手動執行 `iOS build` workflow。設定為標準 `macos-15`、Xcode 16.4、iOS 18.5 iPhone 16 Simulator；缺少指定版本時會失敗而非靜默換版。CI 記錄實際 image、Xcode、SDK、XcodeGen 版本。

測試通過才 archive 裝置 arm64 App，封裝 `Payload/FactoryHello.app`、生成 manifest 與 SHA-256，保存測試結果及符號。此 IPA 未簽署；目前已經 iLoader 實測可簽署安裝，不能因此聲稱 Sideloadly 路徑也通過。

首次成功證據：[run 39760776675](https://github.com/Jupiter705/iphone-ai-app-factory/actions/runs/39760776675)，來源 `bc89451aec78c004ac00ceefd15867dd3f7c11ad`。已驗證組合為 Xcode 16.4 (16F6)、XcodeGen 2.46.0、macos15 image 20260907.0337.1、iPhone 16 iOS 18.5 Simulator。共 4 項測試 PASS，0 failed／skipped；UI 測試包括點擊、重開保存與橫向操作。

產物 `FactoryHello-1.0.0-1-unsigned.ipa`；SHA-256 `c54abb3682e9c09d8eaefad8d76e14e47bbdd58bf8012182e869acd4d36ca4e0`。Windows 端已核對 checksum、來源、Payload、Info.plist、版號與 Mach-O iOS device arm64。首次 workflow 無需修正即成功；尚未進行故意破壞編譯的修復回歸測試。Actions 提示舊 Node 20 action 在 runner 上改以 Node 24 執行，本次已成功；後續更新 actions 時須另做回歸。

Windows 的專案專用 gh：`.tools/gh/bin/gh.exe`。以 `scripts/github.ps1` 呼叫，使用忽略的 `local-output/gh-config`；帳號授權由本人在 GitHub 官方瀏覽器頁完成。工具不修改全域 PATH 或 Git 設定。

更新驗收版 1.0.1 (build 2)：來源 `aab178cc6a4cdb2d4e5cd351ca255f4553cd6621`、[run 39768880907](https://github.com/Jupiter705/iphone-ai-app-factory/actions/runs/39768880907)。同樣 4 項測試 PASS、0 failed/skipped，裝置 IPA 已下載校驗。檔案 `FactoryHello-1.0.1-2-unsigned.ipa`，SHA-256 `5218026c005f71c38121aadeb6aba87d4ed98c975bdbdbd8ed3a41615b32f715`。這版只改副標題與版號，保留 Bundle ID 和儲存 key；本人已確認正確版號及覆蓋後原計數 4 保留。

本地工作區、來源、產物與安裝包使用 D 槽。可選安裝位置的軟體優先 D 槽；Windows 管理的驅動、Apple 共用元件與 Installer cache 維持官方支援位置，不用直接搬資料夾或 junction 取代正式安裝。

## 實機與維運

手機只在簽署安裝階段需要短暫接線，開發與雲端測試不用接線。iLoader 的本人登入、Import IPA 選檔、實機驗收已打通；Apple 驗證、手機信任及開發者模式由本人處理。無人值守安裝、Wi-Fi、免費簽署續期均待獨立驗證。不自動撤銷既有憑證、不刪 App。

提出新功能時可說：「將首頁文字改為……，保留原計數資料，完成測試後準備更新。」Codex 必須保留 Bundle ID、追蹤 commit／run／hash；實機啟動與覆蓋資料保留需要本人確認。

Apple 帳密、裝置資料、本地 log、工具、IPA 及原始私人需求不得公開。公開檔案以審閱清單為準。

## Windows 單一入口

使用既有 Python 3.11+ 及專案本機 gh；`FACTORY_PYTHON` 可指定現有 Python，否則沿用 Codex bundled runtime 或 PATH 中的 Python，不會自動安裝工具。

```powershell
# 建立本機需求紀錄。Codex 接著整理規格並修改程式；不將原始需求文字傳給 CI。
.\scripts\factory.ps1 request --text "更新首頁文字，保留計數資料"
# 使用輸出的 request ID；commit 必須為該 ref 的完整 40 字元 SHA。
.\scripts\factory.ps1 build --request-id REQUEST_ID --ref main --commit FULL_SHA --version 1.0.1
# 也可回收指定的既有 run，完全不重新建置。
.\scripts\factory.ps1 fetch --request-id REQUEST_ID --run-id RUN_ID --commit FULL_SHA --version 1.0.1
.\scripts\factory.ps1 prepare-install --request-id REQUEST_ID --open-folder
.\scripts\factory.ps1 status --request-id REQUEST_ID
```

入口以唯一 correlation ID 找到正確 workflow run，核對公開庫、標準 macos-15、commit、run attempt、測試、SHA-256、plist 版本與 iOS device arm64 Mach-O。失敗保留 log／測試紀錄；初次建置後最多修正 5 輪，不會無限重新派送。安裝準備目錄只放一個版本並以版號命名，降低選錯舊 IPA 的機會。

狀態保存在忽略的 `local-output/requests/`；只有驗證通過才能進入 `IPA_READY`。`prepare-install` 產生 `NEEDS_USER_ACTION`，不會假裝已簽署。本人完成實機檢查後，Codex 可用 `record-device` 記錄精確版號、計數及重開結果。此入口不處理 Apple 帳密，也不直接呼叫付費／遠端簽署服務。
