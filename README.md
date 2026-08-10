# 马腾每日简报 - GitHub Actions 版

> 完全免费 · 永久运行 · 电脑关机也能推送

每天北京时间 10:30 自动推送天气、新闻、课表提醒到企业微信。

## 功能

- 🌤️ **天津天气** — 温度、湿度、日出日落、紫外线、穿衣建议
- 📰 **热门新闻** — 5条科技/数码/社会热点，附原文链接
- 📚 **课表提醒** — 根据当前教学周自动判断今天有课没课
- 💬 **企业微信推送** — 直接发到您的企业微信

## 费用

| 项目 | 费用 |
|------|------|
| GitHub Actions | ✅ 免费（私有仓库2000分钟/月，本任务每月约30-60分钟） |
| wttr.in 天气API | ✅ 免费，无需key |
| RSS 新闻源 | ✅ 免费，无需key |
| 企业微信API | ✅ 免费（需自建应用） |
| **总计** | **¥0/月** |

## 部署步骤

### 1. 创建 GitHub 仓库

```bash
# 在本项目目录初始化 git（如果还没有）
git init
git add .
git commit -m "马腾每日简报 - 初始版本"
gh repo create mateng-daily-report --private  # 或去 github.com 手动创建
git push -u origin main
```

### 2. 获取企业微信 API 凭证

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/)
2. **我的企业** → 复制 **企业ID (corpid)**
3. **应用管理** → **自建** → 创建应用（名称随意，如"马腾简报"）
4. 进入应用 → 复制 **AgentId** 和 **Secret**
5. 在应用设置中，将接收人（马腾）加入可见范围

### 3. 配置 GitHub Secrets

在仓库 **Settings → Secrets and variables → Actions → New repository secret** 中添加：

| Secret 名称 | 值 |
|-------------|-----|
| `WECHAT_CORP_ID` | 企业ID |
| `WECHAT_CORP_SECRET` | 应用Secret |
| `WECHAT_AGENT_ID` | 应用AgentId |
| `WECHAT_USER_ID` | 接收人userid（默认 MaTeng） |

### 4. 验证

- 去仓库 **Actions** 标签页
- 点击 **马腾每日简报** → **Run workflow** 手动触发测试
- 查看日志确认消息发送成功

## 文件说明

```
daily_report.py              # 主脚本
.github/workflows/daily-report.yml  # 定时任务配置
course_schedule.json        # 课表数据（2026-2027第一学期）
requirements.txt            # Python依赖
```

## 自定义

- **修改推送时间**：编辑 `.github/workflows/daily-report.yml` 中的 cron
  - 北京时间 10:30 = UTC `30 2 * * *`
  - 北京时间 8:00 = UTC `0 0 * * *`
  - 换算公式：UTC = 北京时间 - 8小时

- **修改新闻源**：编辑 `daily_report.py` 中的 `rss_feeds` 列表

- **修改学期开始日期**：编辑 `daily_report.py` 中的 `SEM_START_DATE`

- **修改城市**：编辑 `daily_report.py` 中的 `CITY`（wttr.in支持的城市名）

## 常见问题

**Q: 企业微信收不到消息？**
- 检查 Secret 是否正确
- 确认接收人(userid)在应用可见范围内
- 查看 Actions 运行日志的报错信息

**Q: 天气显示英文？**
- wttr.in 偶尔会 fallback 到英文，脚本已设置 `lang=zh`，一般正常

**Q: 新闻获取失败？**
- RSS源可能被墙或不稳定，脚本会自动跳过失败的源
- 可自行替换 `rss_feeds` 中的源

**Q: 课表提醒不准？**
- 检查 `SEM_START_DATE` 是否与实际开学日期一致
- 双周课程已自动处理（如电磁场周四双周）
