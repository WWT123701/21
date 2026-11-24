# -*- coding: utf-8 -*-
"""
decoder.py —— 海明码译码纠错模块（骨架）

任务分工：C 译码纠错
对接说明：docs/encoder_decoder_interface.md

本文件已搭好整体框架：布局推导、校正子计算、总校验、四分支判定。
标有 TODO(译码) 的位置由译码负责人补全：
  1. 单错翻转对应位；2. P0 翻转；3. 按数据位位置还原原始数据。

译码判定约定（偶校验 + SECDED 总校验位）：
  pos == 0 且 S0 == 0  → 无错误
  pos != 0 且 S0 != 0  → 1 位错误，位置 = pos，可纠正
  pos != 0 且 S0 == 0  → 2 位错误，只能检测、不可纠正
  pos == 0 且 S0 == 1  → 错误发生在 P0 上，数据本身无误
"""

from encoder import covered_positions, is_power_of_two


def decode(codeword: list[str]) -> dict:
    """
    输入完整码字（含 P0），返回译码结果。

    返回字段：
      status: "ok" | "single" | "double" | "p0_error"
      pos:    出错位置（无错为 0）
      data:   纠错后还原出的数据串
      code:   纠错后的海明码（下标 1..n，code[0] 留空）
    """
    # ---------- 1. 由码字长度推导布局 ----------
    m = len(codeword)                       # 完整码字长度（含 P0）
    n = m - 1                              # 去掉 P0 后的海明码长度
    r = sum(1 for p in range(1, n + 1) if is_power_of_two(p))
    k = n - r                              # 数据位数

    # 按 1 编号放回本地数组，code[0] 留空
    code: list[str] = [""] * (n + 1)
    for j in range(1, n + 1):
        code[j] = codeword[j - 1]
    overall = codeword[m - 1]              # 总校验位 P0

    parity_positions = [p for p in range(1, n + 1) if is_power_of_two(p)]
    data_positions = [p for p in range(1, n + 1) if not is_power_of_two(p)]
    groups = {p: covered_positions(p, n) for p in parity_positions}

    # ---------- 2. 计算校正子 S_p ----------
    pos = 0                                # 出错位置号（由各组 S 拼装）
    syndrome: dict[int, int] = {}

    for p in parity_positions:
        ones = sum(code[j] == "1" for j in groups[p])
        s = ones % 2                       # 偶校验：1 的个数为奇数则 S=1
        syndrome[p] = s
        if s:
            pos += p

    # ---------- 3. 计算总校验 S0 ----------
    ones_all = sum(code[j] == "1" for j in range(1, n + 1))
    ones_all += (overall == "1")
    s0 = ones_all % 2

    # ---------- 4. 四分支判定 ----------
    if pos == 0 and s0 == 0:
        status = "ok"                      # 无错误
    elif pos != 0 and s0 != 0:
        status = "single"                  # 1 位错误，可纠正
        # TODO(译码): 翻转第 pos 位完成纠错
        #   code[pos] = "0" if code[pos] == "1" else "1"
    elif pos != 0 and s0 == 0:
        status = "double"                  # 2 位错误，只能检测
    else:
        status = "p0_error"                # 错误在 P0 上
        # TODO(译码): 翻转总校验位 P0
        #   overall = "0" if overall == "1" else "1"

    # ---------- 5. 还原原始数据 ----------
    # TODO(译码): 按 data_positions 的顺序，从 code[p] 取出数据位拼成 data
    data = ""

    return {
        "status": status,
        "pos": pos,
        "data": data,
        "code": code,
        "syndrome": syndrome,
        "s0": s0,
        "overall": overall,
    }


# ---------------- 自测演示（骨架阶段只看判定结果） ----------------

def _flip(bit_list: list[str], index: int) -> list[str]:
    """复制并翻转指定下标（0 起）的一位，模拟传输错误。"""
    new_list = bit_list.copy()
    new_list[index] = "1" if new_list[index] == "0" else "0"
    return new_list


if __name__ == "__main__":
    from encoder import encode

    # 用例 1：无错传输
    codeword1 = encode("1011").full_codeword()
    print("用例 1（无错）：", decode(codeword1))

    # 用例 2：翻转第 5 位（下标 4），应为单错、pos=5
    codeword2 = _flip(codeword1, 4)
    print("用例 2（1 位错）：", decode(codeword2))

    # 用例 3：翻转第 3、5 位（下标 2、4），应为双错
    codeword3 = _flip(_flip(codeword1, 2), 4)
    print("用例 3（2 位错）：", decode(codeword3))
