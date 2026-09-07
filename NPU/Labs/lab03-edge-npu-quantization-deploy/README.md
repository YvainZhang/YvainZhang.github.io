# Lab 03: 端侧 NPU 模型 PTQ 量化与离线包导出

## 实验目标

练习对称 INT8 权重量化与 scale 计算，将随机权重导出为教学用 `.bin` 与 `.json`。这不是完整模型 PTQ，也没有实现任何厂商的离线加载规范，不能直接用于证明 NPU 部署成功。

## 产物和验收边界

`export_npu_package.py` 导出权重 shape、scale 和字节数据；它不含计算图、目标指令、layout 契约、目标架构标识或 runtime 版本。脚本在当前目录写入固定文件名，重复运行会覆盖同名教学产物，应在独立临时目录运行。

真实部署还需代表性校准集、逐层误差分析、模型业务指标、目标编译器、算子覆盖/fallback 报告和实卡对拍。参见 [量化 GEMM 验证层次](../../Case-Studies/04-quantized-gemm-contract.md)。
