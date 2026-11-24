# 编码 → 译码 对接接口说明（encoder.py ↔ decoder.py）

> 面向译码模块（C）负责人。本文件说明 `encoder.py` 输出的数据结构、位置约定和
> 可复用函数，`decoder.py` 按此对接即可，不需要重写分组规则。

## 一、位置与编码约定（两边必须一致）

- 位置编号**从 1 开始**，数组第 0 位不使用。
- 校验位位置：1, 2, 4, 8, …（2 的幂次）。
- 数据位位置：其余位置，原始数据按顺序依次填入。
- 校验方式：**偶校验**，组内 1 的个数为偶数。
- 完整码字 = 海明码（位置 1..n）+ 总校验位 P0（第 n+1 位）。
- 样例：数据 `1011` → 完整码字 `01100110`（P0 在最后一位）。

## 二、encoder.py 对外提供的函数

`decoder.py` 与 `encoder.py` 放在同一 `code` 目录下，直接导入：

```python
from encoder import encode, covered_positions, is_power_of_two, calc_r
```

| 函数 | 作用 |
| --- | --- |
| `encode(data: str)` | 输入二进制串，返回 `EncodedResult` 编码结果 |
| `covered_positions(p, n)` | 返回校验位 `p` 在长度 `n` 内负责的位置分组 |
| `is_power_of_two(p)` | 判断位置是否为校验位位置 |
| `calc_r(k)` | 由数据位数求校验位个数 r |

## 三、EncodedResult 字段说明

`encode(data)` 返回对象，字段如下：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `data` | `str` | 原始数据串 |
| `code` | `list[str]` | 海明码，下标 1..n，`code[0]` 留空 |
| `overall` | `str` | 总校验位 P0（`'0'` / `'1'`） |
| `k` | `int` | 数据位数 |
| `r` | `int` | 校验位数 |
| `n` | `int` | 海明码长度（不含 P0） |
| `parity_positions` | `list[int]` | 校验位位置，如 `[1, 2, 4]` |
| `data_positions` | `list[int]` | 数据位位置，按原始数据顺序 |
| `groups` | `dict[int, list[int]]` | 每个校验位覆盖的位置分组 |
| `parity_values` | `dict[int, str]` | 各校验位编码时算出的值 |

便捷方法：

```python
result.full_codeword()   # 完整码字列表：code[1..n] + [overall]
```

### 样例数据（1011）

```python
result = encode("1011")
# result.k = 4, result.r = 3, result.n = 7
# result.parity_positions = [1, 2, 4]
# result.data_positions   = [3, 5, 6, 7]
# result.code = ["", "0", "1", "1", "0", "0", "1", "1"]
# result.overall = "0"
# result.full_codeword() = ['0','1','1','0','0','1','1','0']
```

位置对照表：

| 位置 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8(P0) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 标注 | P1 | P2 | D1 | P3 | D2 | D3 | D4 | P0 |
| 取值 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 |

## 四、译码模块需要做的事

### 1. 由码字反推布局

如果译码输入的是完整码字字符串（含 P0），可先推导：

```python
m = len(codeword)          # 完整码字长度
n = m - 1                  # 去掉 P0 后的海明码长度
r = sum(1 for p in range(1, n + 1) if is_power_of_two(p))
k = n - r
```

再用 `groups = {p: covered_positions(p, n) for p in parity_positions}` 得到分组。

### 2. 计算校正子

对每个校验组 `p`：统计组内 1 的个数，奇偶为 `S_p`；
若 `S_p = 1`，把 `p` 累加到出错位置号 `pos`：

```python
pos = 0
for p in parity_positions:
    ones = sum(code[j] == "1" for j in groups[p])
    if ones % 2:
        pos += p
```

### 3. 总校验 S0

统计全体 `n` 位 + P0 中 1 的个数，取奇偶得到 `S0`。

### 4. 判定与纠错

| 条件 | 结论 | 处理 |
| --- | --- | --- |
| `pos == 0` 且 `S0 == 0` | 无错误 | 直接提取数据 |
| `pos != 0` 且 `S0 != 0` | 1 位错误，位置 = `pos` | 翻转第 `pos` 位后提取数据 |
| `pos != 0` 且 `S0 == 0` | 2 位错误，只能检测 | 报警，不可纠正，需重传 |
| `pos == 0` 且 `S0 == 1` | 错误在 P0 上 | 翻转 P0，数据本身无误 |

### 5. 还原数据

按 `data_positions` 的顺序取出对应位，即为还原出的原始数据：

```python
recovered = "".join(code[pos] for pos in result.data_positions)
```

## 五、对接注意事项

1. 两边都用**偶校验**，不要一边偶校验一边奇校验。
2. 位置一律 1 编号；译码数组下标与编码保持一致。
3. P0 只参与总校验 `S0`，**不参与**各 `S_p` 分组。
4. 若界面层直接把 `EncodedResult` 传给译码，可复用 `groups`、`data_positions`，无需重新推导。
5. 已知局限：只能纠正 1 位错误、检测 2 位错误；3 位及以上错误不在演示范围内。

## 六、建议的 decoder.py 入口

```python
def decode(codeword: list[str]) -> dict:
    """
    输入完整码字（含 P0），返回：
      status: "ok" | "single" | "double" | "p0_error"
      pos:    出错位置（无错为 0）
      data:   纠错后还原出的数据串
      code:   纠错后的海明码（下标 1..n）
    """
```
