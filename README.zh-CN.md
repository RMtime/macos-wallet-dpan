# macos-wallet-dpan

**解决 macOS Apple Pay 的银行验证死循环：银行要求设备账户号码（DPAN）后四位，但 Wallet 在完成验证前不显示该号码。**

> **实验性工具。** 仅当 DPAN 尾号已存在于当前 Mac 可访问的 Wallet 本地元数据时，才有机会读取。工具不能激活卡片、生成令牌或绕过银行验证，也不能保证适用于所有待验证卡片。

## 原理

部分银行电话验证要求 Apple Pay 的设备账户号码后四位。macOS 可能要求先完成银行验证，才允许查看该号码。工具以只读方式检查 `~/Library/Passes/passes23.sqlite`，使用 `pass.pid = payment_application.pass_pid` 关联支付应用，再提取已存储的 `dpan_suffix`。

**DPAN 尾号与银行原始卡号（FPAN）尾号不同。**

## 环境

- macOS；你的 Mac 已添加过 Apple Pay 卡片
- Python 3.9 或更新版本；无需安装第三方依赖
- 本机 Wallet 数据库可读取；不同 macOS 版本的内部结构可能变化

## 使用

下载本仓库的 `wallet_dpan.py`，打开终端：

```bash
python3 wallet_dpan.py --list
python3 wallet_dpan.py
```

第一个命令仅列出卡片、尾号是否已存储，**不显示 DPAN 数字**。第二个命令让你选择卡片并确认显示。

如需显式非交互模式：

```bash
python3 wallet_dpan.py --index 1 --reveal
```

请仔细核实卡片选择；原卡号后四位可能重复。

## 安全与限制

- 使用 SQLite 只读模式；不修改数据库、不联网、不上传数据。
- 仅读取尾号字段与卡片标签，不访问完整卡号、动态验证码或 Secure Element 密钥。
- DPAN 后四位可能属于银行核验资料，请勿在公开 Issue、截图或日志里泄露。
- 如果数据库未保存 DPAN，工具无法凭空推算。
- 获取四位数字不代表银行一定接受，也不代表完成 Apple Pay 激活。

更多安全信息见 [SECURITY.md](SECURITY.md)。

独立社区项目，与 Apple 或任何发卡银行无关联。
