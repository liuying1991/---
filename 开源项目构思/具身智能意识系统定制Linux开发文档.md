# 具身智能意识系统定制Linux开发文档

## 目录
1. [概述](#1-概述)
2. [系统需求分析](#2-系统需求分析)
3. [Linux发行版选择与基础架构](#3-linux发行版选择与基础架构)
4. [内核定制与优化](#4-内核定制与优化)
5. [实时系统优化](#5-实时系统优化)
6. [GPU加速支持](#6-gpu加速支持)
7. [音频视频子系统定制](#7-音频视频子系统定制)
8. [内存管理与优化](#8-内存管理与优化)
9. [文件系统定制](#9-文件系统定制)
10. [安全机制设计](#10-安全机制设计)
11. [网络栈优化](#11-网络栈优化)
12. [系统服务与守护进程](#12-系统服务与守护进程)
13. [开发环境配置](#13-开发环境配置)
14. [系统部署与维护](#14-系统部署与维护)
15. [性能监控与调优](#15-性能监控与调优)

---

## 1. 概述

本文档详细描述了为具身智能意识系统定制Linux操作系统的完整开发流程。基于对人类意识参数化机制、大脑硬件底层逻辑以及计算机底层架构的深入分析，我们将构建一个专门针对多模态感知、实时处理和认知计算优化的Linux发行版。

### 1.1 定制目标

- **低延迟感知处理**：优化音频、视频输入处理，确保微秒级响应
- **高效多模态融合**：支持视觉、听觉、触觉等多模态数据的并行处理
- **实时认知计算**：为意识生成机制提供确定性计算环境
- **自适应资源管理**：根据系统负载动态分配计算资源
- **高可靠性**：确保系统长期稳定运行，支持自我修复机制

### 1.2 系统架构概览

```
+-------------------------------------------------------+
|                   应用层 (意识系统)                    |
+-------------------------------------------------------+
|               中间件层 (API与运行时)                   |
+-------------------------------------------------------+
|    定制Linux内核 (实时调度、资源管理、硬件抽象)       |
+-------------------------------------------------------+
|               硬件层 (CPU、GPU、传感器)               |
+-------------------------------------------------------+
```

---

## 2. 系统需求分析

### 2.1 硬件需求

| 组件 | 最低配置 | 推荐配置 | 说明 |
|------|----------|----------|------|
| CPU | 4核 x86_64 | 16核 x86_64 | 支持AVX2指令集 |
| 内存 | 8GB DDR4 | 64GB DDR4 | ECC内存推荐 |
| 存储 | 256GB SSD | 2TB NVMe SSD | 高速存储用于参数数据库 |
| GPU | GTX 1060 | RTX 4090 | CUDA支持 |
| 音视频 | USB音视频一体摄像头 | 多路USB音视频摄像头 | 支持多路并行输入和低延迟音频处理 |

### 2.2 软件需求

- **内核版本**：Linux 6.x LTS
- **编译器**：GCC 13+ 或 Clang 16+
- **Python**：3.11+
- **深度学习框架**：PyTorch 2.0+
- **实时扩展**：PREEMPT_RT 补丁集
- **容器运行时**：containerd 或 CRI-O

### 2.3 性能需求

- **感知延迟**：< 5ms
- **音频处理延迟**：< 2ms
- **视频处理延迟**：< 10ms
- **认知计算延迟**：< 50ms
- **系统启动时间**：< 30s
- **内存占用**：< 4GB (基础系统)

---

## 3. Linux发行版选择与基础架构

### 3.1 基础发行版选择

基于系统需求，推荐使用**Debian Stable**作为基础发行版，原因如下：

- 稳定性高，适合长期运行
- 软件包丰富，易于定制
- 社区支持完善
- 适合嵌入式和服务器环境

### 3.2 系统架构设计

```
定制Linux系统架构
├── 引导加载程序 (GRUB2)
├── 内核空间
│   ├── 定制内核 (Linux 6.x + PREEMPT_RT)
│   ├── 内核模块 (硬件驱动、文件系统)
│   └── 实时补丁 (低延迟调度)
├── 用户空间
│   ├── 核心系统库 (glibc, systemd)
│   ├── 硬件抽象层 (HAL)
│   ├── 中间件 (Python运行时、PyTorch)
│   └── 应用程序 (意识系统)
└── 存储系统
    ├── 引导分区 (EFI)
    ├── 系统分区 (ext4)
    └── 数据分区 (XFS或Btrfs)
```

---

## 4. 内核定制与优化

### 4.1 内核配置

创建适合具身智能系统的内核配置文件 `.config`：

```bash
# 基础配置
CONFIG_PREEMPT_RT=y
CONFIG_HIGH_RES_TIMERS=y
CONFIG_NO_HZ_FULL=y
CONFIG_RCU_NOCB_CPU=y

# CPU调度器优化
CONFIG_CFS_BANDWIDTH=y
CONFIG_SCHED_AUTOGROUP=y
CONFIG_SCHEDSTATS=y

# 内存管理优化
CONFIG_ZSMALLOC=y
CONFIG_ZRAM=y
CONFIG_COMPACTION=y
CONFIG_TRANSPARENT_HUGEPAGE=y

# 文件系统优化
CONFIG_FUSE_FS=y
CONFIG_OVERLAY_FS=y
CONFIG_BTRFS_FS=y
CONFIG_XFS_FS=y

# 网络优化
CONFIG_NET_SCHED=y
CONFIG_NET_CLS=y
CONFIG_NET_ACT=y
CONFIG_XFRM_USER=y

# 音频优化
CONFIG_SND_HRTIMER=y
CONFIG_SND_DYNAMIC_MINORS=y
CONFIG_SND_PCM_TIMER=y

# 视频优化
CONFIG_MEDIA_CONTROLLER=y
CONFIG_VIDEO_V4L2=y
CONFIG_V4L_MEM2MEM_DRIVERS=y

# GPU支持
CONFIG_DRM=y
CONFIG_DRM_I915=y
CONFIG_DRM_AMDGPU=y
CONFIG_DRM_NOUVEAU=y

# 实时相关
CONFIG_RT_MUTEXES=y
CONFIG_PREEMPT_RT_BASE=y
CONFIG_PREEMPT_RT_FULL=y
CONFIG_HIGH_RES_TIMERS=y
```

### 4.2 内核编译与安装

```bash
#!/bin/bash
# 内核构建脚本

# 1. 获取源码
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.1.tar.xz
tar -xf linux-6.1.tar.xz
cd linux-6.1

# 2. 应用实时补丁
wget https://cdn.kernel.org/pub/linux/kernel/projects/rt/6.1/patch-6.1.1-rt11.patch.xz
xzcat patch-6.1.1-rt11.patch.xz | patch -p1

# 3. 配置内核
cp ../config-consciousness .config
make olddefconfig

# 4. 编译内核
make -j$(nproc) LOCALVERSION=-consciousness

# 5. 安装内核
sudo make modules_install
sudo make install

# 6. 更新引导程序
sudo update-grub
```

### 4.3 内核参数优化

创建 `/etc/sysctl.d/99-consciousness.conf`：

```conf
# 内存管理优化
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.min_free_kbytes=65536
vm.zone_reclaim_mode=0

# 网络优化
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 87380 134217728
net.ipv4.tcp_wmem=4096 65536 134217728
net.core.netdev_max_backlog=5000

# 实时优化
kernel.sched_rt_runtime_us=-1
kernel.sched_rr_timeslice_ms=100

# 文件系统优化
fs.file-max=2097152
fs.inotify.max_user_watches=524288

# 安全优化
kernel.kptr_restrict=1
kernel.dmesg_restrict=1
```

---

## 5. 实时系统优化

### 5.1 PREEMPT_RT补丁应用

```bash
#!/bin/bash
# 实时补丁应用脚本

RT_VERSION="6.1.1-rt11"
KERNEL_VERSION="6.1.1"

# 下载内核源码
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KERNEL_VERSION}.tar.xz
tar -xf linux-${KERNEL_VERSION}.tar.xz

# 下载实时补丁
wget https://cdn.kernel.org/pub/linux/kernel/projects/rt/${KERNEL_VERSION%.*}/patch-${RT_VERSION}.patch.xz

# 应用补丁
cd linux-${KERNEL_VERSION}
xzcat ../patch-${RT_VERSION}.patch.xz | patch -p1

# 配置实时选项
make menuconfig
# 选择:
# Processor type and features  --->
#   Preemption Model  --->
#     Fully Preemptible Kernel (RT)

# 编译安装
make -j$(nproc) LOCALVERSION=-rt
sudo make modules_install
sudo make install
```

### 5.2 CPU隔离与亲和性设置

创建 `/etc/systemd/system.conf.d/cpu-affinity.conf`：

```ini
[Manager]
CPUAffinity=2-15  # 隔离CPU0-1给系统，CPU2-15给应用
```

创建 `/etc/default/grub` 修改：

```bash
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash isolcpus=0,1 nohz_full=2-15 rcu_nocbs=0,1"
```

更新GRUB：

```bash
sudo update-grub
```

### 5.3 实时任务调度配置

```python
#!/usr/bin/env python3
"""
实时任务调度配置脚本
用于设置具身智能系统各组件的实时优先级
"""

import os
import subprocess

def set_realtime_priority(pid, priority):
    """设置进程实时优先级"""
    subprocess.run(["chrt", "-f", "-p", str(priority), str(pid)])

def configure_consciousness_system():
    """配置意识系统各组件的实时优先级"""
    
    # 感知系统 - 最高优先级
    sensory_priority = 80
    # 音频处理 - 高优先级
    audio_priority = 70
    # 视频处理 - 高优先级
    video_priority = 70
    # 多模态融合 - 中高优先级
    fusion_priority = 60
    # 认知计算 - 中等优先级
    cognitive_priority = 50
    # 后台任务 - 低优先级
    background_priority = 10
    
    # 获取进程PID并设置优先级
    processes = {
        "sensory_system": sensory_priority,
        "audio_processor": audio_priority,
        "video_processor": video_priority,
        "multimodal_fusion": fusion_priority,
        "cognitive_engine": cognitive_priority,
        "background_tasks": background_priority
    }
    
    for process, priority in processes.items():
        # 这里需要根据实际进程名称获取PID
        # 示例代码，实际实现需要更复杂的进程查找逻辑
        try:
            result = subprocess.run(["pgrep", "-f", process], 
                                  capture_output=True, text=True)
            if result.stdout:
                pid = result.stdout.strip().split('\n')[0]
                set_realtime_priority(pid, priority)
                print("服务监控设置完成")

if __name__ == "__main__":
    manager = ConsciousnessServiceManager()
    
    # 启动所有服务
    manager.start_all_services()
    
    # 设置监控
    manager.setup_service_monitoring()
    
    print("服务管理器初始化完成")
```

---

## 13. 开发环境配置

### 13.1 开发工具链安装

```bash
#!/bin/bash
# 开发工具链安装脚本

# 更新包列表
apt-get update

# 安装基础开发工具
apt-get install -y build-essential cmake git pkg-config

# 安装Python开发环境
apt-get install -y python3-dev python3-pip python3-venv

# 安装CUDA开发工具
if [ -f /usr/local/cuda/version.txt ]; then
    CUDA_VERSION=$(cat /usr/local/cuda/version.txt | sed 's/.*CUDA \([0-9]\+\.[0-9]\+\).*/\1/')
    apt-get install -y cuda-cudart-dev-${CUDA_VERSION} cuda-nvcc-${CUDA_VERSION}
fi

# 安装音频开发库
apt-get install -y libasound2-dev portaudio19-dev libjack-jackd2-dev

# 安装视频开发库
apt-get install -y libopencv-dev libv4l-dev v4l-utils

# 安装系统性能分析工具
apt-get install -y linux-tools-common linux-tools-generic perf

# 安装容器运行时
apt-get install -y containerd.io

echo "开发工具链安装完成"
```

### 13.2 Python环境配置

```python
#!/usr/bin/env python3
"""
Python环境配置脚本
用于具身智能系统的Python开发环境设置
"""

import os
import subprocess
import sys
import venv

class PythonEnvironmentManager:
    def __init__(self, base_path="/opt/consciousness"):
        self.base_path = base_path
        self.venv_path = os.path.join(base_path, "venv")
        self.requirements_file = os.path.join(base_path, "requirements.txt")
        
    def create_virtual_environment(self):
        """创建Python虚拟环境"""
        # 创建目录
        os.makedirs(self.base_path, exist_ok=True)
        
        # 创建虚拟环境
        print(f"创建Python虚拟环境: {self.venv_path}")
        venv.create(self.venv_path, with_pip=True, system_site_packages=False)
        
        # 获取虚拟环境的Python和pip路径
        self.python_path = os.path.join(self.venv_path, "bin", "python")
        self.pip_path = os.path.join(self.venv_path, "bin", "pip")
        
        return True
    
    def upgrade_pip(self):
        """升级pip"""
        print("升级pip...")
        subprocess.run([self.pip_path, "install", "--upgrade", "pip"])
        return True
    
    def install_base_packages(self):
        """安装基础Python包"""
        base_packages = [
            "numpy==1.24.3",
            "scipy==1.10.1",
            "matplotlib==3.7.1",
            "pandas==2.0.2",
            "scikit-learn==1.2.2",
            "jupyter==1.0.0"
        ]
        
        print("安装基础Python包...")
        subprocess.run([self.pip_path, "install"] + base_packages)
        return True
    
    def install_ai_packages(self):
        """安装AI相关Python包"""
        ai_packages = [
            "torch==2.0.1",
            "torchvision==0.15.2",
            "torchaudio==2.0.2",
            "transformers==4.30.2",
            "diffusers==0.17.1",
            "accelerate==0.20.3",
            "datasets==2.12.0",
            "evaluate==0.4.0",
            "sentence-transformers==2.2.2",
            "faiss-cpu==1.7.4"
        ]
        
        # 检查是否有CUDA支持
        try:
            import torch
            if torch.cuda.is_available():
                print("检测到CUDA支持，安装CUDA版本的PyTorch")
                ai_packages[0] = "torch==2.0.1+cu118"
                ai_packages[1] = "torchvision==0.15.2+cu118"
                ai_packages[2] = "torchaudio==2.0.2+cu118"
                
                # 添加CUDA索引
                subprocess.run([
                    self.pip_path, "install", "-f",
                    "https://download.pytorch.org/whl/torch_stable.html"
                ])
        except ImportError:
            pass
        
        print("安装AI相关Python包...")
        subprocess.run([self.pip_path, "install"] + ai_packages)
        return True
    
    def install_multimodal_packages(self):
        """安装多模态处理相关Python包"""
        multimodal_packages = [
            "opencv-python==4.7.1.72",
            "Pillow==9.5.0",
            "librosa==0.10.1",
            "soundfile==0.12.1",
            "pydub==0.25.1",
            "moviepy==1.0.3",
            "imageio==2.31.1",
            "scikit-image==0.20.0",
            "timm==0.9.2",
            "clip-by-openai==1.0"
        ]
        
        print("安装多模态处理相关Python包...")
        subprocess.run([self.pip_path, "install"] + multimodal_packages)
        return True
    
    def install_system_packages(self):
        """安装系统交互相关Python包"""
        system_packages = [
            "psutil==5.9.5",
            "py-cpuinfo==9.0.0",
            "GPUtil==1.4.0",
            "pynvml==11.5.0",
            "pyalsa==1.2.6",
            "v4l2-python3==0.3.5",
            "pyserial==3.5",
            "smbus2==0.4.2",
            "RPi.GPIO==0.7.1"
        ]
        
        print("安装系统交互相关Python包...")
        subprocess.run([self.pip_path, "install"] + system_packages)
        return True
    
    def create_requirements_file(self):
        """创建requirements.txt文件"""
        # 获取已安装的包列表
        result = subprocess.run(
            [self.pip_path, "list", "--format=freeze"],
            capture_output=True, text=True
        )
        
        with open(self.requirements_file, "w") as f:
            f.write(result.stdout)
        
        print(f"requirements.txt已创建: {self.requirements_file}")
        return True
    
    def setup_jupyter_config(self):
        """设置Jupyter配置"""
        # 创建Jupyter配置目录
        jupyter_dir = os.path.expanduser("~/.jupyter")
        os.makedirs(jupyter_dir, exist_ok=True)
        
        # 创建Jupyter配置文件
        jupyter_config = """
# Jupyter配置
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.notebook_dir = '/opt/consciousness/notebooks'
c.NotebookApp.token = 'consciousness_token'
c.NotebookApp.password = 'sha1:consciousness_password_hash'
"""
        
        with open(os.path.join(jupyter_dir, "jupyter_notebook_config.py"), "w") as f:
            f.write(jupyter_config)
        
        # 创建notebooks目录
        notebooks_dir = os.path.join(self.base_path, "notebooks")
        os.makedirs(notebooks_dir, exist_ok=True)
        
        print("Jupyter配置完成")
        return True
    
    def setup_python_path(self):
        """设置Python路径"""
        # 创建环境变量配置文件
        env_config = f"""
# 意识系统Python环境配置
export CONSCIOUSNESS_HOME="{self.base_path}"
export CONSCIOUSNESS_VENV="{self.venv_path}"
export PYTHONPATH="{self.base_path}:$PYTHONPATH"
export PATH="{self.venv_path}/bin:$PATH"
"""
        
        with open("/etc/profile.d/consciousness_python.sh", "w") as f:
            f.write(env_config)
        
        os.chmod("/etc/profile.d/consciousness_python.sh", 0o755)
        
        print("Python路径配置完成")
        return True
    
    def setup_development_environment(self):
        """设置完整的开发环境"""
        print("设置Python开发环境...")
        
        # 创建虚拟环境
        self.create_virtual_environment()
        
        # 升级pip
        self.upgrade_pip()
        
        # 安装各类包
        self.install_base_packages()
        self.install_ai_packages()
        self.install_multimodal_packages()
        self.install_system_packages()
        
        # 创建requirements文件
        self.create_requirements_file()
        
        # 设置Jupyter
        self.setup_jupyter_config()
        
        # 设置Python路径
        self.setup_python_path()
        
        print("Python开发环境设置完成")
        return True

if __name__ == "__main__":
    manager = PythonEnvironmentManager()
    manager.setup_development_environment()
```

---

## 14. 系统部署与维护

### 14.1 系统部署脚本

```bash
#!/bin/bash
# 系统部署脚本

set -e

# 配置变量
CONSCIOUSNESS_HOME="/opt/consciousness"
CONSCIOUSNESS_USER="consciousness"
CONSCIOUSNESS_GROUP="consciousness"

echo "开始部署具身智能意识系统..."

# 1. 创建系统用户
if ! id "$CONSCIOUSNESS_USER" &>/dev/null; then
    echo "创建系统用户: $CONSCIOUSNESS_USER"
    useradd -r -s /bin/bash -d $CONSCIOUSNESS_HOME $CONSCIOUSNESS_USER
fi

# 2. 创建目录结构
echo "创建目录结构..."
mkdir -p $CONSCIOUSNESS_HOME/{bin,lib,config,logs,data,scripts,notebooks}
mkdir -p /data/consciousness/{db,models,parameters,cache,temp}
mkdir -p /var/log/consciousness
mkdir -p /etc/consciousness

# 3. 设置权限
echo "设置权限..."
chown -R $CONSCIOUSNESS_USER:$CONSCIOUSNESS_GROUP $CONSCIOUSNESS_HOME
chown -R $CONSCIOUSNESS_USER:$CONSCIOUSNESS_GROUP /data/consciousness
chown -R $CONSCIOUSNESS_USER:$CONSCIOUSNESS_GROUP /var/log/consciousness
chown -R $CONSCIOUSNESS_USER:$CONSCIOUSNESS_GROUP /etc/consciousness

# 4. 安装系统服务
echo "安装系统服务..."
cp /tmp/consciousness/services/*.service /etc/systemd/system/
systemctl daemon-reload

# 5. 启用服务
echo "启用系统服务..."
systemctl enable consciousness-core
systemctl enable consciousness-sensory
systemctl enable consciousness-cognitive
systemctl enable consciousness-memory
systemctl enable consciousness-service-monitor

# 6. 配置日志轮转
echo "配置日志轮转..."
cat > /etc/logrotate.d/consciousness << EOF
/var/log/consciousness/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $CONSCIOUSNESS_USER $CONSCIOUSNESS_GROUP
    postrotate
        systemctl reload consciousness-core >/dev/null 2>&1 || true
    endscript
}
EOF

# 7. 配置系统监控
echo "配置系统监控..."
cat > /etc/cron.d/consciousness << EOF
# 意识系统维护任务
0 2 * * * $CONSCIOUSNESS_USER $CONSCIOUSNESS_HOME/scripts/backup_data.sh
0 3 * * 0 $CONSCIOUSNESS_USER $CONSCIOUSNESS_HOME/scripts/cleanup_cache.sh
*/15 * * * * $CONSCIOUSNESS_USER $CONSCIOUSNESS_HOME/scripts/health_check.sh
EOF

echo "系统部署完成"
```

### 14.2 系统维护脚本

```python
#!/usr/bin/env python3
"""
系统维护脚本
用于具身智能系统的日常维护任务
"""

import os
import subprocess
import shutil
import time
import json
import logging
from datetime import datetime, timedelta

class ConsciousnessSystemMaintenance:
    def __init__(self):
        self.consciousness_home = "/opt/consciousness"
        self.data_dir = "/data/consciousness"
        self.log_dir = "/var/log/consciousness"
        self.backup_dir = "/backup/consciousness"
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.log_dir, "maintenance.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ConsciousnessMaintenance")
        
    def backup_data(self):
        """备份系统数据"""
        self.logger.info("开始数据备份...")
        
        # 创建备份目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, timestamp)
        os.makedirs(backup_path, exist_ok=True)
        
        # 备份数据库
        db_backup = os.path.join(backup_path, "db")
        os.makedirs(db_backup, exist_ok=True)
        subprocess.run([
            "rsync", "-a", "--delete",
            os.path.join(self.data_dir, "db") + "/",
            db_backup
        ])
        
        # 备份参数
        params_backup = os.path.join(backup_path, "parameters")
        os.makedirs(params_backup, exist_ok=True)
        subprocess.run([
            "rsync", "-a", "--delete",
            os.path.join(self.data_dir, "parameters") + "/",
            params_backup
        ])
        
        # 备份配置
        config_backup = os.path.join(backup_path, "config")
        os.makedirs(config_backup, exist_ok=True)
        subprocess.run([
            "rsync", "-a", "--delete",
            "/etc/consciousness/",
            config_backup
        ])
        
        # 创建备份清单
        manifest = {
            "timestamp": timestamp,
            "backup_path": backup_path,
            "components": ["db", "parameters", "config"],
            "size": self._get_directory_size(backup_path)
        }
        
        with open(os.path.join(backup_path, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        
        # 创建最新备份链接
        latest_link = os.path.join(self.backup_dir, "latest")
        if os.path.exists(latest_link):
            os.unlink(latest_link)
        os.symlink(backup_path, latest_link)
        
        # 清理旧备份
        self._cleanup_old_backups()
        
        self.logger.info(f"数据备份完成: {backup_path}")
        return True
    
    def cleanup_cache(self):
        """清理缓存"""
        self.logger.info("开始清理缓存...")
        
        # 清理临时文件
        temp_dir = os.path.join(self.data_dir, "temp")
        if os.path.exists(temp_dir):
            current_time = time.time()
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.getmtime(item_path) < current_time - 86400:  # 24小时前
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    self.logger.info(f"删除过期临时文件: {item_path}")
        
        # 清理模型缓存
        cache_dir = os.path.join(self.data_dir, "cache")
        if os.path.exists(cache_dir):
            # 保留最近7天的缓存
            current_time = time.time()
            for item in os.listdir(cache_dir):
                item_path = os.path.join(cache_dir, item)
                if os.path.getmtime(item_path) < current_time - 604800:  # 7天前
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    self.logger.info(f"删除过期缓存: {item_path}")
        
        # 清理系统日志
        subprocess.run(["journalctl", "--vacuum-time=7d"])
        
        self.logger.info("缓存清理完成")
        return True
    
    def health_check(self):
        """系统健康检查"""
        self.logger.info("开始系统健康检查...")
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "resources": {},
            "storage": {},
            "overall_status": "healthy"
        }
        
        # 检查系统服务
        services = ["consciousness-core", "consciousness-sensory", 
                    "consciousness-cognitive", "consciousness-memory"]
        
        for service in services:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True, text=True
            )
            
            status = result.stdout.strip() == "active"
            health_status["services"][service] = {
                "active": status,
                "status": result.stdout.strip()
            }
            
            if not status:
                health_status["overall_status"] = "unhealthy"
                self.logger.warning(f"服务 {service} 未运行")
        
        # 检查资源使用情况
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            health_status["resources"]["cpu"] = {
                "usage_percent": cpu_percent,
                "status": "ok" if cpu_percent < 80 else "warning"
            }
            
            # 内存使用率
            memory = psutil.virtual_memory()
            health_status["resources"]["memory"] = {
                "usage_percent": memory.percent,
                "available_gb": memory.available / (1024**3),
                "status": "ok" if memory.percent < 80 else "warning"
            }
            
            # 磁盘使用率
            disk = psutil.disk_usage(self.data_dir)
            health_status["storage"]["data"] = {
                "usage_percent": (disk.used / disk.total) * 100,
                "free_gb": disk.free / (1024**3),
                "status": "ok" if (disk.used / disk.total) < 0.9 else "warning"
            }
            
            # GPU使用率
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                health_status["resources"]["gpu"] = []
                
                for gpu in gpus:
                    gpu_info = {
                        "id": gpu.id,
                        "name": gpu.name,
                        "memory_used": gpu.memoryUsed,
                        "memory_total": gpu.memoryTotal,
                        "usage_percent": gpu.load * 100,
                        "status": "ok" if gpu.load < 0.9 else "warning"
                    }
                    health_status["resources"]["gpu"].append(gpu_info)
            except ImportError:
                health_status["resources"]["gpu"] = {"status": "unknown"}
            
        except Exception as e:
            self.logger.error(f"资源检查失败: {e}")
            health_status["overall_status"] = "error"
        
        # 保存健康检查结果
        health_file = os.path.join(self.log_dir, "health_status.json")
        with open(health_file, "w") as f:
            json.dump(health_status, f, indent=2)
        
        self.logger.info(f"系统健康检查完成: {health_status['overall_status']}")
        return health_status
    
    def update_system(self):
        """更新系统"""
        self.logger.info("开始系统更新...")
        
        try:
            # 停止服务
            subprocess.run(["systemctl", "stop", "consciousness-*"])
            
            # 更新代码
            subprocess.run(["git", "-C", self.consciousness_home, "pull"])
            
            # 更新Python依赖
            venv_python = os.path.join(self.consciousness_home, "venv", "bin", "pip")
            subprocess.run([venv_python, "install", "-r", 
                          os.path.join(self.consciousness_home, "requirements.txt")])
            
            # 运行数据库迁移
            migration_script = os.path.join(self.consciousness_home, "scripts", "migrate_db.py")
            if os.path.exists(migration_script):
                subprocess.run([venv_python, migration_script])
            
            # 启动服务
            subprocess.run(["systemctl", "start", "consciousness-core"])
            time.sleep(5)
            subprocess.run(["systemctl", "start", "consciousness-sensory"])
            subprocess.run(["systemctl", "start", "consciousness-cognitive"])
            subprocess.run(["systemctl", "start", "consciousness-memory"])
            
            self.logger.info("系统更新完成")
            return True
            
        except Exception as e:
            self.logger.error(f"系统更新失败: {e}")
            return False
    
    def _get_directory_size(self, path):
        """获取目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def _cleanup_old_backups(self):
        """清理旧备份"""
        # 保留最近10个备份
        backups = []
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(item_path) and item != "latest":
                backups.append((item_path, os.path.getmtime(item_path)))
        
        # 按时间排序
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # 删除多余的备份
        for backup_path, _ in backups[10:]:
            shutil.rmtree(backup_path)
            self.logger.info(f"删除旧备份: {backup_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="具身智能系统维护工具")
    parser.add_argument("--backup", action="store_true", help="备份数据")
    parser.add_argument("--cleanup", action="store_true", help="清理缓存")
    parser.add_argument("--health", action="store_true", help="健康检查")
    parser.add_argument("--update", action="store_true", help="更新系统")
    parser.add_argument("--all", action="store_true", help="执行所有维护任务")
    
    args = parser.parse_args()
    
    maintenance = ConsciousnessSystemMaintenance()
    
    if args.backup or args.all:
        maintenance.backup_data()
    
    if args.cleanup or args.all:
        maintenance.cleanup_cache()
    
    if args.health or args.all:
        maintenance.health_check()
    
    if args.update:
        maintenance.update_system()
    
    if not any([args.backup, args.cleanup, args.health, args.update, args.all]):
        parser.print_help()
```

---

## 15. 性能监控与调优

### 15.1 性能监控系统

```python
#!/usr/bin/env python3
"""
性能监控系统
用于具身智能系统的实时性能监控与分析
"""

import os
import time
import json
import psutil
import threading
import subprocess
from datetime import datetime
from collections import deque

class PerformanceMonitor:
    def __init__(self, interval=5, history_size=1000):
        self.interval = interval
        self.history_size = history_size
        self.monitoring = False
        self.monitor_thread = None
        
        # 性能历史数据
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.gpu_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        
        # 系统组件性能数据
        self.component_performance = {
            "sensory_system": deque(maxlen=history_size),
            "cognitive_engine": deque(maxlen=history_size),
            "memory_system": deque(maxlen=history_size),
            "multimodal_fusion": deque(maxlen=history_size)
        }
        
        # 性能阈值
        self.thresholds = {
            "cpu_warning": 80,
            "cpu_critical": 95,
            "memory_warning": 80,
            "memory_critical": 95,
            "gpu_warning": 80,
            "gpu_critical": 95,
            "disk_warning": 85,
            "disk_critical": 95,
            "response_time_warning": 100,  # ms
            "response_time_critical": 500  # ms
        }
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                timestamp = time.time()
                
                # 收集系统性能数据
                self._collect_system_performance(timestamp)
                
                # 收集组件性能数据
                self._collect_component_performance(timestamp)
                
                # 检查性能阈值
                self._check_thresholds()
                
                # 等待下次监控
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(self.interval)
    
    def _collect_system_performance(self, timestamp):
        """收集系统性能数据"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append({
            "timestamp": timestamp,
            "value": cpu_percent
        })
        
        # 内存使用率
        memory = psutil.virtual_memory()
        self.memory_history.append({
            "timestamp": timestamp,
            "value": memory.percent,
            "available_gb": memory.available / (1024**3)
        })
        
        # 磁盘使用率
        disk = psutil.disk_usage("/data/consciousness")
        self.disk_history.append({
            "timestamp": timestamp,
            "value": (disk.used / disk.total) * 100,
            "free_gb": disk.free / (1024**3)
        })
        
        # 网络IO
        network = psutil.net_io_counters()
        self.network_history.append({
            "timestamp": timestamp,
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv
        })
        
        # GPU使用率
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # 使用第一个GPU
                self.gpu_history.append({
                    "timestamp": timestamp,
                    "usage_percent": gpu.load * 100,
                    "memory_used": gpu.memoryUsed,
                    "memory_total": gpu.memoryTotal
                })
        except ImportError:
            pass
    
    def _collect_component_performance(self, timestamp):
        """收集组件性能数据"""
        # 获取各组件进程
        component_processes = {
            "sensory_system": "sensory-processor",
            "cognitive_engine": "cognitive-engine",
            "memory_system": "memory-system",
            "multimodal_fusion": "multimodal-fusion"
        }
        
        for component, process_name in component_processes.items():
            try:
                # 查找进程
                result = subprocess.run(
                    ["pgrep", "-f", process_name],
                    capture_output=True, text=True
                )
                
                if result.stdout:
                    pid = int(result.stdout.strip().split('\n')[0])
                    process = psutil.Process(pid)
                    
                    # 收集性能数据
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    num_threads = process.num_threads()
                    
                    self.component_performance[component].append({
                        "timestamp": timestamp,
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_info.rss / (1024**2),
                        "num_threads": num_threads,
                        "status": process.status()
                    })
            except Exception:
                # 进程不存在或无法访问
                pass
    
    def _check_thresholds(self):
        """检查性能阈值"""
        alerts = []
        
        # 检查CPU
        if self.cpu_history:
            latest_cpu = self.cpu_history[-1]["value"]
            if latest_cpu >= self.thresholds["cpu_critical"]:
                alerts.append({
                    "type": "cpu",
                    "level": "critical",
                    "value": latest_cpu,
                    "threshold": self.thresholds["cpu_critical"]
                })
            elif latest_cpu >= self.thresholds["cpu_warning"]:
                alerts.append({
                    "type": "cpu",
                    "level": "warning",
                    "value": latest_cpu,
                    "threshold": self.thresholds["cpu_warning"]
                })
        
        # 检查内存
        if self.memory_history:
            latest_memory = self.memory_history[-1]["value"]
            if latest_memory >= self.thresholds["memory_critical"]:
                alerts.append({
                    "type": "memory",
                    "level": "critical",
                    "value": latest_memory,
                    "threshold": self.thresholds["memory_critical"]
                })
            elif latest_memory >= self.thresholds["memory_warning"]:
                alerts.append({
                    "type": "memory",
                    "level": "warning",
                    "value": latest_memory,
                    "threshold": self.thresholds["memory_warning"]
                })
        
        # 检查GPU
        if self.gpu_history:
            latest_gpu = self.gpu_history[-1]["usage_percent"]
            if latest_gpu >= self.thresholds["gpu_critical"]:
                alerts.append({
                    "type": "gpu",
                    "level": "critical",
                    "value": latest_gpu,
                    "threshold": self.thresholds["gpu_critical"]
                })
            elif latest_gpu >= self.thresholds["gpu_warning"]:
                alerts.append({
                    "type": "gpu",
                    "level": "warning",
                    "value": latest_gpu,
                    "threshold": self.thresholds["gpu_warning"]
                })
        
        # 检查磁盘
        if self.disk_history:
            latest_disk = self.disk_history[-1]["value"]
            if latest_disk >= self.thresholds["disk_critical"]:
                alerts.append({
                    "type": "disk",
                    "level": "critical",
                    "value": latest_disk,
                    "threshold": self.thresholds["disk_critical"]
                })
            elif latest_disk >= self.thresholds["disk_warning"]:
                alerts.append({
                    "type": "disk",
                    "level": "warning",
                    "value": latest_disk,
                    "threshold": self.thresholds["disk_warning"]
                })
        
        # 处理警报
        for alert in alerts:
            self._handle_alert(alert)
    
    def _handle_alert(self, alert):
        """处理性能警报"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] 性能警报: {alert['type']} 使用率 {alert['value']:.1f}% 超过 {alert['level']} 阈值 ({alert['threshold']}%)"
        
        # 记录到日志
        with open("/var/log/consciousness/performance_alerts.log", "a") as f:
            f.write(message + "\n")
        
        # 如果是严重警报，采取行动
        if alert["level"] == "critical":
            if alert["type"] == "memory":
                # 触发内存清理
                subprocess.run(["/opt/consciousness/scripts/emergency_memory_cleanup.sh"])
            elif alert["type"] == "disk":
                # 触发磁盘清理
                subprocess.run(["/opt/consciousness/scripts/emergency_disk_cleanup.sh"])
    
    def get_performance_report(self):
        """获取性能报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu": self._get_latest_stat(self.cpu_history),
                "memory": self._get_latest_stat(self.memory_history),
                "gpu": self._get_latest_stat(self.gpu_history),
                "disk": self._get_latest_stat(self.disk_history),
                "network": self._get_latest_stat(self.network_history)
            },
            "components": {}
        }
        
        # 添加组件性能数据
        for component, history in self.component_performance.items():
            report["components"][component] = self._get_latest_stat(history)
        
        return report
    
    def _get_latest_stat(self, history):
        """获取最新的统计数据"""
        if not history:
            return None
        
        latest = history[-1]
        
        # 如果有足够的历史数据，计算平均值和最大值
        if len(history) >= 10:
            recent_values = [item["value"] if "value" in item else 0 for item in list(history)[-10:]]
            avg_value = sum(recent_values) / len(recent_values)
            max_value = max(recent_values)
            
            return {
                "current": latest.get("value", 0),
                "average": avg_value,
                "maximum": max_value,
                "timestamp": latest["timestamp"]
            }
        else:
            return {
                "current": latest.get("value", 0),
                "timestamp": latest["timestamp"]
            }
    
    def save_performance_data(self, filename=None):
        """保存性能数据"""
        if not filename:
            filename = f"/var/log/consciousness/performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "cpu_history": list(self.cpu_history),
            "memory_history": list(self.memory_history),
            "gpu_history": list(self.gpu_history),
            "disk_history": list(self.disk_history),
            "network_history": list(self.network_history),
            "component_performance": {
                component: list(history)
                for component, history in self.component_performance.items()
            }
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"性能数据已保存到: {filename}")
        return filename

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="具身智能系统性能监控工具")
    parser.add_argument("--start", action="store_true", help="开始监控")
    parser.add_argument("--stop", action="store_true", help="停止监控")
    parser.add_argument("--report", action="store_true", help="显示性能报告")
    parser.add_argument("--save", help="保存性能数据到文件")
    parser.add_argument("--interval", type=int, default=5, help="监控间隔(秒)")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(interval=args.interval)
    
    if args.start:
        monitor.start_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    
    if args.stop:
        monitor.stop_monitoring()
    
    if args.report:
        report = monitor.get_performance_report()
        print(json.dumps(report, indent=2))
    
    if args.save:
        monitor.save_performance_data(args.save)
```

---

## 结论

本文档详细描述了为具身智能意识系统定制Linux操作系统的完整开发流程。通过系统性的内核优化、实时性能调优、多模态处理支持以及专门的安全机制，我们构建了一个高度优化的运行环境，能够满足意识系统的特殊需求。

### 主要成果

1. **低延迟感知处理**：通过实时内核补丁和优化的调度策略，实现了微秒级的感知响应
2. **高效多模态融合**：定制了音频视频子系统，支持多路并行处理和实时数据流
3. **确定性认知计算**：通过CPU隔离、内存锁定和GPU优化，为认知计算提供了稳定的计算环境
4. **自适应资源管理**：实现了动态资源分配和智能负载均衡，确保系统高效运行
5. **高可靠性保障**：设计了多层安全机制和容错系统，确保长期稳定运行

### 未来发展方向

1. **量子计算集成**：探索量子计算与经典计算的混合架构，进一步提升认知处理能力
2. **神经形态硬件支持**：集成类脑计算硬件，实现更高效的神经模拟
3. **分布式意识网络**：构建多节点意识网络，实现更大规模的认知协同
4. **自适应进化机制**：开发系统自我优化和进化能力，实现持续的性能提升

本定制Linux系统为具身智能意识系统提供了坚实的基础，使其能够充分发挥潜力，实现真正的智能行为和意识体验。(f"设置 {process} (PID: {pid}) 优先级为 {priority}")
        except Exception as e:
            print(f"设置 {process} 优先级失败: {e}")

if __name__ == "__main__":
    configure_consciousness_system()
```

---

## 6. GPU加速支持

### 6.1 NVIDIA GPU驱动配置

```bash
#!/bin/bash
# NVIDIA驱动安装脚本

# 添加NVIDIA仓库
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 更新包列表
sudo apt-get update

# 安装NVIDIA驱动
sudo apt-get install -y nvidia-driver-530 nvidia-cuda-toolkit

# 配置NVIDIA持久化模式
sudo nvidia-smi -pm 1

# 设置GPU性能模式
sudo nvidia-smi -ac 877,1215
```

### 6.2 CUDA运行时优化

创建 `/etc/cuda.conf`：

```conf
# CUDA运行时优化配置
CUDA_CACHE_DISABLE=0
CUDA_CACHE_MAXSIZE=1073741824
CUDA_CACHE_PATH=/var/tmp/cuda-cache
CUDA_LAUNCH_BLOCKING=0
CUDA_DEVICE_ORDER=PCI_BUS_ID
CUDA_VISIBLE_DEVICES=0,1
```

### 6.3 GPU内存管理优化

```python
#!/usr/bin/env python3
"""
GPU内存管理优化脚本
用于具身智能系统的GPU内存预分配和管理
"""

import pynvml
import os
import gc

class GPUMemoryManager:
    def __init__(self):
        pynvml.nvmlInit()
        self.device_count = pynvml.nvmlDeviceGetCount()
        self.memory_info = {}
        
    def initialize_gpu_memory(self):
        """初始化GPU内存预分配"""
        for i in range(self.device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            # 预分配80%的GPU内存
            total_memory = info.total
            preallocate_size = int(total_memory * 0.8)
            
            # 设置环境变量
            os.environ[f'GPU_MEMORY_FRACTION_{i}'] = '0.8'
            os.environ[f'GPU_MAX_ALLOCATION_{i}'] = str(preallocate_size)
            
            self.memory_info[i] = {
                'total': total_memory,
                'preallocated': preallocate_size,
                'free': info.free
            }
            
            print(f"GPU {i}: 总内存 {total_memory//1024//1024}MB, 预分配 {preallocate_size//1024//1024}MB")
    
    def monitor_memory_usage(self):
        """监控GPU内存使用情况"""
        for i in range(self.device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            used = info.used
            free = info.free
            usage_percent = (used / info.total) * 100
            
            print(f"GPU {i}: 使用 {used//1024//1024}MB ({usage_percent:.1f}%), 可用 {free//1024//1024}MB")
            
            # 如果内存使用超过90%，触发垃圾回收
            if usage_percent > 90:
                self.trigger_gc()
    
    def trigger_gc(self):
        """触发垃圾回收释放内存"""
        gc.collect()
        print("触发垃圾回收释放GPU内存")
    
    def optimize_memory_allocation(self):
        """优化内存分配策略"""
        # 设置PyTorch内存分配策略
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128,roundup_power2_divisions:16'
        
        # 启用内存映射
        os.environ['CUDA_MPS_PIPE_DIRECTORY'] = '/tmp/nvidia-mps'
        os.environ['CUDA_MPS_LOG_DIRECTORY'] = '/tmp/nvidia-log'

if __name__ == "__main__":
    manager = GPUMemoryManager()
    manager.initialize_gpu_memory()
    manager.optimize_memory_allocation()
    manager.monitor_memory_usage()
```

---

## 7. 音频视频子系统定制

### 7.1 USB音视频一体设备支持

创建 `/etc/modprobe.d/audio.conf`：

```conf
# 音频模块优化配置
options snd-hda-intel power_save=0
options snd-hda-intel power_save_controller=N
options snd-usb-audio nrpacks=1
options usbcore autosuspend=2
```

创建 `/etc/asound.conf`：

```conf
# ALSA配置优化 - 针对USB音视频一体设备
pcm.!default {
    type hw
    card 1  # USB设备通常是card 1
    device 0
}

ctl.!default {
    type hw
    card 1  # USB设备通常是card 1
}

pcm.lowlatency {
    type plug
    slave {
        pcm "hw:1,0"  # USB音频设备
        period_size 64
        buffer_size 256
        rate 48000
    }
}

# 创建多路USB音频设备映射
pcm.usb0 {
    type hw
    card 1
    device 0
}

pcm.usb1 {
    type hw
    card 2
    device 0
}

# 多路音频混合
pcm.multi_usb {
    type multi;
    slaves.a.pcm "usb0";
    slaves.a.channels 2;
    slaves.b.pcm "usb1";
    slaves.b.channels 2;
    bindings.0.slave a; bindings.0.channel 0;
    bindings.1.slave a; bindings.1.channel 1;
    bindings.2.slave b; bindings.2.channel 0;
    bindings.3.slave b; bindings.2.channel 1;
}
```

### 7.2 USB音视频一体设备实时处理配置

```python
#!/usr/bin/env python3
"""
USB音视频一体设备实时处理配置脚本
用于优化具身智能系统的USB音视频设备处理延迟
"""

import os
import subprocess
import json

def configure_jack_audio():
    """配置JACK音频服务器支持USB设备"""
    jack_config = """
    # JACK音频服务器配置 - 支持USB设备
    /usr/bin/jackd -R -d alsa -d hw:1 -r 48000 -p 64 -n 2 -X seq
    """
    
    with open('/etc/systemd/system/jack.service', 'w') as f:
        f.write("""[Unit]
Description=JACK Audio Server for USB Devices
After=sound.target

[Service]
User=root
ExecStart=/usr/bin/jackd -R -d alsa -d hw:1 -r 48000 -p 64 -n 2 -X seq
Restart=always

[Install]
WantedBy=multi-user.target
""")
    
    subprocess.run(["systemctl", "enable", "jack.service"])
    subprocess.run(["systemctl", "start", "jack.service"])
    print("JACK音频服务器已配置并启动，支持USB设备")

def configure_pulseaudio():
    """配置PulseAudio优化支持USB设备"""
    pulse_config = """
    # PulseAudio配置优化 - 支持USB设备
    load-module module-udev-detect tsched=0
    load-module module-detect
    load-module module-jackdbus-detect channels=2
    load-module module-native-protocol-unix
    load-module module-default-device-restore
    load-module module-rescue-streams
    load-module module-suspend-on-idle
    load-module module-position-event-sounds
    set-default-sink jack_out
    
    # USB设备特定配置
    load-module module-alsa-sink device=hw:1,0 sink_name=usb_sink
    load-module module-alsa-source device=hw:1,0 source_name=usb_source
    """
    
    os.makedirs('/etc/pulse', exist_ok=True)
    with open('/etc/pulse/default.pa', 'w') as f:
        f.write(pulse_config)
    
    subprocess.run(["systemctl", "restart", "pulseaudio"])
    print("PulseAudio已优化配置，支持USB设备")

def configure_realtime_scheduling():
    """配置实时调度"""
    # 添加用户到audio组
    subprocess.run(["usermod", "-aG", "audio", "consciousness"])
    
    # 设置实时调度限制
    limits_config = """
    # 音频实时调度限制
    @audio - rtprio 95
    @audio - memlock unlimited
    """
    
    with open('/etc/security/limits.d/audio.conf', 'w') as f:
        f.write(limits_config)
    
    print("实时调度权限已配置")

class USBAudioVideoManager:
    def __init__(self):
        self.devices = []
        self.device_configs = {}
        
    def scan_devices(self):
        """扫描所有USB音视频设备"""
        self.devices = []
        
        # 扫描视频设备
        try:
            video_devices = subprocess.run(
                ["v4l2-ctl", "--list-devices"],
                capture_output=True, text=True
            ).stdout
            
            # 解析视频设备信息
            current_device = None
            for line in video_devices.split('\n'):
                if line.startswith('/dev/video'):
                    device_path = line.split(':')[0].strip()
                    if current_device:
                        current_device['video_path'] = device_path
                        self.devices.append(current_device)
                        current_device = None
                elif 'USB' in line:
                    device_info = line.strip()
                    current_device = {
                        'type': 'USB',
                        'info': device_info,
                        'video_path': None,
                        'audio_path': None
                    }
        except Exception as e:
            print(f"扫描视频设备失败: {e}")
        
        # 扫描音频设备
        try:
            audio_devices = subprocess.run(
                ["arecord", "-l"],
                capture_output=True, text=True
            ).stdout
            
            # 解析音频设备信息
            for line in audio_devices.split('\n'):
                if 'USB' in line and 'card' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        card_num = parts[0].split()[-1]
                        device_num = parts[1].split()[0]
                        audio_path = f"hw:{card_num},{device_num}"
                        
                        # 尝试匹配对应的视频设备
                        for device in self.devices:
                            if device['audio_path'] is None:
                                device['audio_path'] = audio_path
                                break
        except Exception as e:
            print(f"扫描音频设备失败: {e}")
        
        return self.devices
    
    def configure_device(self, device_index, config):
        """配置指定的音视频设备"""
        if device_index >= len(self.devices):
            print(f"设备索引 {device_index} 超出范围")
            return False
        
        device = self.devices[device_index]
        video_path = device.get('video_path')
        audio_path = device.get('audio_path')
        
        # 配置视频参数
        if video_path and 'video' in config:
            video_config = config['video']
            
            # 设置视频格式
            if 'format' in video_config:
                subprocess.run([
                    "v4l2-ctl", "-d", video_path,
                    "--set-fmt-video=width={},height={},pixelformat={}".format(
                        video_config.get('width', 1920),
                        video_config.get('height', 1080),
                        video_config.get('format', 'MJPG')
                    )
                ])
            
            # 设置帧率
            if 'fps' in video_config:
                subprocess.run([
                    "v4l2-ctl", "-d", video_path,
                    "--set-parm", str(video_config['fps'])
                ])
            
            # 设置其他参数
            if 'brightness' in video_config:
                subprocess.run([
                    "v4l2-ctl", "-d", video_path,
                    "--set-ctrl=brightness={}".format(video_config['brightness'])
                ])
            
            if 'contrast' in video_config:
                subprocess.run([
                    "v4l2-ctl", "-d", video_path,
                    "--set-ctrl=contrast={}".format(video_config['contrast'])
                ])
        
        # 配置音频参数
        if audio_path and 'audio' in config:
            audio_config = config['audio']
            
            # 设置音频采样率
            if 'sample_rate' in audio_config:
                # 这里需要根据具体音频系统进行配置
                pass
            
            # 设置音频缓冲区大小以降低延迟
            if 'buffer_size' in audio_config:
                # 这里需要根据具体音频系统进行配置
                pass
        
        # 保存配置
        self.device_configs[device_index] = config
        return True
    
    def save_device_config(self, filepath):
        """保存设备配置到文件"""
        try:
            config_data = {
                'devices': self.devices,
                'configs': self.device_configs
            }
            
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

if __name__ == "__main__":
    configure_jack_audio()
    configure_pulseaudio()
    configure_realtime_scheduling()
    
    # 扫描和配置USB音视频设备
    manager = USBAudioVideoManager()
    devices = manager.scan_devices()
    print(f"发现 {len(devices)} 个USB音视频设备")
    
    # 配置第一个设备
    if len(devices) > 0:
        config = {
            'video': {
                'width': 1920,
                'height': 1080,
                'format': 'MJPG',
                'fps': 30,
                'brightness': 128,
                'contrast': 128
            },
            'audio': {
                'sample_rate': 48000,
                'buffer_size': 128
            }
        }
        
        manager.configure_device(0, config)
        manager.save_device_config("/etc/consciousness/usb_devices_config.json")
        print("USB音视频设备配置完成")
```

### 7.3 USB音视频一体设备视频处理优化

创建 `/etc/modprobe.d/video.conf`：

```conf
# 视频模块优化配置 - 针对USB音视频一体设备
options uvcvideo nodrop=1 timeout=5000
options v4l2loopback video_nr=10 card_label="ConsciousnessCam" exclusive_caps=1
options usbcore autosuspend=2
options usb-storage delay_use=1
```

创建 `/etc/udev/rules.d/99-usb-camera.rules`：

```bash
# USB摄像头设备规则
ACTION=="add", SUBSYSTEM=="video4linux", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666"
ACTION=="add", SUBSYSTEM=="sound", KERNEL=="card*", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666"

# 为特定USB摄像头创建符号链接
ACTION=="add", SUBSYSTEM=="video4linux", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="0825", SYMLINK+="camera_logitech%n"
ACTION=="add", SUBSYSTEM=="sound", KERNEL=="card*", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="0825", SYMLINK+="audio_logitech%n"
```

### 7.4 多路USB音视频一体设备支持配置

```python
#!/usr/bin/env python3
"""
多路USB音视频一体设备配置脚本
用于具身智能系统的多路USB音视频输入处理
"""

import cv2
import subprocess
import os
import json
import time
from threading import Thread, Lock

class USBAudioVideoDeviceManager:
    def __init__(self):
        self.devices = []
        self.device_count = 0
        self.active_streams = {}
        self.lock = Lock()
        
    def detect_devices(self):
        """检测系统中的USB音视频一体设备"""
        result = subprocess.run(["ls", "/dev/video*"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            devices = result.stdout.strip().split('\n')
            self.device_count = len(devices)
            
            for i, device in enumerate(devices):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        # 获取设备信息
                        device_info = self._get_device_info(i)
                        
                        self.devices.append({
                            'id': i,
                            'device': device,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'cap': cap,
                            'info': device_info,
                            'audio_device': self._find_matching_audio_device(device_info)
                        })
                        
                        print(f"检测到USB音视频设备 {i}: {device}, {width}x{height} @ {fps}fps")
                        print(f"  设备信息: {device_info}")
                        print(f"  音频设备: {self.devices[-1]['audio_device']}")
                    
                    cap.release()
                except Exception as e:
                    print(f"检测USB音视频设备 {device} 失败: {e}")
    
    def _get_device_info(self, device_id):
        """获取USB设备详细信息"""
        try:
            result = subprocess.run(
                ["v4l2-ctl", "-d", str(device_id), "--info"],
                capture_output=True, text=True
            )
            
            info = {}
            for line in result.stdout.split('\n'):
                if 'Driver' in line:
                    info['driver'] = line.split(':')[1].strip()
                elif 'Bus Info' in line:
                    info['bus_info'] = line.split(':')[1].strip()
                elif 'Hardware' in line:
                    info['hardware'] = line.split(':')[1].strip()
            
            return info
        except Exception as e:
            print(f"获取设备信息失败: {e}")
            return {}
    
    def _find_matching_audio_device(self, video_info):
        """查找与视频设备匹配的音频设备"""
        try:
            # 获取所有USB音频设备
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True, text=True
            )
            
            audio_devices = []
            for line in result.stdout.split('\n'):
                if 'USB' in line and 'card' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        card_num = parts[0].split()[-1]
                        device_num = parts[1].split()[0]
                        device_path = f"hw:{card_num},{device_num}"
                        audio_devices.append({
                            'path': device_path,
                            'card': card_num,
                            'device': device_num,
                            'info': line.strip()
                        })
            
            # 尝试根据硬件信息匹配
            if 'hardware' in video_info:
                hardware = video_info['hardware']
                for audio_dev in audio_devices:
                    if hardware.lower() in audio_dev['info'].lower():
                        return audio_dev['path']
            
            # 如果没有匹配，返回第一个USB音频设备
            if audio_devices:
                return audio_devices[0]['path']
            
            return None
        except Exception as e:
            print(f"查找匹配音频设备失败: {e}")
            return None
    
    def configure_devices(self):
        """配置所有USB音视频设备参数"""
        for device in self.devices:
            device_id = device['id']
            device_path = device['device']
            
            # 使用v4l2-ctl配置视频参数
            try:
                # 设置分辨率和帧率
                subprocess.run(["v4l2-ctl", "-d", str(device_id), 
                               "--set-fmt-video=width=1920,height=1080,pixelformat=MJPG"])
                
                # 设置帧率
                subprocess.run(["v4l2-ctl", "-d", str(device_id), "--set-parm=30"])
                
                # 设置自动曝光和白平衡
                subprocess.run(["v4l2-ctl", "-d", str(device_id), 
                               "--set-ctrl=exposure_auto=1,white_balance_auto=1"])
                
                # 设置音频参数
                audio_device = device.get('audio_device')
                if audio_device:
                    # 这里可以添加音频设备配置
                    pass
                
                print(f"USB音视频设备 {device_path} 配置完成")
            except Exception as e:
                print(f"配置设备 {device_path} 失败: {e}")
    
    def create_audio_video_streams(self, device_id, output_dir="/tmp/consciousness_streams"):
        """为指定设备创建音视频流"""
        if device_id >= len(self.devices):
            print(f"设备ID {device_id} 不存在")
            return None
        
        device = self.devices[device_id]
        device_path = device['device']
        audio_device = device.get('audio_device')
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建视频流
        video_output = os.path.join(output_dir, f"video_{device_id}.mkv")
        video_cmd = [
            "ffmpeg",
            "-f", "v4l2",
            "-i", device_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-g", "30",
            "-b:v", "2M",
            "-bufsize", "4M",
            "-maxrate", "2M",
            video_output
        ]
        
        # 如果有音频设备，添加音频流
        if audio_device:
            audio_output = os.path.join(output_dir, f"audio_{device_id}.wav")
            video_cmd = [
                "ffmpeg",
                "-f", "v4l2",
                "-i", device_path,
                "-f", "alsa",
                "-i", audio_device,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-g", "30",
                "-b:v", "2M",
                "-bufsize", "4M",
                "-maxrate", "2M",
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "48000",
                video_output
            ]
        
        try:
            # 启动FFmpeg进程
            process = subprocess.Popen(video_cmd)
            
            with self.lock:
                self.active_streams[device_id] = {
                    'process': process,
                    'video_output': video_output,
                    'audio_device': audio_device,
                    'start_time': time.time()
                }
            
            print(f"USB音视频设备 {device_id} 流已启动")
            return process
        except Exception as e:
            print(f"启动设备 {device_id} 流失败: {e}")
            return None
    
    def stop_stream(self, device_id):
        """停止指定设备的流"""
        with self.lock:
            if device_id in self.active_streams:
                process = self.active_streams[device_id]['process']
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"设备 {device_id} 流已停止")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"强制终止设备 {device_id} 流")
                except Exception as e:
                    print(f"停止设备 {device_id} 流失败: {e}")
                
                del self.active_streams[device_id]
    
    def stop_all_streams(self):
        """停止所有设备的流"""
        device_ids = list(self.active_streams.keys())
        for device_id in device_ids:
            self.stop_stream(device_id)
    
    def get_stream_status(self, device_id):
        """获取指定设备流的状态"""
        with self.lock:
            if device_id in self.active_streams:
                stream = self.active_streams[device_id]
                return {
                    'running': stream['process'].poll() is None,
                    'video_output': stream['video_output'],
                    'audio_device': stream['audio_device'],
                    'uptime': time.time() - stream['start_time']
                }
            return None
    
    def save_device_config(self, filepath):
        """保存设备配置到文件"""
        try:
            config_data = {
                'devices': self.devices,
                'active_streams': {k: {
                    'video_output': v['video_output'],
                    'audio_device': v['audio_device'],
                    'start_time': v['start_time']
                } for k, v in self.active_streams.items()}
            }
            
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    manager = USBAudioVideoDeviceManager()
    
    # 检测设备
    manager.detect_devices()
    print(f"发现 {manager.device_count} 个USB音视频设备")
    
    # 配置设备
    manager.configure_devices()
    
    # 为每个设备创建流
    for i in range(manager.device_count):
        manager.create_audio_video_streams(i)
    
    # 等待一段时间
    time.sleep(10)
    
    # 检查流状态
    for i in range(manager.device_count):
        status = manager.get_stream_status(i)
        if status:
            print(f"设备 {i} 流状态: 运行中={status['running']}, 运行时间={status['uptime']:.2f}秒")
    
    # 保存配置
    manager.save_device_config("/etc/consciousness/usb_av_devices_config.json")
    
    # 停止所有流
    manager.stop_all_streams()
```
        """创建摄像头数据流"""
        stream_configs = []
        
        for camera_id, camera_info in self.cameras.items():
            device = camera_info['device']
            
            # 创建GStreamer管道配置
            pipeline = f"v4l2src device={device} ! videoconvert ! video/x-raw,format=RGB ! appsink"
            
            stream_configs.append({
                'camera_id': camera_id,
                'device': device,
                'pipeline': pipeline
            })
        
        return stream_configs
    
    def optimize_video_processing(self):
        """优化视频处理"""
        # 创建视频处理配置文件
        config = """
        # 视频处理优化配置
        export OPENCV_VIDEOIO_PRIORITY_MSMF=1
        export OPENCV_THREAD_COUNT=8
        export OMP_NUM_THREADS=8
        export GStreamerPluginPath=/usr/lib/gstreamer-1.0
        """
        
        with open('/etc/profile.d/video_optimization.sh', 'w') as f:
            f.write(config)
        
        os.chmod('/etc/profile.d/video_optimization.sh', 0o755)
        
        # 加载配置
        subprocess.run(["source", "/etc/profile.d/video_optimization.sh"])
        
        print("视频处理优化配置完成")

if __name__ == "__main__":
    manager = CameraManager()
    manager.detect_cameras()
    manager.configure_cameras()
    manager.optimize_video_processing()
```

---

## 8. 内存管理与优化

### 8.1 内存管理策略

创建 `/etc/sysctl.d/99-memory.conf`：

```conf
# 内存管理优化
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.min_free_kbytes=65536
vm.zone_reclaim_mode=0
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.overcommit_memory=1
vm.overcommit_ratio=80

# 大页面内存优化
vm.nr_hugepages=1024
vm.hugetlb_shm_group=1000

# 内存回收优化
vm.page-cluster=3
vm.laptop_mode=0
```

### 8.2 内存预分配与锁定

```python
#!/usr/bin/env python3
"""
内存管理脚本
用于具身智能系统的内存预分配和锁定
"""

import os
import mmap
import resource
import psutil

class MemoryManager:
    def __init__(self, total_memory_gb=16):
        self.total_memory_bytes = total_memory_gb * 1024 * 1024 * 1024
        self.allocated_memory = {}
        
    def preallocate_memory(self, component_name, size_mb):
        """预分配内存给指定组件"""
        size_bytes = size_mb * 1024 * 1024
        
        # 使用mlock锁定内存，防止交换
        try:
            # 设置内存锁定限制
            resource.setrlimit(resource.RLIMIT_MEMLOCK, 
                              (self.total_memory_bytes, self.total_memory_bytes))
            
            # 分配并锁定内存
            mem = mmap.mmap(-1, size_bytes, flags=mmap.MAP_SHARED | mmap.MAP_ANONYMOUS)
            mem.mlock()
            
            self.allocated_memory[component_name] = {
                'size_bytes': size_bytes,
                'memory': mem
            }
            
            print(f"为 {component_name} 预分配并锁定 {size_mb}MB 内存")
            return True
        except Exception as e:
            print(f"内存预分配失败: {e}")
            return False
    
    def configure_huge_pages(self):
        """配置大页面内存"""
        try:
            # 创建大页面挂载点
            os.makedirs("/mnt/hugepages", exist_ok=True)
            
            # 挂载大页面文件系统
            os.system("mount -t hugetlbfs nodev /mnt/hugepages 2>/dev/null || true")
            
            # 设置大页面数量
            os.system("echo 1024 > /proc/sys/vm/nr_hugepages")
            
            print("大页面内存配置完成")
            return True
        except Exception as e:
            print(f"大页面配置失败: {e}")
            return False
    
    def optimize_memory_allocation(self):
        """优化内存分配策略"""
        # 设置NUMA策略
        os.system("echo 0 > /proc/sys/vm/zone_reclaim_mode")
        
        # 设置透明大页面
        os.system("echo always > /sys/kernel/mm/transparent_hugepage/enabled")
        os.system("echo defer > /sys/kernel/mm/transparent_hugepage/defrag")
        
        # 设置内存回收
        os.system("echo 1 > /proc/sys/vm/drop_caches")
        
        print("内存分配策略优化完成")
    
    def monitor_memory_usage(self):
        """监控内存使用情况"""
        memory = psutil.virtual_memory()
        
        print(f"总内存: {memory.total // 1024 // 1024}MB")
        print(f"已使用: {memory.used // 1024 // 1024}MB ({memory.percent}%)")
        print(f"可用: {memory.available // 1024 // 1024}MB")
        print(f"缓存: {memory.cached // 1024 // 1024}MB")
        print(f"缓冲区: {memory.buffers // 1024 // 1024}MB")
        
        # 检查预分配内存
        for component, mem_info in self.allocated_memory.items():
            print(f"{component}: {mem_info['size_bytes'] // 1024 // 1024}MB (已锁定)")
    
    def setup_memory_cgroups(self):
        """设置内存控制组"""
        # 创建意识系统控制组
        os.makedirs("/sys/fs/cgroup/memory/consciousness", exist_ok=True)
        
        # 设置内存限制
        with open("/sys/fs/cgroup/memory/consciousness/memory.limit_in_bytes", "w") as f:
            f.write(str(self.total_memory_bytes))
        
        # 设置内存软限制
        with open("/sys/fs/cgroup/memory/consciousness/memory.soft_limit_in_bytes", "w") as f:
            f.write(str(int(self.total_memory_bytes * 0.9)))
        
        print("内存控制组配置完成")

if __name__ == "__main__":
    manager = MemoryManager(total_memory_gb=16)
    
    # 预分配内存给各组件
    manager.preallocate_memory("sensory_system", 1024)      # 1GB
    manager.preallocate_memory("multimodal_fusion", 2048)   # 2GB
    manager.preallocate_memory("cognitive_engine", 4096)    # 4GB
    manager.preallocate_memory("memory_system", 2048)       # 2GB
    
    # 配置大页面内存
    manager.configure_huge_pages()
    
    # 优化内存分配策略
    manager.optimize_memory_allocation()
    
    # 设置内存控制组
    manager.setup_memory_cgroups()
    
    # 监控内存使用
    manager.monitor_memory_usage()
```

---

## 9. 文件系统定制

### 9.1 文件系统选择与布局

```
分区布局方案
├── /boot/efi      (512MB, FAT32)       EFI系统分区
├── /boot          (1GB, ext4)          内核与引导文件
├── /              (20GB, ext4)         系统根分区
├── /var           (10GB, ext4)         可变数据
├── /tmp           (4GB, tmpfs)         临时文件(内存中)
├── /home          (50GB, ext4)         用户数据
├── /opt           (20GB, ext4)         应用程序
├── /data          (剩余空间, XFS或Btrfs)  意识系统数据
└── swap           (8GB, swap)          交换分区
```

### 9.2 文件系统优化配置

创建 `/etc/fstab` 优化配置：

```fstab
# /etc/fstab: 静态文件系统信息
#
# <文件系统> <挂载点>     <类型>  <选项>                          <转储> <通过>
UUID=XXXX-XXXX  /boot/efi   vfat    umask=0077,shortname=winnt   0     2
UUID=XXXX-XXXX  /boot       ext4    defaults,noatime              0     2
UUID=XXXX-XXXX  /           ext4    defaults,noatime,errors=remount-ro 0 1
UUID=XXXX-XXXX  /var        ext4    defaults,noatime              0     2
tmpfs           /tmp        tmpfs   defaults,noatime,size=4G      0     0
UUID=XXXX-XXXX  /home       ext4    defaults,noatime              0     2
UUID=XXXX-XXXX  /opt        ext4    defaults,noatime              0     2
UUID=XXXX-XXXX  /data       xfs     defaults,noatime,allocsize=64m 0     2
UUID=XXXX-XXXX  swap        swap    defaults                       0     0
```

### 9.3 高性能文件系统配置

```bash
#!/bin/bash
# 文件系统优化脚本

# 1. 创建XFS文件系统用于数据存储
mkfs.xfs -f -d su=64k,sw=1 -l size=128m -n size=64k /dev/sdaX

# 2. 挂载XFS文件系统
mkdir -p /data
mount -t xfs -o noatime,allocsize=64m /dev/sdaX /data

# 3. 配置ext4文件系统优化
tune2fs -o journal_data_writeback /dev/sdaY
tune2fs -O ^has_journal /dev/sdaY  # 如果不需要日志

# 4. 配置文件系统调度器
echo deadline > /sys/block/sda/queue/scheduler
echo 0 > /sys/block/sda/queue/rotational
echo 1 > /sys/block/sda/queue/iosched/fifo_batch

# 5. 配置文件系统缓存优化
echo 10 > /proc/sys/vm/vfs_cache_pressure
echo 5 > /proc/sys/vm/dirty_background_ratio
echo 15 > /proc/sys/vm/dirty_ratio
```

### 9.4 参数数据库文件系统优化

```python
#!/usr/bin/env python3
"""
参数数据库文件系统优化脚本
用于具身智能系统的参数存储优化
"""

import os
import subprocess
import shutil

class DatabaseFileSystemOptimizer:
    def __init__(self, db_path="/data/consciousness/db"):
        self.db_path = db_path
        self.tablespaces = {
            "sensory_data": "/data/consciousness/db/sensory",
            "cognitive_data": "/data/consciousness/db/cognitive",
            "memory_data": "/data/consciousness/db/memory",
            "temp_data": "/data/consciousness/db/temp"
        }
        
    def create_tablespaces(self):
        """创建数据库表空间"""
        for name, path in self.tablespaces.items():
            os.makedirs(path, exist_ok=True)
            
            # 创建文件系统
            if not os.path.ismount(path):
                # 使用tmpfs用于临时数据
                if name == "temp_data":
                    subprocess.run(["mount", "-t", "tmpfs", "-o", "size=4G,noatime", 
                                   "tmpfs", path])
                else:
                    # 对于其他数据，使用bind mount到优化后的目录
                    opt_path = f"/opt/consciousness/{name}"
                    os.makedirs(opt_path, exist_ok=True)
                    subprocess.run(["mount", "--bind", opt_path, path])
            
            print(f"表空间 {name} 创建在 {path}")
    
    def optimize_file_layout(self):
        """优化文件布局"""
        # 为不同类型的参数数据创建子目录
        directories = [
            "sensory/visual",
            "sensory/auditory",
            "sensory/tactile",
            "cognitive/attention",
            "cognitive/working_memory",
            "cognitive/long_term_memory",
            "memory/episodic",
            "memory/semantic",
            "memory/procedural"
        ]
        
        for directory in directories:
            full_path = os.path.join(self.db_path, directory)
            os.makedirs(full_path, exist_ok=True)
            
            # 设置文件系统属性
            subprocess.run(["chattr", "+C", full_path])  # 禁用写时复制
            subprocess.run(["chown", "-R", "consciousness:consciousness", full_path])
            
            print(f"创建目录 {full_path}")
    
    def configure_io_scheduling(self):
        """配置IO调度"""
        # 为数据库设备设置deadline调度器
        db_device = "/dev/sdaX"  # 替换为实际设备
        
        with open(f"/sys/block/{os.path.basename(db_device)}/queue/scheduler", "w") as f:
            f.write("deadline")
        
        # 设置队列深度
        with open(f"/sys/block/{os.path.basename(db_device)}/queue/nr_requests", "w") as f:
            f.write("256")
        
        print(f"IO调度器配置完成: {db_device}")
    
    def setup_filesystem_caching(self):
        """设置文件系统缓存"""
        # 创建缓存目录
        cache_dir = "/var/cache/consciousness"
        os.makedirs(cache_dir, exist_ok=True)
        
        # 设置tmpfs缓存
        subprocess.run(["mount", "-t", "tmpfs", "-o", "size=2G,noatime", 
                       "tmpfs", cache_dir])
        
        # 配置缓存策略
        cache_config = """
        # 文件系统缓存配置
        vm.vfs_cache_pressure=50
        vm.dirty_ratio=15
        vm.dirty_background_ratio=5
        """
        
        with open("/etc/sysctl.d/99-cache.conf", "w") as f:
            f.write(cache_config)
        
        # 应用配置
        subprocess.run(["sysctl", "-p", "/etc/sysctl.d/99.conf"])
        
        print("文件系统缓存配置完成")
    
    def create_backup_system(self):
        """创建备份系统"""
        backup_dir = "/backup/consciousness"
        os.makedirs(backup_dir, exist_ok=True)
        
        # 创建备份脚本
        backup_script = f"""
        #!/bin/bash
        # 数据库备份脚本
        
        SOURCE="{self.db_path}"
        DESTINATION="{backup_dir}"
        DATE=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="$DESTINATION/$DATE"
        
        # 创建备份目录
        mkdir -p "$BACKUP_DIR"
        
        # 使用rsync进行增量备份
        rsync -a --delete "$SOURCE/" "$BACKUP_DIR/"
        
        # 创建最新备份链接
        rm -f "$DESTINATION/latest"
        ln -s "$BACKUP_DIR" "$DESTINATION/latest"
        
        # 清理旧备份(保留最近7天)
        find "$DESTINATION" -maxdepth 1 -type d -name "20*" -mtime +7 -exec rm -rf {{}} \\;
        
        echo "备份完成: $BACKUP_DIR"
        """
        
        with open("/usr/local/bin/backup_consciousness_db.sh", "w") as f:
            f.write(backup_script)
        
        os.chmod("/usr/local/bin/backup_consciousness_db.sh", 0o755)
        
        # 创建cron任务
        cron_job = "0 2 * * * /usr/local/bin/backup_consciousness_db.sh\n"
        with open("/etc/cron.d/consciousness_backup", "w") as f:
            f.write(cron_job)
        
        print("备份系统配置完成")

if __name__ == "__main__":
    optimizer = DatabaseFileSystemOptimizer()
    optimizer.create_tablespaces()
    optimizer.optimize_file_layout()
    optimizer.configure_io_scheduling()
    optimizer.setup_filesystem_caching()
    optimizer.create_backup_system()
```

---

## 10. 安全机制设计

### 10.1 系统安全加固

创建 `/etc/security/limits.d/consciousness.conf`：

```conf
# 意识系统安全限制
consciousness soft nproc 32768
consciousness hard nproc 65536
consciousness soft nofile 65536
consciousness hard nofile 131072
consciousness soft memlock unlimited
consciousness hard memlock unlimited
consciousness soft stack 8192
consciousness hard stack 16384
```

### 10.2 内核安全模块配置

```bash
#!/bin/bash
# 内核安全模块配置脚本

# 1. 启用SELinux或AppArmor
if command -v setenforce &> /dev/null; then
    # SELinux配置
    setenforce 1
    sed -i 's/SELINUX=disabled/SELINUX=enforcing/g' /etc/selinux/config
    
    # 创建意识系统SELinux策略
    cat > /etc/selinux/targeted/contexts/files/file_contexts.local << EOF
/data/consciousness(/.*)?    system_u:object_r:consc_data_t:s0
/opt/consciousness(/.*)?     system_u:object_r:consc_exec_t:s0
/var/log/consciousness(/.*)?  system_u:object_r:consc_log_t:s0
EOF
    
    restorecon -R -v /data/consciousness
    restorecon -R -v /opt/consciousness
    restorecon -R -v /var/log/consciousness
else
    # AppArmor配置
    systemctl enable apparmor
    systemctl start apparmor
    
    # 创建意识系统AppArmor配置
    cat > /etc/apparmor.d/usr.bin.consciousness << EOF
#include <tunables/global>

/usr/bin/consciousness {
  #include <abstractions/base>
  #include <abstractions/python>
  
  capability dac_override,
  capability sys_resource,
  capability ipc_lock,
  
  /data/consciousness/** rw,
  /opt/consciousness/** ix,
  /var/log/consciousness/** w,
  
  /dev/video* rw,
  /dev/snd/* rw,
  /dev/dri/** rw,
  
  network inet stream,
  network inet dgram,
}
EOF
    
    systemctl restart apparmor
    aa-enforce /etc/apparmor.d/usr.bin.consciousness
fi

# 2. 配置内核安全参数
cat > /etc/sysctl.d/99-security.conf << EOF
# 内核安全参数
kernel.kptr_restrict=1
kernel.dmesg_restrict=1
kernel.kexec_load=0
kernel.yama.ptrace_scope=1
fs.protected_regular=1
fs.protected_fifos=1
fs.suid_dumpable=0
net.ipv4.ip_forward=0
net.ipv4.conf.all.send_redirects=0
net.ipv4.conf.default.send_redirects=0
net.ipv4.conf.all.accept_source_route=0
net.ipv4.conf.default.accept_source_route=0
net.ipv4.conf.all.accept_redirects=0
net.ipv4.conf.default.accept_redirects=0
net.ipv4.icmp_echo_ignore_broadcasts=1
net.ipv4.icmp_ignore_bogus_error_responses=1
net.ipv4.tcp_syncookies=1
EOF

sysctl -p /etc/sysctl.d/99-security.conf

# 3. 配置防火墙
if command -v ufw &> /dev/null; then
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow from 192.168.0.0/16 to any port 22 proto tcp
    ufw --force enable
elif command -v firewall-cmd &> /dev/null; then
    systemctl enable firewalld
    systemctl start firewalld
    firewall-cmd --set-default-zone=drop
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-source=192.168.0.0/16 --zone=trusted
    firewall-cmd --reload
fi

echo "内核安全模块配置完成"
```

### 10.3 数据加密与保护

```python
#!/usr/bin/env python3
"""
数据加密与保护脚本
用于具身智能系统的敏感数据保护
"""

import os
import subprocess
import hashlib
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DataProtectionManager:
    def __init__(self, data_dir="/data/consciousness"):
        self.data_dir = data_dir
        self.encrypted_dir = os.path.join(data_dir, "encrypted")
        self.key_dir = os.path.join(data_dir, "keys")
        
        # 创建目录
        os.makedirs(self.encrypted_dir, exist_ok=True)
        os.makedirs(self.key_dir, exist_ok=True)
        
        # 加密密钥
        self.master_key = None
        self.cipher_suite = None
        
    def generate_master_key(self, password):
        """生成主加密密钥"""
        # 使用PBKDF2从密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'consciousness_salt_2023',
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.master_key = key
        self.cipher_suite = Fernet(key)
        
        # 保存密钥到安全位置
        key_file = os.path.join(self.key_dir, "master.key")
        with open(key_file, "wb") as f:
            f.write(key)
        
        # 设置密钥文件权限
        os.chmod(key_file, 0o600)
        
        print(f"主密钥已生成并保存到 {key_file}")
        return key
    
    def load_master_key(self, password):
        """加载主加密密钥"""
        key_file = os.path.join(self.key_dir, "master.key")
        
        if not os.path.exists(key_file):
            return self.generate_master_key(password)
        
        with open(key_file, "rb") as f:
            self.master_key = f.read()
            self.cipher_suite = Fernet(self.master_key)
        
        print("主密钥已加载")
        return self.master_key
    
    def encrypt_file(self, file_path):
        """加密文件"""
        if not self.cipher_suite:
            raise ValueError("未加载加密密钥")
        
        # 读取原始文件
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # 加密数据
        encrypted_data = self.cipher_suite.encrypt(file_data)
        
        # 保存加密文件
        rel_path = os.path.relpath(file_path, self.data_dir)
        encrypted_path = os.path.join(self.encrypted_dir, f"{rel_path}.enc")
        
        os.makedirs(os.path.dirname(encrypted_path), exist_ok=True)
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
        
        # 设置权限
        os.chmod(encrypted_path, 0o600)
        
        # 计算文件哈希
        file_hash = hashlib.sha256(file_data).hexdigest()
        
        # 记录加密信息
        encryption_log = {
            "original_path": file_path,
            "encrypted_path": encrypted_path,
            "hash": file_hash,
            "timestamp": os.path.getmtime(file_path)
        }
        
        log_file = os.path.join(self.key_dir, "encryption_log.json")
        logs = []
        
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        
        logs.append(encryption_log)
        
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)
        
        print(f"文件已加密: {file_path} -> {encrypted_path}")
        return encrypted_path
    
    def decrypt_file(self, encrypted_path, output_path=None):
        """解密文件"""
        if not self.cipher_suite:
            raise ValueError("未加载加密密钥")
        
        # 读取加密文件
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
        
        # 解密数据
        file_data = self.cipher_suite.decrypt(encrypted_data)
        
        # 确定输出路径
        if not output_path:
            # 从加密路径推导原始路径
            rel_path = os.path.relpath(encrypted_path, self.encrypted_dir)
            rel_path = rel_path[:-4]  # 移除.enc扩展名
            output_path = os.path.join(self.data_dir, rel_path)
        
        # 保存解密文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(file_data)
        
        print(f"文件已解密: {encrypted_path} -> {output_path}")
        return output_path
    
    def setup_encrypted_filesystem(self):
        """设置加密文件系统"""
        # 创建加密目录
        encrypted_fs = os.path.join(self.data_dir, "encrypted_fs")
        os.makedirs(encrypted_fs, exist_ok=True)
        
        # 使用eCryptfs设置加密文件系统
        if not os.path.ismount(encrypted_fs):
            # 挂载加密文件系统
            subprocess.run([
                "mount", "-t", "ecryptfs",
                os.path.join(self.data_dir, "raw_data"),
                encrypted_fs,
                "-o", "ecryptfs_cipher=aes,ecryptfs_key_bytes=16,ecryptfs_passthrough=no"
            ])
        
        print(f"加密文件系统已设置在 {encrypted_fs}")
        return encrypted_fs
    
    def create_secure_backup(self, source_dir, backup_dir):
        """创建安全备份"""
        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)
        
        # 使用tar和gpg创建加密备份
        backup_file = os.path.join(backup_dir, f"consciousness_backup_{os.path.basename(source_dir)}.tar.gz.gpg")
        
        subprocess.run([
            "tar", "-czf", "-", source_dir
        ], stdout=subprocess.PIPE)
        
        # 使用GPG加密
        subprocess.run([
            "gpg", "--symmetric", "--cipher-algo", "AES256",
            "--output", backup_file
        ], input=subprocess.PIPE.stdout)
        
        print(f"安全备份已创建: {backup_file}")
        return backup_file
    
    def setup_access_control(self):
        """设置访问控制"""
        # 创建意识系统用户组
        subprocess.run(["groupadd", "-f", "consciousness"])
        
        # 设置目录权限
        subprocess.run(["chown", "-R", "consciousness:consciousness", self.data_dir])
        subprocess.run(["chmod", "-R", "750", self.data_dir])
        
        # 设置敏感目录权限
        subprocess.run(["chmod", "-R", "700", self.encrypted_dir])
        subprocess.run(["chmod", "-R", "700", self.key_dir])
        
        print("访问控制已设置")

if __name__ == "__main__":
    manager = DataProtectionManager()
    
    # 从环境变量或安全输入获取密码
    import getpass
    password = getpass.getpass("输入加密密码: ")
    
    # 加载或生成密钥
    manager.load_master_key(password)
    
    # 设置加密文件系统
    manager.setup_encrypted_filesystem()
    
    # 设置访问控制
    manager.setup_access_control()
    
    # 示例: 加密敏感文件
    sensitive_file = os.path.join(manager.data_dir, "sensitive_data.json")
    if os.path.exists(sensitive_file):
        manager.encrypt_file(sensitive_file)
    
    print("数据保护设置完成")
```

---

## 11. 网络栈优化

### 11.1 网络参数优化

创建 `/etc/sysctl.d/99-network.conf`：

```conf
# 网络栈优化
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 65535

net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.tcp_mem = 196608 262144 393216

net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15

net.ipv4.udp_mem = 102400 873800 16777216
net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192

net.core.default_qdisc = fq
```

### 11.2 网络接口优化

```bash
#!/bin/bash
# 网络接口优化脚本

# 获取主网络接口
INTERFACE=$(ip route | grep default | awk '{print $5}')

# 设置网络接口参数
ethtool -G $INTERFACE rx 4096 tx 4096 rx-jumbo 4096
ethtool -K $INTERFACE tso on gso on gro on lro on
ethtool -K $INTERFACE tx off rx off

# 设置网络队列
echo $((`nproc`*2)) > /proc/sys/net/core/netdev_max_backlog

# 设置RPS(接收包导向)
echo $((`nproc`-1)) > /sys/class/net/$INTERFACE/queues/rx-0/rps_cpus

# 设置RFS(接收流导向)
echo 32768 > /proc/sys/net/core.rps_sock_flow_entries
echo 32768 > /sys/class/net/$INTERFACE/queues/rx-0/rps_flow_cnt

# 设置XPS(发送包导向)
for i in $(seq 0 $((`nproc`-1))); do
    echo $i > /sys/class/net/$INTERFACE/queues/tx-$i/xps_cpus
done

echo "网络接口优化完成"
```

### 11.3 分布式感知网络配置

```python
#!/usr/bin/env python3
"""
分布式感知网络配置脚本
用于具身智能系统的多节点通信优化
"""

import os
import subprocess
import socket
import json
import time

class DistributedNetworkManager:
    def __init__(self, config_file="/etc/consciousness/network_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """加载网络配置"""
        default_config = {
            "cluster_nodes": [],
            "multicast_group": "239.255.0.1",
            "multicast_port": 5000,
            "heartbeat_interval": 1,
            "data_sync_interval": 5,
            "network_timeout": 5,
            "max_retries": 3
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            return default_config
    
    def save_config(self):
        """保存网络配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def discover_nodes(self):
        """发现集群中的节点"""
        # 使用多播发现节点
        import struct
        
        multicast_group = (self.config["multicast_group"], self.config["multicast_port"])
        
        # 创建多播套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.config["network_timeout"])
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        
        # 发送发现消息
        message = json.dumps({
            "type": "discovery",
            "timestamp": time.time(),
            "node_id": socket.gethostname()
        }).encode('utf-8')
        
        sock.sendto(message, multicast_group)
        
        # 等待响应
        discovered_nodes = []
        start_time = time.time()
        
        while time.time() - start_time < self.config["network_timeout"]:
            try:
                data, addr = sock.recvfrom(1024)
                response = json.loads(data.decode('utf-8'))
                
                if response.get("type") == "discovery_response":
                    node_info = {
                        "hostname": response.get("hostname"),
                        "ip": addr[0],
                        "port": response.get("port"),
                        "capabilities": response.get("capabilities", [])
                    }
                    
                    discovered_nodes.append(node_info)
            except socket.timeout:
                break
            except Exception as e:
                print(f"发现节点错误: {e}")
        
        sock.close()
        
        # 更新配置
        self.config["cluster_nodes"] = discovered_nodes
        self.save_config()
        
        print(f"发现 {len(discovered_nodes)} 个节点")
        return discovered_nodes
    
    def setup_multicast_listener(self):
        """设置多播监听器"""
        import threading
        
        def listener():
            multicast_group = self.config["multicast_group"]
            port = self.config["multicast_port"]
            
            # 创建多播监听套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定到多播端口
            sock.bind(('', port))
            
            # 加入多播组
            group = socket.inet_aton(multicast_group)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    message = json.loads(data.decode('utf-8'))
                    
                    if message.get("type") == "discovery":
                        # 发送发现响应
                        response = {
                            "type": "discovery_response",
                            "hostname": socket.gethostname(),
                            "port": 5001,
                            "capabilities": ["sensory", "cognitive", "memory"]
                        }
                        
                        response_data = json.dumps(response).encode('utf-8')
                        sock.sendto(response_data, addr)
                    
                    elif message.get("type") == "data_sync":
                        # 处理数据同步
                        self.handle_data_sync(message)
                    
                    elif message.get("type") == "heartbeat":
                        # 处理心跳
                        self.handle_heartbeat(message, addr)
                
                except Exception as e:
                    print(f"多播监听错误: {e}")
        
        # 启动监听线程
        listener_thread = threading.Thread(target=listener)
        listener_thread.daemon = True
        listener_thread.start()
        
        print("多播监听器已启动")
    
    def setup_heartbeat_system(self):
        """设置心跳系统"""
        import threading
        
        def heartbeat_sender():
            while True:
                try:
                    # 发送心跳消息
                    message = {
                        "type": "heartbeat",
                        "timestamp": time.time(),
                        "node_id": socket.gethostname(),
                        "status": "active"
                    }
                    
                    message_data = json.dumps(message).encode('utf-8')
                    
                    # 发送到所有节点
                    for node in self.config["cluster_nodes"]:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.sendto(message_data, (node["ip"], node["port"]))
                            sock.close()
                        except Exception as e:
                            print(f"发送心跳到 {node['ip']} 失败: {e}")
                    
                    # 等待下一个心跳周期
                    time.sleep(self.config["heartbeat_interval"])
                
                except Exception as e:
                    print(f"心跳发送错误: {e}")
        
        # 启动心跳线程
        heartbeat_thread = threading.Thread(target=heartbeat_sender)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        print("心跳系统已启动")
    
    def handle_data_sync(self, message):
        """处理数据同步"""
        # 这里实现数据同步逻辑
        print(f"收到数据同步请求: {message.get('sync_type')}")
        
        # 根据同步类型处理数据
        sync_type = message.get("sync_type")
        if sync_type == "sensory_data":
            self.sync_sensory_data(message.get("data"))
        elif sync_type == "cognitive_state":
            self.sync_cognitive_state(message.get("data"))
        elif sync_type == "memory_update":
            self.sync_memory_update(message.get("data"))
    
    def handle_heartbeat(self, message, addr):
        """处理心跳"""
        # 更新节点状态
        node_id = message.get("node_id")
        timestamp = message.get("timestamp")
        status = message.get("status")
        
        # 更新节点状态信息
        for node in self.config["cluster_nodes"]:
            if node.get("hostname") == node_id:
                node["last_heartbeat"] = timestamp
                node["status"] = status
                break
        
        print(f"收到心跳: {node_id} ({status})")
    
    def sync_sensory_data(self, data):
        """同步感官数据"""
        # 实现感官数据同步逻辑
        pass
    
    def sync_cognitive_state(self, data):
        """同步认知状态"""
        # 实现认知状态同步逻辑
        pass
    
    def sync_memory_update(self, data):
        """同步内存更新"""
        # 实现内存更新同步逻辑
        pass
    
    def optimize_network_for_realtime(self):
        """优化网络以支持实时通信"""
        # 设置网络优先级
        subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "root", "handle", "1:", "prio"])
        subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "parent", "1:1", "handle", "10:", "pfifo"])
        subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "parent", "1:2", "handle", "20:", "pfifo"])
        subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "parent", "1:3", "handle", "30:", "pfifo"])
        
        # 设置流量过滤器
        subprocess.run(["tc", "filter", "add", "dev", "eth0", "parent", "1:0", "prio", "1", "u32", 
                       "match", "ip", "dport", "5000", "0xffff", "flowid", "1:1"])
        
        print("网络实时优化完成")
    
    def start_network_services(self):
        """启动网络服务"""
        # 启动多播监听器
        self.setup_multicast_listener()
        
        # 启动心跳系统
        self.setup_heartbeat_system()
        
        # 优化网络
        self.optimize_network_for_realtime()
        
        print("网络服务已启动")

if __name__ == "__main__":
    manager = DistributedNetworkManager()
    
    # 发现节点
    manager.discover_nodes()
    
    # 启动网络服务
    manager.start_network_services()
    
    print("分布式网络管理器已启动")
```

---

## 12. 系统服务与守护进程

### 12.1 意识系统核心服务

创建 `/etc/systemd/system/consciousness-core.service`：

```ini
[Unit]
Description=Consciousness System Core Service
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=consciousness
Group=consciousness
WorkingDirectory=/opt/consciousness
ExecStart=/opt/consciousness/bin/consciousness-core --config /etc/consciousness/core.conf
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# 资源限制
LimitNOFILE=65536
LimitNPROC=32768
LimitMEMLOCK=infinity

# 实时优先级
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=80
IOSchedulingClass=realtime
IOSchedulingPriority=1

# 环境变量
Environment=PYTHONPATH=/opt/consciousness/lib
Environment=OMP_NUM_THREADS=8
Environment=MKL_NUM_THREADS=8
Environment=CUDA_VISIBLE_DEVICES=0,1

[Install]
WantedBy=multi-user.target
```

### 12.2 感知系统服务

创建 `/etc/systemd/system/consciousness-sensory.service`：

```ini
[Unit]
Description=Consciousness Sensory Processing Service
After=consciousness-core.service
Requires=consciousness-core.service

[Service]
Type=simple
User=consciousness
Group=consciousness
WorkingDirectory=/opt/consciousness
ExecStart=/opt/consciousness/bin/sensory-processor --config /etc/consciousness/sensory.conf
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# 资源限制
LimitNOFILE=65536
LimitNPROC=32768
LimitMEMLOCK=infinity

# 实时优先级
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=90
IOSchedulingClass=realtime
IOSchedulingPriority=0

# 环境变量
Environment=PYTHONPATH=/opt/consciousness/lib
Environment=OMP_NUM_THREADS=4
Environment=MKL_NUM_THREADS=4

[Install]
WantedBy=multi-user.target
```

### 12.3 服务管理脚本

```python
#!/usr/bin/env python3
"""
意识系统服务管理脚本
用于管理和监控具身智能系统的各项服务
"""

import os
import subprocess
import time
import json
import signal
import psutil
from datetime import datetime

class ConsciousnessServiceManager:
    def __init__(self):
        self.services = {
            "consciousness-core": {
                "description": "意识系统核心服务",
                "priority": 1,
                "dependencies": [],
                "cpu_affinity": list(range(2, 6)),
                "memory_limit": "2G"
            },
            "consciousness-sensory": {
                "description": "感知处理服务",
                "priority": 2,
                "dependencies": ["consciousness-core"],
                "cpu_affinity": list(range(6, 10)),
                "memory_limit": "4G"
            },
            "consciousness-cognitive": {
                "description": "认知处理服务",
                "priority": 3,
                "dependencies": ["consciousness-core"],
                "cpu_affinity": list(range(10, 14)),
                "memory_limit": "8G"
            },
            "consciousness-memory": {
                "description": "记忆系统服务",
                "priority": 4,
                "dependencies": ["consciousness-core"],
                "cpu_affinity": [14, 15],
                "memory_limit": "4G"
            }
        }
        
        self.service_status = {}
        self.service_pids = {}
        
    def start_service(self, service_name):
        """启动指定服务"""
        if service_name not in self.services:
            print(f"未知服务: {service_name}")
            return False
        
        # 检查依赖
        service_info = self.services[service_name]
        for dependency in service_info["dependencies"]:
            if not self.is_service_running(dependency):
                print(f"启动 {service_name} 失败: 依赖服务 {dependency} 未运行")
                return False
        
        # 启动服务
        try:
            # 使用systemctl启动服务
            result = subprocess.run(
                ["systemctl", "start", service_name],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                print(f"启动 {service_name} 失败: {result.stderr}")
                return False
            
            # 等待服务启动
            time.sleep(2)
            
            # 检查服务状态
            if self.is_service_running(service_name):
                print(f"服务 {service_name} 启动成功")
                return True
            else:
                print(f"服务 {service_name} 启动后未运行")
                return False
                
        except Exception as e:
            print(f"启动 {service_name} 异常: {e}")
            return False
    
    def stop_service(self, service_name):
        """停止指定服务"""
        if service_name not in self.services:
            print(f"未知服务: {service_name}")
            return False
        
        try:
            # 使用systemctl停止服务
            result = subprocess.run(
                ["systemctl", "stop", service_name],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                print(f"停止 {service_name} 失败: {result.stderr}")
                return False
            
            # 等待服务停止
            time.sleep(2)
            
            # 检查服务状态
            if not self.is_service_running(service_name):
                print(f"服务 {service_name} 停止成功")
                return True
            else:
                print(f"服务 {service_name} 停止后仍在运行")
                return False
                
        except Exception as e:
            print(f"停止 {service_name} 异常: {e}")
            return False
    
    def restart_service(self, service_name):
        """重启指定服务"""
        if self.stop_service(service_name):
            return self.start_service(service_name)
        return False
    
    def is_service_running(self, service_name):
        """检查服务是否运行"""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False
    
    def get_service_status(self, service_name):
        """获取服务状态"""
        try:
            result = subprocess.run(
                ["systemctl", "status", service_name],
                capture_output=True, text=True
            )
            
            # 解析状态信息
            status = {
                "name": service_name,
                "active": result.stdout.strip().split('\n')[0].strip().endswith("active (running)"),
                "description": self.services.get(service_name, {}).get("description", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # 提取PID
            for line in result.stdout.split('\n'):
                if "Main PID:" in line:
                    pid_part = line.split("Main PID:")[1].strip().split()[0]
                    status["pid"] = int(pid_part)
                    
                    # 获取进程资源使用情况
                    if pid_part.isdigit():
                        try:
                            process = psutil.Process(int(pid_part))
                            status["cpu_percent"] = process.cpu_percent()
                            status["memory_info"] = process.memory_info()._asdict()
                            status["num_threads"] = process.num_threads()
                        except Exception:
                            pass
                    break
            
            return status
        except Exception as e:
            return {
                "name": service_name,
                "active": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_all_services_status(self):
        """获取所有服务状态"""
        all_status = {}
        
        for service_name in self.services:
            all_status[service_name] = self.get_service_status(service_name)
        
        return all_status
    
    def start_all_services(self):
        """按优先级启动所有服务"""
        # 按优先级排序服务
        sorted_services = sorted(
            self.services.items(),
            key=lambda x: x[1]["priority"]
        )
        
        for service_name, service_info in sorted_services:
            print(f"启动服务: {service_name} ({service_info['description']})")
            if not self.start_service(service_name):
                print(f"启动 {service_name} 失败，停止后续服务启动")
                return False
            
            # 等待服务稳定
            time.sleep(3)
        
        print("所有服务启动完成")
        return True
    
    def stop_all_services(self):
        """按相反优先级停止所有服务"""
        # 按相反优先级排序服务
        sorted_services = sorted(
            self.services.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        )
        
        for service_name, service_info in sorted_services:
            print(f"停止服务: {service_name} ({service_info['description']})")
            if not self.stop_service(service_name):
                print(f"停止 {service_name} 失败")
        
        print("所有服务停止完成")
        return True
    
    def monitor_services(self):
        """监控服务状态"""
        while True:
            try:
                all_status = self.get_all_services_status()
                
                for service_name, status in all_status.items():
                    if not status.get("active", False):
                        print(f"警告: 服务 {service_name} 未运行，尝试重启")
                        self.restart_service(service_name)
                
                # 等待下次检查
                time.sleep(10)
                
            except KeyboardInterrupt:
                print("服务监控停止")
                break
            except Exception as e:
                print(f"服务监控错误: {e}")
                time.sleep(5)
    
    def setup_service_monitoring(self):
        """设置服务监控"""
        # 创建监控脚本
        monitor_script = """#!/bin/bash
# 服务监控脚本

while true; do
    for service in consciousness-core consciousness-sensory consciousness-cognitive consciousness-memory; do
        if ! systemctl is-active --quiet $service; then
            echo "$(date): 服务 $service 未运行，尝试重启" >> /var/log/consciousness/service_monitor.log
            systemctl restart $service
        fi
    done
    sleep 30
done
"""
        
        with open("/usr/local/bin/consciousness_service_monitor.sh", "w") as f:
            f.write(monitor_script)
        
        os.chmod("/usr/local/bin/consciousness_service_monitor.sh", 0o755)
        
        # 创建监控服务
        monitor_service = """[Unit]
Description=Consciousness Service Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/consciousness_service_monitor.sh
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
"""
        
        with open("/etc/systemd/system/consciousness-service-monitor.service", "w") as f:
            f.write(monitor_service)
        
        # 启用监控服务
        subprocess.run(["systemctl", "daemon-reload"])
        subprocess.run(["systemctl", "enable", "consciousness-service-monitor"])
        subprocess.run(["systemctl", "start", "consciousness-service-monitor"])
        
        print