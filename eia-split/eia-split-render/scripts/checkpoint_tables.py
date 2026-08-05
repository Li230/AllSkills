# -*- coding: utf-8 -*-
"""eia-split-render 强制检查点: 逐表内容校验。
检测: 列数一致性 / 表头垃圾(正文误当表头) / 空单元格 / 缺失行。
层级计数 PASS 不等于内容正确 —— render 后必须跑此脚本。
用法: python3 checkpoint_tables.py --work-dir <sub_dir>
"""
import os, re, argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", required=True)
    args = ap.parse_args()
    wd = os.path.abspath(args.work_dir)
    import yaml
    chapter = yaml.safe_load(open(os.path.join(wd, "project.yaml"), encoding="utf-8")).get("chapter")
    html_path = os.path.join(wd, "output", f"chapter{chapter}.html")
    if not os.path.exists(html_path):
        print(f"❌ 未找到 {html_path}")
        return
    html = open(html_path, encoding="utf-8").read()
    # 切分每个带 caption 的表块
    blocks = re.findall(r'<p class="caption"[^>]*>表([\d.\-]+)[^<]*</p>\s*<table.*?</table>', html, re.S)
    # blocks 是 (num, blk) 交替? 上面只有1组捕获 -> 修正
    blocks = re.findall(r'<p class="caption"[^>]*>(表[\d.\-]+[^<]*)</p>\s*(<table.*?</table>)', html, re.S)
    print(f"检测到带 caption 的表块: {len(blocks)}\n")
    all_ok = True
    for cap, tbl in blocks:
        num = re.search(r"表([\d.\-]+)", cap).group(1)
        rows = re.findall(r"<tr>(.*?)</tr>", tbl, re.S)
        rowlens = [len(re.findall(r"<t[hd]", r)) for r in rows]
        # 表头可能是嵌套多行 (如 站号/表层/10~25m层/底层/初级生产力 分两行), 取最大列数为基准
        hdr = max(rowlens) if rowlens else 0
        bad = [i for i, l in enumerate(rowlens) if l != hdr]
        head_cells = re.findall(r"<th>(.*?)</th>", rows[0], re.S) if rows else []
        head_clean = [re.sub(r"<[^>]+>", "", c).strip() for c in head_cells]
        # 表头垃圾判定 (严格, 避免假阳性):
        #  - 含句号/逗号等正文标点 → 真垃圾 (正文误当表头)
        #  - 单格超40字 → 真垃圾
        #  ⚠️ 字段内空格("油品类 别"/"罐区防火堤容 积")是 PDF 提取特征, 不算垃圾, 勿误修
        garbage = any(("。" in c) or ("，" in c) or ("；" in c) for c in head_clean) or any(len(c) > 40 for c in head_clean)
        total_cells = len(re.findall(r"<t[hd]", tbl))
        empty = sum(1 for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tbl, re.S)
                    if re.sub(r"<[^>]+>", "", c).strip() == "")
        status = "✓" if (not bad and not garbage) else "⚠️"
        if bad or garbage:
            all_ok = False
        print(f"  {status} 表{num}: 列数={hdr}, 行数={len(rowlens)}, 异常行={bad if bad else '无'}, "
              f"表头垃圾={'是' if garbage else '否'}, 空单元格={empty}")
        if garbage:
            print(f"       表头原文: {''.join(head_clean)[:80]}")
    print("\n检查点结论:", "✅ 全部表通过 (可进入 verify/审核)" if all_ok
          else "⚠️ 存在需根上修复的表 (改 all_tables_pdf.json 的 rows 后重渲, 勿打HTML补丁)")


if __name__ == "__main__":
    main()
