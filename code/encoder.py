# -*- coding: utf-8 -*-
"""
encoder.py —— 海明码（SECDED 扩展）编码模块

任务分工：B 编码算法
职责：
  1. 数据位摆放到非 2 的幂次位置；
  2. 按门牌号分组计算各校验位（偶校验）；
  3. 计算 SECDED 总校验位 P0（可区分 1 位错 / 2 位错）。

供 decoder.py 调用的核心接口：
  encode(data: str) -> EncodedResult

位置编号从 1 开始：
  校验位位置：1, 2, 4, 8, ...（2 的幂次）
  数据位位置：其余位置，按原始数据顺序依次填入
"""

from dataclasses import dataclass, field
from typing import Dict, List


# ---------------- 基础工具函数 ----------------

def is_power_of_two(p: int) -> bool:
    """判断 p 是否为 2 的幂次（校验位所在位置）。"""
    return p > 0 and (p & (p - 1)) == 0


def calc_r(k: int) -> int:
    """由数据位数 k 求校验位个数 r，满足 2^r >= r + k + 1。"""
    r = 1
    while (1 << r) < r + k + 1:
        r += 1
    return r


def covered_positions(p: int, n: int) -> List[int]:
    """
    校验位 p 负责的门牌号分组：
    所有位置编号的二进制中，对应位为 1 的位置。
    例如 p=1(001) 覆盖 1,3,5,7,...；p=2(010) 覆盖 2,3,6,7,...
    """
    return [j for j in range(1, n + 1) if j & p]


# ---------------- 编码结果数据结构 ----------------

@dataclass
class EncodedResult:
    data: str                                   # 原始数据串
    code: List[str]                             # 海明码，下标 1..n，code[0] 留空
    overall: str                                # SECDED 总校验位 P0
    k: int                                      # 数据位数
    r: int                                      # 校验位数
    n: int                                      # 海明码长度（不含 P0）
    parity_positions: List[int]                 # 校验位位置
    data_positions: List[int]                   # 数据位位置
    groups: Dict[int, List[int]]                # 每个校验位覆盖的位置分组
    parity_values: Dict[int, str]               # 每个校验位算出的值

    def full_codeword(self) -> List[str]:
        """返回完整码字：海明码 + 总校验位 P0。"""
        return self.code[1:] + [self.overall]


# ---------------- 核心编码函数 ----------------

def encode(data: str) -> EncodedResult:
    """
    输入二进制数据串（如 "1011"），返回编码后的海明码结果。

    异常：
      ValueError：输入为空、含非 0/1 字符、数据位超过 11 位。
    """
    bits = data.strip()

    if not bits:
        raise ValueError("数据为空，请输入由 0、1 组成的二进制串。")
    if any(ch not in "01" for ch in bits):
        raise ValueError("只能输入字符 0 和 1。")

    k = len(bits)
    if k > 11:
        raise ValueError("数据位最多 11 位（对应 15 位海明码）。")

    # 1. 计算校验位个数与总长
    r = calc_r(k)
    n = k + r

    # 下标 0 不使用，位置从 1 开始
    code: List[str] = [""] * (n + 1)

    # 2. 数据位顺序填入非 2 的幂次位置
    data_positions = [p for p in range(1, n + 1) if not is_power_of_two(p)]
    for pos, bit in zip(data_positions, bits):
        code[pos] = bit

    parity_positions = [1 << (i - 1) for i in range(1, r + 1)]
    groups: Dict[int, List[int]] = {p: covered_positions(p, n)
                                   for p in parity_positions}
    parity_values: Dict[int, str] = {}

    # 3. 逐组计算校验位（偶校验：组内 1 的个数凑成偶数）
    for p in parity_positions:
        others = [j for j in groups[p] if j != p]      # 本组除自身外的位置
        ones = sum(code[j] == "1" for j in others)
        parity_values[p] = "1" if ones % 2 else "0"
        code[p] = parity_values[p]

    # 4. SECDED 总校验位 P0：使全部 n 位中 1 的个数为偶数
    ones_all = sum(code[j] == "1" for j in range(1, n + 1))
    overall = "1" if ones_all % 2 else "0"

    return EncodedResult(
        data=bits,
        code=code,
        overall=overall,
        k=k,
        r=r,
        n=n,
        parity_positions=parity_positions,
        data_positions=data_positions,
        groups=groups,
        parity_values=parity_values,
    )


# ---------------- 演示 / 自测输出 ----------------

def _print_result(result: EncodedResult) -> None:
    """按步骤打印编码过程，方便演示与截图。"""
    line = "=" * 60
    print(line)
    print(f"【编码】原始数据：{result.data}（共 {result.k} 位）")
    print(f"  校验位个数 r：2^r >= r+k+1 → r={result.r}，海明码总长 n={result.n}")
    print(f"  校验位位置：{result.parity_positions}")
    print()

    print("【分组计算校验位（偶校验）】")
    for p in result.parity_positions:
        others = [j for j in result.groups[p] if j != p]
        ones = sum(result.code[j] == "1" for j in others)
        print(f"  P{p}（第 {p} 位）负责位置：{result.groups[p]}")
        print(f"      组内其余位 1 的个数 = {ones}，故 P{p} = {result.parity_values[p]}")

    print()
    ones_all = sum(result.code[j] == "1" for j in range(1, result.n + 1))
    print(f"  总校验位 P0（第 {result.n + 1} 位）= {result.overall}"
          f"（前 {result.n} 位中 1 的个数 = {ones_all}，补 P0 后为偶数）")

    print(line)
    print("【生成的海明码】")
    print("  位置 : " + " ".join(f"{p:2d}" for p in range(1, result.n + 1))
          + f" {result.n + 1}")
    print("  内容 : " + " ".join(f"{result.code[p]:2s}" for p in range(1, result.n + 1))
          + f" {result.overall:2s}")
    labels = ["P" if is_power_of_two(p) else "D"
              for p in range(1, result.n + 1)]
    print("  标注 : " + " ".join(f"{x:2s}" for x in labels) + " P0")
    print()
    print(f"  完整码字（含 P0）：{''.join(result.full_codeword())}")
    print()


if __name__ == "__main__":
    # 自测样例：1011 → 0110011 + P0=0；11 位边界数据
    samples = ["1011", "10101010101"]
    for sample in samples:
        try:
            res = encode(sample)
            _print_result(res)
        except ValueError as e:
            print(f"输入 {sample} 出错：{e}")
