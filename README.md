# Super Balance & Tax Simulator (AU)

一个用于澳洲退休金（super）与个人税务情景测算的命令行/库工具。

## 功能
- 个人所得税（2024–25税率）+ Medicare Levy（2%）
- 可选 **Medicare Levy Surcharge (MLS)**（用户自设阈值与费率；可用“有/无私人医保”开关）
- **Negative gearing** 扣除
- **Concessional cap**（默认30,000）逻辑、**SG默认12%**、**carry-forward** 输入
- **Division 293** 判定与额外税
- **Salary sacrifice** 可用额度提示与校验
- **Super 投资期**收益税（15%）与费用率
- 余额投影与CSV导出

## 安装与使用
```bash
python super_tool.py --salary 175000 --negative-gearing 60000 \
  --salary-sacrifice 8400 --sg-rate 0.12 --cap 30000 --carry-forward 0 \
  --start-balance 200000 --years 10 --return 0.06 --fees-rate 0.0075 \
  --private-insured --mls-enabled --mls-threshold 90000 --mls-rate 0.01 \
  --csv projection.csv
