#!/bin/bash
# 跟踪 Doorbell MMIO 写操作 (需 root 权限)
echo "Tracing GPU MMIO Doorbell Writes via ftrace..."
sudo trace-cmd record -e drm -e pci ./profile_target
