# 🔒 安全政策

## 报告安全漏洞

我们非常重视项目的安全性。如果你发现了安全漏洞，请通过以下方式报告：

### ⚠️ 请勿在 GitHub Issue 中公开安全漏洞！

请通过以下方式私下联系维护者：

1. **GitHub Security Advisories**（推荐）
   - 前往 https://github.com/Jason-prd/ai-workflow/security/advisories
   - 点击 "Report a vulnerability"
   - 填写详细信息

2. **邮件联系**
   - 在 GitHub Issue 中私信维护者

### 📋 报告信息

请包含以下信息：

- 安全漏洞的类型和描述
- 复现步骤
- 影响的版本范围
- 可能的修复建议（如果有）

### 🕐 响应时间

- 我们会在 **48 小时内** 确认收到报告
- 会在 **7 天内** 提供初步评估
- 修复后会及时通知你

---

## 🔐 安全最佳实践

### 生产环境部署

1. **修改默认密钥**
   ```env
   SECRET_KEY=your-production-secret-key-min-32-chars
   ```

2. **使用 HTTPS**
   确保所有外部访问使用 HTTPS 协议

3. **限制 OpenAI API Key**
   - 不要在客户端暴露 API Key
   - 使用环境变量而非代码中硬编码

4. **飞书配置**
   - 确保 `FEISHU_ENCRYPT_KEY` 已配置
   - 使用 HTTPS 的公网 Webhook URL

5. **定期更新**
   - 关注项目 Release 页面
   - 及时更新到最新版本

### 访问控制

- 生产环境建议配合反向代理（Nginx）进行访问控制
- 使用防火墙限制不必要的端口暴露
- 数据库文件（SQLite）放在安全目录下，不要对外暴露

---

感谢你帮助我们保持项目安全！ 🙏
