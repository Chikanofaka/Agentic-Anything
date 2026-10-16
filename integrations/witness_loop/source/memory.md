# Memory Contract

每条记忆包含 `fact`, `source`, `scene`, `turn`。`source` 区分 `PLAYER_STATEMENT`, `PLAYER_COMMITMENT`, `NPC_ADMISSION`。MVM 不把系统推断写成玩家事实；同一 fact 去重。跨场景读取会影响称呼、承诺召回、线索释放与结局。

Doing 后应增加：admission gate、隐私分类、删除/编辑、时间范围、冲突标记、模型输出 schema 校验和回放测试。
