# NomadMem — 自主AI记忆与人格模拟系统

## 核心理念

**万物皆节点，万物皆关联**

记忆的最小单元是「信息片段」，不区分物理实体、感官输入、抽象概念还是虚构产物。

## 架构

```
nodes 表（万物皆节点）
├── 可感知对象（人、物、地点）
├── 感官片段（录音、图像、文本）
├── 抽象概念（思想、方法论）
├── 虚构产物（梦、假设、想象）
├── 情感状态（恐惧、兴奋）
└── 时空标记（地点、时间、坐标）

edges 表（万物关联不受限）
└── 任意节点间的任意关联
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt
python -m spacy download zh_core_web_sm

# 运行测试
python tests/test_pipeline.py

# 启动系统
python run.py
```

## 交互模式

```
nomad> node 张三 person
nomad> tag 张三 性别 男
nomad> link 张三 黑色西装 穿着
nomad> path 张三 会议室A
nomad> search 黑色
```

## v3.0 特性

- 统一节点表：所有类型平等存储
- 自由关联：edge_type 不设限制
- 自由标签：tags_json 动态扩展
- 跨类型关联：梦→情感→生理反应

## License

MIT
