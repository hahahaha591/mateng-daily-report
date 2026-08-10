#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
马腾每日简报 - GitHub Actions 版
功能：获取天津天气 + 热门新闻 + 课表提醒，通过企业微信API推送
完全免费、零依赖（仅用标准库 + requests）
"""

import json
import os
import sys
import html
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests")
    sys.exit(1)


# ========== 配置 ==========
CITY = "Tianjin"  # 天气城市（天津）

# 企业微信群机器人 Webhook URL（从 GitHub Secrets 读取）
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# 课程表JSON路径
SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "course_schedule.json")

# 学期开始日期（2026-2027第一学期，约9月1日开学，第1周）
# 如有变动请修改此日期
SEM_START_DATE = datetime(2026, 9, 1)

WEEKDAY_MAP = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# 天气代码 → 中文描述映射（wttr.in weatherCode）
WEATHER_CODE_MAP = {
    "113": "晴",
    "116": "多云",
    "119": "阴",
    "122": "阴",
    "143": "有雾",
    "176": "阵雨",
    "179": "有雪",
    "182": "雨夹雪",
    "185": "雨夹雪",
    "200": "雷阵雨",
    "227": "下雪",
    "230": "暴风雪",
    "248": "有雾",
    "260": "有雾",
    "263": "小雨",
    "266": "小雨",
    "281": "冻雨",
    "284": "冻雨",
    "293": "阵雨",
    "296": "阵雨",
    "299": "中雨",
    "302": "大雨",
    "305": "中雨",
    "308": "大雨",
    "311": "暴雨",
    "314": "暴雨",
    "317": "雨夹雪",
    "320": "雨夹雪",
    "323": "小雪",
    "326": "小雪",
    "329": "中雪",
    "332": "中雪",
    "335": "大雪",
    "338": "大雪",
    "350": "阵雨",
    "353": "阵雨",
    "356": "阵雨",
    "359": "暴雨",
    "362": "雨夹雪",
    "365": "雨夹雪",
    "368": "雨夹雪",
    "371": "大雪",
    "374": "雨夹雪",
    "377": "雨夹雪",
    "386": "雷阵雨",
    "389": "雷阵雨",
    "392": "雷阵雪",
    "395": "雷阵雪",
}


def get_weather():
    """从 wttr.in 获取天津天气（免费，无需API key）"""
    try:
        url = f"https://wttr.in/{CITY}?format=j1&lang=zh"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        cur = data["current_condition"][0]
        today = data["weather"][0]
        # 固定显示中文城市名（wttr.in 的 nearest_area 可能返回拼音）
        city_name = "天津"

        # 天气描述（用代码映射到中文）
        weather_code = cur["weatherCode"]
        desc = WEATHER_CODE_MAP.get(weather_code, cur["weatherDesc"][0]["value"])

        # 温度
        temp_now = cur["temp_C"]
        temp_min = today["mintempC"]
        temp_max = today["maxtempC"]
        feels = cur["FeelsLikeC"]

        # 湿度
        humidity = cur["humidity"]

        # 日出日落
        sunrise = today["astronomy"][0]["sunrise"]
        sunset = today["astronomy"][0]["sunset"]

        # 紫外线
        uv = today["uvIndex"]

        # 穿衣建议（简单规则）
        temp_max_int = int(temp_max)
        if temp_max_int <= 5:
            cloth = "气温较低，建议穿羽绒服/厚棉服+毛衣，注意保暖。"
        elif temp_max_int <= 15:
            cloth = "早晚偏凉，建议穿厚外套+毛衣，中午可脱外套。"
        elif temp_max_int <= 25:
            cloth = "气温舒适，建议穿薄外套或长袖衬衫。"
        else:
            cloth = "天气较热，建议穿短袖短裤，注意防暑防晒。"

        # 雾/霾提示
        extra = ""
        if "雾" in desc or int(humidity) >= 85:
            extra = "\n  • 🌫️ 湿度较高，可能有雾，出行注意交通安全。"

        return (
            f"📍 {city_name}今日天气\n"
            f"  • ⛅ 天气：{desc}\n"
            f"  • 🌡️ 气温：{temp_min}°C ~ {temp_max}°C（当前{temp_now}°C，体感{feels}°C）\n"
            f"  • 💧 湿度：{humidity}%\n"
            f"  • 🌅 日出：{sunrise} | 日落：{sunset}\n"
            f"  • ☀️ 紫外线指数：{uv}（{'较强' if int(uv) >= 4 else '较弱'}）\n"
            f"👕 穿衣建议：{cloth}{extra}"
        )
    except Exception as e:
        return f"📍 天气获取失败：{e}"


def get_news():
    """从RSS源获取热门新闻（免费，无需API key）"""
    # 科技/综合类RSS源（可自由增减）
    rss_feeds = [
        ("少数派", "https://sspai.com/feed"),
        ("36氪", "https://36kr.com/feed"),
        ("知乎每日精选", "https://www.zhihu.com/rss"),
    ]

    news_list = []
    for name, url in rss_feeds:
        try:
            resp = requests.get(url, timeout=15,
                                headers={"User-Agent": "Mozilla/5.0"})
            # 简单解析RSS（XML）
            content = resp.text
            # 提取 <item> 或 <entry> 块
            import re
            items = re.findall(r"<item>(.*?)</item>", content, re.DOTALL)
            if not items:
                items = re.findall(r"<entry>(.*?)</entry>", content, re.DOTALL)

            for item in items[:3]:  # 每个源取前3条
                title_m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.DOTALL)
                link_m = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", item, re.DOTALL)
                # RSS link也可能是属性形式
                if not link_m:
                    link_m = re.search(r"<link[^>]*href=\"(.*?)\"", item)
                desc_m = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.DOTALL)

                if title_m:
                    title = html.unescape(title_m.group(1).strip())
                    link = link_m.group(1).strip() if link_m else ""
                    desc = ""
                    if desc_m:
                        # 先解码HTML实体，再去除所有HTML标签
                        raw_desc = html.unescape(desc_m.group(1))
                        desc = re.sub(r"<[^>]+>", "", raw_desc).strip()
                        # 去除残留的 > 前缀和多余空白
                        desc = desc.lstrip(">").strip()
                        # 去除"查看全文"等模板文字
                        desc = re.sub(r"查看全文|继续阅读|阅读原文", "", desc).strip()
                        desc = (desc[:60] + "…") if len(desc) > 60 else desc

                    if title and link:
                        news_list.append({
                            "source": name,
                            "title": title,
                            "link": link,
                            "desc": desc
                        })
                        if len(news_list) >= 5:
                            break
            if len(news_list) >= 5:
                break
        except Exception as e:
            print(f"获取 {name} 新闻失败：{e}")
            continue

    if not news_list:
        return "📰 暂无新闻（获取失败）"

    lines = ["📰 热门文章"]
    categories = ["科技", "数码", "AI", "社会", "校园"]
    for i, n in enumerate(news_list[:5], 1):
        cat = categories[(i - 1) % len(categories)]
        lines.append(f"{i}️⃣ 【{cat}】{n['title']}")
        if n["desc"]:
            lines.append(f"  • {n['desc']}")
        lines.append(f"  • 链接：{n['link']}")
        lines.append(f"  • 来源：{n['source']}")

    return "\n".join(lines)


def get_current_week():
    """计算当前教学周（基于学期开始日期）"""
    today = datetime.now()
    days_diff = (today - SEM_START_DATE).days
    if days_diff < 0:
        return 0  # 还没开学
    return days_diff // 7 + 1


def parse_week_range(week_str, current_week):
    """解析周次字符串，判断当前周是否在该范围内
    支持：'1-11周', '2-10周(双周)', '8-9周' 等格式
    """
    import re
    # 提取数字范围
    nums = re.findall(r"(\d+)", week_str)
    if len(nums) < 2:
        return False
    start, end = int(nums[0]), int(nums[1])

    # 双周判断
    is_double = "双" in week_str
    is_single = "单" in week_str

    if current_week < start or current_week > end:
        return False

    if is_double and current_week % 2 != 0:
        return False
    if is_single and current_week % 2 == 0:
        return False

    return True


def get_courses_today():
    """根据今天是星期几和当前教学周，获取今天的课程"""
    try:
        with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
            schedule = json.load(f)
    except Exception as e:
        return f"📚 课表读取失败：{e}"

    today = datetime.now()
    weekday_idx = today.weekday()  # 0=周一
    weekday_name = WEEKDAY_MAP[weekday_idx]
    current_week = get_current_week()

    if current_week == 0:
        return f"📚 今日课程（{weekday_name}）\n  • 尚未开学（第{current_week}周）"

    courses = schedule["课程表"].get(weekday_name, [])

    # 筛选当前周次内的课程
    today_courses = []
    for c in courses:
        if parse_week_range(c.get("周次", ""), current_week):
            today_courses.append(c)

    if not today_courses:
        return f"📚 今日课程（{weekday_name}，第{current_week}周）\n  • 今日无课 🎉"

    lines = [f"📚 今日课程（{weekday_name}，第{current_week}周）"]
    for c in sorted(today_courses, key=lambda x: x["时间"]):
        lines.append(f"  • {c['时间']} {c['课程']} | {c.get('场地', 'N/A')} | {c.get('教师', 'N/A')}")

    return "\n".join(lines)


def send_to_wechat(content):
    """通过企业微信群机器人 Webhook 发送消息"""
    if not WEBHOOK_URL:
        print("❌ 未配置 WEBHOOK_URL")
        return False
    try:
        payload = {
            "msgtype": "text",
            "text": {"content": content}
        }
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        data = resp.json()
        if data.get("errcode") == 0:
            print("✅ 消息发送成功")
            return True
        else:
            print(f"❌ 发送失败：{data}")
            return False
    except Exception as e:
        print(f"❌ 发送异常：{e}")
        return False


def main():
    """主函数"""
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")

    print(f"=== 马腾每日简报生成中 ({date_str}) ===")

    # 1. 天气
    print("获取天气...")
    weather = get_weather()

    # 2. 新闻
    print("获取新闻...")
    news = get_news()

    # 3. 课表
    print("解析课表...")
    courses = get_courses_today()

    # 4. 组装消息
    message = (
        f"🌤️ 早安马腾！{date_str}简报 🐈‍⬛\n\n"
        f"{weather}\n\n"
        f"{news}\n\n"
        f"{courses}\n\n"
        f"📝 提醒\n"
        f"  • 今天天气如上，合理安排出行\n"
        f"  • 记得查看课程安排，按时上课\n\n"
        f"祝你学习顺利！有事随时叫我 🐈‍⬛"
    )

    print("\n" + "=" * 40)
    print(message)
    print("=" * 40)

    # 5. 发送
    if WEBHOOK_URL:
        send_to_wechat(message)
    else:
        print("\n⚠️ 未配置 WEBHOOK_URL，仅打印预览（不发送）")
        print("请在GitHub Secrets中设置 WEBHOOK_URL")


if __name__ == "__main__":
    main()
