# MCP Server 入門模板：常見問題與踩雷清單

## 常見坑

- MCP stdio server 不應該把 debug log 印到 stdout，否則會污染 JSON-RPC；debug 請印 stderr。
- 工具 schema 要明確，否則 agent 不知道該傳什麼參數。
- 讀檔、寫檔、呼叫內部 API 都要設安全邊界。
- 不要一開始就接太多工具，先用 echo / now / read_text_file 確認 client-server 流程。
- 不同 client 支援的 MCP 版本與設定檔格式可能不同。

## Debug 順序

1. 先確認服務有沒有啟動。
2. 再確認 endpoint / webhook URL 是否正確。
3. 檢查環境變數是否有載入。
4. 用 echo / fake provider 排除 AI 服務問題。
5. 查看完整錯誤訊息，不要只看最後一行。
6. 把問題縮到最小可重現案例。

## 問別人前準備

- repo / branch
- 啟動指令
- 完整錯誤訊息
- 你已經檢查過哪些設定
- secret 請遮掉，不要直接貼 token
