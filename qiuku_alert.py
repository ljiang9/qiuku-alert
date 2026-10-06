#!/usr/bin/env python3
"""qiuku-alert 秋裤预警穿衣模拟器。

灵感：2026 年 10 月 6 日冷空气南下，"一夜入秋"，全网玩"秋裤预警"梗。
玩家每天为 8 个城市"出差的你"挑选穿搭，7 天后按健康 + 时尚结算称号。
纯娱乐，温度为演示数据，非实况天气预报。
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
import random


# ---------------------------------------------------------------------------
# 演示数据（非实况）：8 个城市 10 月 6-7 日体感温度，按新闻合理虚构
# 武汉南京最低 10-11℃，杭州长沙南昌最高 20℃，"一夜入秋"；北京更冷，
# 广州 28℃纯属"广东人还在穿短袖"彩蛋。
# ---------------------------------------------------------------------------
CITIES: dict[str, float] = {
    "武汉": 11.0,
    "南京": 10.0,
    "杭州": 20.0,
    "长沙": 20.0,
    "南昌": 20.0,
    "重庆": 20.0,
    "北京": 8.0,
    "广州": 28.0,
}
CITY_ORDER = list(CITIES)

# 穿搭 -> (保暖值, 时尚值)
OUTFITS: dict[str, tuple[float, float]] = {
    "短袖": (1.0, 8.0),
    "长袖": (3.0, 6.0),
    "外套": (5.0, 7.0),
    "秋裤": (6.0, 2.0),
    "羽绒服": (9.0, 3.0),
}
OUTFIT_ORDER = list(OUTFITS)

FREEZE_MARGIN = 1.0  # 保暖缺口超过此值 -> 冻成狗
HEAT_MARGIN = 2.0    # 保暖超出需求此值 -> 热成狗
DAYS = 7


class IllegalChoice(ValueError):
    """非法城市或穿搭选择。"""


def demand(temp: float) -> float:
    """体感温度 -> 需要的保暖值。"""
    return max(0.0, (20.0 - temp) / 2.5)


def check_city(city: str) -> str:
    if city not in CITIES:
        raise IllegalChoice(f"没有这个城市：{city}")
    return city


def check_outfit(outfit: str) -> str:
    if outfit not in OUTFITS:
        raise IllegalChoice(f"没有这种穿搭：{outfit}")
    return outfit


def settle(warm: float, temp: float) -> tuple[str, int, int]:
    """单城单日结算。返回 (评语, 健康变化, 时尚变化)。

    判定边界：保暖缺口 > FREEZE_MARGIN 冻；超出 > HEAT_MARGIN 热；
    恰好等于边界值不触发，算"精准命中"。
    """
    gap = demand(temp) - warm
    if gap > FREEZE_MARGIN:
        return ("冻成狗", -2, 0)
    if gap < -HEAT_MARGIN:
        return ("热成狗", 0, -1)
    return ("穿搭王者", 1, 1)


class Game:
    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.day = 0
        self.health = 50
        self.style = 50
        self.qiuku_count = 0
        self.freeze_count = 0

    # -- 一天流程：看预报 -> 选穿搭 -> 揭晓事件 -> 结算 ----------------------

    def start_day(self) -> tuple[int, dict[str, float]]:
        """返回 (天数, 预报体感温度)。穿搭按预报选，事件随后才揭晓。"""
        day_no = self.day + 1
        forecast = {c: round(CITIES[c] + self.rng.uniform(-2.0, 2.0), 1)
                    for c in CITY_ORDER}
        return day_no, forecast

    def draw_event(self) -> tuple[str, str, float]:
        """抽取当日事件，返回 (事件名, 事件城市, 温度变化℃)。"""
        ev_city = self.rng.choice(CITY_ORDER)
        r = self.rng.random()
        if r < 0.30:
            return ("秋裤预警", ev_city, -8.0)
        if r < 0.50:
            return ("回温", ev_city, 6.0)
        if r < 0.70:
            return ("妈妈来电", ev_city, 0.0)
        return ("风平浪静", ev_city, 0.0)

    def finish_day(self, day_no: int, forecast: dict[str, float],
                   event: tuple[str, str, float],
                   picks: dict[str, str]) -> list[str]:
        """先揭晓事件（修正实况温度），再用 picks 结算一天，返回战报行。"""
        ev_name, ev_city, delta = event
        for city in CITY_ORDER:
            if city not in picks:
                raise IllegalChoice(f"第 {day_no} 天缺少城市穿搭：{city}")
            check_city(city)
            check_outfit(picks[city])

        temps = dict(forecast)
        if ev_name in ("秋裤预警", "回温"):
            temps[ev_city] = round(temps[ev_city] + delta, 1)

        report = [f"—— 第 {day_no} 天 ——"]
        if ev_name == "秋裤预警":
            report.append(f"【红色警报】{ev_city}一夜降温 8℃！秋裤预警生效！")
        elif ev_name == "回温":
            report.append(f"{ev_city}倒春寒式回温 +6℃，穿多了会热成狗。")
        elif ev_name == "妈妈来电":
            report.append(f"{ev_city}接到妈妈来电：“多穿点！”——已强制换上秋裤")

        for city in CITY_ORDER:
            outfit = picks[city]
            temp = temps[city]
            forced = ev_name == "妈妈来电" and city == ev_city
            if forced:
                outfit = "秋裤"
                self.health = min(100, self.health + 2)  # 妈妈的爱
            warm, _sty = OUTFITS[outfit]
            verdict, dh, ds = settle(warm, temp)
            self.health = max(0, min(100, self.health + dh))
            self.style = max(0, min(100, self.style + ds))
            note = ""
            if outfit == "秋裤":
                self.qiuku_count += 1
                self.health = min(100, self.health + 1)  # 秋裤护体
                note = "（秋裤护体+1）"
            if verdict == "冻成狗":
                self.freeze_count += 1
            egg = ""
            if city == "广州" and outfit == "短袖" and verdict == "穿搭王者":
                egg = "（广东人还在穿短袖）"
            report.append(f"  {city} {temp:.0f}℃ 穿{outfit} → {verdict}{note}{egg}")

        self.day = day_no
        return report

    # -- AI：按温度贪心选穿搭（保暖最接近需求，持平选时尚高的） ----------

    def ai_pick(self, temps: dict[str, float]) -> dict[str, str]:
        picks = {}
        for city, temp in temps.items():
            need = demand(temp)
            best = min(OUTFIT_ORDER,
                       key=lambda o: (abs(OUTFITS[o][0] - need), -OUTFITS[o][1]))
            picks[city] = best
        return picks

    # -- 终局称号 ---------------------------------------------------------

    def final_title(self) -> tuple[str, str]:
        h, s = self.health, self.style
        if h >= 70 and s >= 60:
            return ("穿搭王者",
                    "冷热拿捏，健康时尚两开花，你就是朋友圈的人间天气博主。")
        if self.qiuku_count >= 20:
            return ("秋裤战神",
                    "秋裤不离身，妈妈最放心。时尚是什么？能当暖气用吗？")
        if s >= 60 and h < 40:
            return ("要风度不要温度",
                    "冻得哆嗦也要保持微笑，时尚圈有你一席之地，暖气片没有。")
        if self.freeze_count >= 12 or h < 30:
            return ("老寒腿预备役",
                    "年轻人，膝盖是自己的，秋裤是妈妈的爱——穿上吧，不丢人。")
        return ("平平无奇穿衣人",
                "不功不过，这个秋天你安然路过，秋裤在衣柜里为你鼓掌。")


def auto_game(seed: int | None = None, verbose: bool = False) -> dict:
    """跑一局 AI 全自动对局，返回结算摘要。"""
    game = Game(seed)
    for _ in range(DAYS):
        day_no, forecast = game.start_day()
        picks = game.ai_pick(forecast)
        event = game.draw_event()
        report = game.finish_day(day_no, forecast, event, picks)
        if verbose:
            print("\n".join(report))
            print(f"  当前：健康 {game.health} / 时尚 {game.style}\n")
    title, comment = game.final_title()
    return {
        "health": game.health,
        "style": game.style,
        "title": title,
        "comment": comment,
        "qiuku": game.qiuku_count,
        "freeze": game.freeze_count,
    }


def interactive() -> None:
    game = Game()
    print("=== 秋裤预警穿衣模拟器 ===")
    print("冷空气南下！每天为 8 个城市出差的你挑选穿搭，7 天后结算称号。")
    print("可选穿搭：" + " / ".join(
        f"{o}(保暖{OUTFITS[o][0]:.0f},时尚{OUTFITS[o][1]:.0f})"
        for o in OUTFIT_ORDER))
    for _ in range(DAYS):
        day_no, forecast = game.start_day()
        print(f"\n—— 第 {day_no} 天（预报） ——")
        for city in CITY_ORDER:
            print(f"  {city}：{forecast[city]:.0f}℃")
        print("（事件未知：可能一夜降温 8℃，也可能妈妈来电查岗）")
        picks: dict[str, str] = {}
        for city in CITY_ORDER:
            while True:
                try:
                    ans = input(
                        f"{city}（预报{forecast[city]:.0f}℃）穿什么？"
                        f"[{ '/'.join(OUTFIT_ORDER) }] "
                    ).strip()
                except EOFError:
                    print("\n输入结束，退出。")
                    return
                if ans in OUTFITS:
                    picks[city] = ans
                    break
                print(f"没有这种穿搭：{ans}，请重选。")
        event = game.draw_event()
        for line in game.finish_day(day_no, forecast, event, picks):
            print(line)
        print(f"当前：健康 {game.health} / 时尚 {game.style}")
    title, comment = game.final_title()
    print("\n=== 7 天结束 ===")
    print(f"称号：{title}")
    print(f"评语：{comment}")
    print(f"健康 {game.health}，时尚 {game.style}，"
          f"秋裤 {game.qiuku_count} 次，冻成狗 {game.freeze_count} 次")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="秋裤预警穿衣模拟器")
    parser.add_argument("--auto", action="store_true", help="AI 自动演示")
    parser.add_argument("--games", type=int, default=1, help="自动演示局数")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--verbose", action="store_true", help="打印每日战报")
    args = parser.parse_args(argv)

    if args.auto:
        if args.games < 1:
            print("--games 至少为 1", file=sys.stderr)
            return 2
        results = []
        for i in range(args.games):
            seed = None if args.seed is None else args.seed + i
            results.append(auto_game(seed, verbose=args.verbose))
        dist = Counter(r["title"] for r in results)
        print(f"共 {args.games} 局，称号分布：")
        for title, count in dist.most_common():
            print(f"  {title}：{count} 局")
        avg_h = sum(r["health"] for r in results) / len(results)
        avg_s = sum(r["style"] for r in results) / len(results)
        print(f"平均健康 {avg_h:.1f}，平均时尚 {avg_s:.1f}")
        return 0

    if not sys.stdin.isatty():
        print("交互模式需要在终端中运行；非终端请使用 --auto 自动演示。",
              file=sys.stderr)
        return 2
    interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
