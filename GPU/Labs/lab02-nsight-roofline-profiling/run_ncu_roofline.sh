#!/bin/bash
# 使用 NSight Compute (NCU) 采集 Roofline 指标
ncu --set full --section SpeedOfLight_HierarchicalRooflineChart --export roofline_report ./profile_target
echo "Roofline report generated: roofline_report.ncu-rep"
