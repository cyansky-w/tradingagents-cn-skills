# 环境变量

这份参考专门说明如何像 Tushare skill 一样，先通过环境变量完成配置，再调用 TradingAgentsCN。

## 推荐变量名

- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_USERNAME`
- `TRADINGAGENTS_PASSWORD`
- `TRADINGAGENTS_APP_TOKEN`
- `TRADINGAGENTS_BEARER_TOKEN`

当前推荐的最小配置是：
- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_USERNAME`
- `TRADINGAGENTS_PASSWORD`

如果系统支持免登录 Token，也可以改为：
- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_APP_TOKEN`

或者：
- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_BEARER_TOKEN`

## 读取规则

1. 优先使用用户当前消息里明确提供的配置
2. 其次使用会话中已缓存的有效认证
3. 其次读取环境变量
4. 都没有时，再询问用户

## PowerShell 示例

```powershell
$env:TRADINGAGENTS_BASE_URL = "http://124.222.83.243/api"
$env:TRADINGAGENTS_USERNAME = "admin"
$env:TRADINGAGENTS_PASSWORD = "admin123"
```

如果使用 Token：

```powershell
$env:TRADINGAGENTS_BASE_URL = "http://124.222.83.243/api"
$env:TRADINGAGENTS_BEARER_TOKEN = "your_token"
```

## Bash 示例

```bash
export TRADINGAGENTS_BASE_URL="http://124.222.83.243/api"
export TRADINGAGENTS_USERNAME="admin"
export TRADINGAGENTS_PASSWORD="admin123"
```

如果使用 Token：

```bash
export TRADINGAGENTS_BASE_URL="http://124.222.83.243/api"
export TRADINGAGENTS_BEARER_TOKEN="your_token"
```

## 缺失配置时的最短提示

如果缺少环境变量，优先给用户这种短提示，而不是先去跑主请求：

```powershell
$env:TRADINGAGENTS_BASE_URL = "http://124.222.83.243/api"
$env:TRADINGAGENTS_USERNAME = "admin"
$env:TRADINGAGENTS_PASSWORD = "admin123"
```

## 安全规则

- 不要在对话中完整展示密码或 Token
- 可以提醒用户设置环境变量，但不要替用户泄露敏感值
- 如果认证失败，只报告失败原因，不回显完整凭证
