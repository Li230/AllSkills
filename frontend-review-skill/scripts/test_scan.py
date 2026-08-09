"""scan.py 单元测试：已知反模式必须命中，干净代码不得误报。"""

from __future__ import annotations

from pathlib import Path


from scan import load_rules, scan_text

RULES = Path(__file__).parent / "rules.json"


def scan_sample(text: str, tech: str = "all") -> list[dict]:
    """对单段文本跑全规则，返回命中的 rule_id 集合。"""
    rules = load_rules(RULES)["rules"]
    return scan_text(text, rules, tech)


def rule_ids(text: str, tech: str = "all") -> set[str]:
    return {f["rule_id"] for f in scan_sample(text, tech)}


# ---- 内存/资源：正例（应命中） ----


def test_r1_timer_uncleaned() -> None:
    assert "R1" in rule_ids(
        "let c = 0;\nsetInterval(() => { c += 1; }, 1000);\n"
    )  # noqa: E501


def test_r2_listener_unremoved() -> None:
    assert "R2" in rule_ids("window.addEventListener('resize', onResize);\n")


def test_r3_websocket_unclosed() -> None:
    assert "R3" in rule_ids("const ws = new WebSocket(url);\n")


def test_r4_objecturl_unrevoked() -> None:
    assert "R4" in rule_ids("const u = URL.createObjectURL(blob);\n")


def test_r5_history_unbounded() -> None:
    assert "R5" in rule_ids("conversationHistory.push({ role, content });\n")


def test_r6_effect_no_cleanup_react() -> None:
    assert "R6" in rule_ids(
        "useEffect(() => {\n  const t = setInterval(tick, 1000);\n}, []);\n",
        "react",  # noqa: E501
    )


def test_r7_fetch_no_abort() -> None:
    assert "R7" in rule_ids("fetch('/api/data').then(r => r.json());\n")


def test_r8_vue_mounted_no_cleanup() -> None:
    assert "R8" in rule_ids(
        "onMounted(() => { window.addEventListener('resize', f); });\n", "vue"
    )


def test_r9_eventbus_no_off() -> None:
    assert "R9" in rule_ids("bus.$on('msg', handler);\n", "vue")


# ---- 安全：正例 ----


def test_s1_vhtml() -> None:
    assert "S1" in rule_ids('<div v-html="userInput"></div>\n', "vue")


def test_s2_dangerously_set_html() -> None:
    assert "S2" in rule_ids(
        "<div dangerouslySetInnerHTML={{ __html: x }} />\n", "react"
    )


def test_s3_inner_html() -> None:
    assert "S3" in rule_ids("el.innerHTML = userInput;\n")


def test_s4_hardcoded_key() -> None:
    assert "S4" in rule_ids(
        'const config = { apiKey: "sk-1234567890abcdef" };\n'
    )  # noqa: E501


def test_s5_eval() -> None:
    assert "S5" in rule_ids("eval(userCode);\n")


# ---- 其他维度：正例 ----


def test_d1_deprecated_api() -> None:
    assert "D1" in rule_ids("componentWillMount() {}\n", "react")


def test_a1_img_no_alt() -> None:
    assert "A1" in rule_ids('<img src="a.png" />\n')


def test_a2_empty_button() -> None:
    assert "A2" in rule_ids("<button></button>\n")


def test_a3_div_clickable() -> None:
    assert "A3" in rule_ids("<div onClick={handle}>x</div>\n", "react")


def test_a4_input_no_label() -> None:
    assert "A4" in rule_ids('<input type="text" />\n')


def test_p2_map_no_key_react() -> None:
    assert "P2" in rule_ids("items.map(item => <li>{item}</li>);\n", "react")


def test_e1_fetch_no_catch() -> None:
    assert "E1" in rule_ids("fetch('/api').then(r => r.json());\n")


def test_e2_empty_catch() -> None:
    assert "E2" in rule_ids("try { x() } catch (e) {}\n")


def test_c1_fixed_width() -> None:
    assert "C1" in rule_ids(".box { width: 300px; }\n")


def test_q1_console_log() -> None:
    assert "Q1" in rule_ids("console.log('debug');\n")


# ---- 负例：干净代码不得误报 ----


def test_clean_timer_with_clear() -> None:
    assert "R1" not in rule_ids(
        "let c = 0;\nconst t = setInterval(() => { c += 1; }, 1000);\nclearInterval(t);\n"  # noqa: E501
    )


def test_clean_listener_with_remove() -> None:
    assert "R2" not in rule_ids(
        "window.addEventListener('resize', f);\nwindow.removeEventListener('resize', f);\n"  # noqa: E501
    )


def test_clean_fetch_with_catch() -> None:
    assert "E1" not in rule_ids(
        "fetch('/api').then(r => r.json()).catch(e => showError(e));\n"
    )


def test_clean_effect_with_cleanup_react() -> None:
    assert "R6" not in rule_ids(
        "useEffect(() => {\n  const t = setInterval(tick, 1000);\n  return () => clearInterval(t);\n}, []);\n",  # noqa: E501
        "react",
    )


def test_clean_vue_with_unmount() -> None:
    assert "R8" not in rule_ids(
        "onMounted(() => { window.addEventListener('resize', f); });\nonUnmounted(() => { window.removeEventListener('resize', f); });\n",  # noqa: E501
        "vue",
    )


def test_img_with_alt() -> None:
    assert "A1" not in rule_ids('<img src="a.png" alt="描述" />\n')


def test_input_with_label() -> None:
    assert "A4" not in rule_ids(
        '<label for="n">名字</label>\n<input id="n" />\n'
    )  # noqa: E501


# ---- 技术栈过滤 ----


def test_tech_filter_vue_rule_not_fired_in_react() -> None:
    # vue 专属规则不应在 react 代码命中
    ids = rule_ids('<div v-html="x"></div>\n', "react")
    assert "S1" not in ids


def test_rules_count() -> None:
    rules = load_rules(RULES)
    assert len(rules["rules"]) >= 25, "规则集应 ≥25 条"
    mem = [r for r in rules["rules"] if r["dimension"] == "memory"]
    assert len(mem) >= 8, "内存/资源维度应 ≥8 条"


# ---- Phase 5 审查修复：回归测试 ----


def test_a3_div_with_role_not_fired() -> None:
    """正确做法：div onClick + role/tabIndex 不应命中 A3。"""
    assert "A3" not in rule_ids(
        '<div onClick={go} role="button" tabIndex={0}>x</div>\n', "react"
    )


def test_c1_maxwidth_not_fired() -> None:
    """响应式正确做法：max-width 不应命中 C1。"""
    assert "C1" not in rule_ids(".box { max-width: 300px; }\n")


def test_r3_comment_cleanup_not_exempt() -> None:
    """注释含 cleanup 不应豁免 WebSocket 未关闭。"""
    assert "R3" in rule_ids("const ws = new WebSocket(u); // cleanup 在这里\n")


def test_s4_form_password_default_not_fired() -> None:
    """表单 password 初始值不应命中硬编码密钥。"""
    assert "S4" not in rule_ids('const form = { password: "12345678" };\n')


def test_js_react_sniffing() -> None:
    """.js 文件含 React 特征（useState）应识别为 react 技术栈。"""
    from scan import detect_tech

    p = Path("/tmp/__sniff_test.js")
    p.write_text("import React, { useState } from 'react';\n", encoding="utf-8")
    assert detect_tech(p) == "react"
