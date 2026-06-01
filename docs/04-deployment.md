# MCP Server 入門模板：部署筆記

## 部署前檢查

- 本機流程已經跑通。
- `.env` 沒有被 commit。
- README 的啟動指令與實際程式一致。
- `/health` 或等價檢查 endpoint 可用。
- 外部服務 token 已放在部署平台 secrets。

## 啟動指令

```bash
python client_smoke_test.py
```

## 常見部署選項

- Render / Railway / Fly.io：適合快速 demo。
- VPS + Docker / systemd：適合長期自管。
- 公司內網主機：適合企業內部工具，但要處理網路與權限。
- NAS / edge gateway：適合工業或內部自動化場景。

## 部署後驗證

```bash
python client_smoke_test.py
```

接著再測真正的業務流程，不要只看服務有沒有啟動。

## 實務提醒

部署不是最後一步。正式使用前至少要補：log、錯誤告警、權限控管、備份策略、secret rotation，以及基本監控。
