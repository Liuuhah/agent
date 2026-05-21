"""
模块名称：_prompt_engine.py
职责：封装所有 LLM Prompt 构建逻辑
依赖：无
被依赖：_business_logic.py

核心方法：
- _build_feeding_plan_prompt(): 构建喂养计划 Prompt
- _build_diagnosis_prompt(): 构建症状诊断 Prompt
- _build_health_report_prompt(): 构建健康报告 Prompt
"""

from typing import Dict, Any


class PromptEngineMixin:
    """Prompt 工程混入类"""
    
    def _build_feeding_plan_prompt(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        构建喂养计划分析的 LLM Prompt
        
        设计原则：
        - 结构化 Prompt → 提高 LLM 输出一致性
        - 物种差异化 → 猫/狗营养需求不同
        - 年龄阶段适配 → 幼宠/成宠/老宠喂养策略不同
        
        Args:
            pet_profile_dict: 宠物档案字典
        
        Returns:
            str: 格式化的 Prompt 文本
        """
        name = pet_profile_dict.get("name", "未知宠物")
        species = pet_profile_dict.get("species", "unknown")
        breed = pet_profile_dict.get("breed", "未知品种")
        age = pet_profile_dict.get("age", 0)
        weight = pet_profile_dict.get("weight", 0)
        gender = pet_profile_dict.get("gender", "unknown")
        
        # 物种映射（中文显示）
        species_map = {"cat": "猫咪", "dog": "狗狗", "other": "其他宠物", "unknown": "宠物"}
        species_cn = species_map.get(species, "宠物")
        
        # 年龄阶段判断
        if age < 1:
            life_stage = "幼年"
        elif age < 7:
            life_stage = "成年"
        else:
            life_stage = "老年"
        
        # 构建健康记录摘要（如果有）
        records_summary = ""
        if "recent_records" in pet_profile_dict and pet_profile_dict["recent_records"]:
            records_summary = "\n【最近健康记录】\n"
            for record in pet_profile_dict["recent_records"][-5:]:  # 最近 5 条
                records_summary += f"- {record.get('date', '未知日期')}: {record.get('desc', '无描述')}\n"
        
        prompt = f"""你是一位专业的宠物营养师，请为以下宠物制定个性化的喂养计划。

【宠物档案】
- 名字：{name}
- 物种：{species_cn}
- 品种：{breed}
- 年龄：{age} 岁（{life_stage}期）
- 体重：{weight} kg
- 性别：{"公" if gender == "male" else "母" if gender == "female" else "未知"}
{records_summary}

【任务要求】
请提供以下内容：
1. **每日喂食量建议**：根据年龄、体重计算具体克数
2. **喂食频率**：每日几次，每次间隔多久
3. **营养配比**：蛋白质、脂肪、碳水化合物的比例建议
4. **推荐食物类型**：干粮/湿粮/生骨肉等
5. **注意事项**：该品种/年龄段的特殊饮食禁忌

【输出格式】
请使用清晰的 Markdown 格式，分点列出建议。语气要亲切专业，像在和宠物主人对话。

【开始分析】"""
        
        return prompt
    
    def _build_diagnosis_prompt(self, pet_profile_dict: Dict[str, Any], symptoms: str) -> str:
        """
        构建症状诊断的 LLM Prompt
        
        设计原则：
        - 强调"非医疗诊断"免责声明 → 法律合规
        - 提供紧急程度判断 → 帮助用户决策是否立即就医
        - 结合年龄/品种特点 → 提高诊断准确性
        
        Args:
            pet_profile_dict: 宠物档案字典
            symptoms: 用户描述的症状
        
        Returns:
            str: 格式化的 Prompt 文本
        """
        name = pet_profile_dict.get("name", "未知宠物")
        species = pet_profile_dict.get("species", "unknown")
        breed = pet_profile_dict.get("breed", "未知品种")
        age = pet_profile_dict.get("age", 0)
        
        species_map = {"cat": "猫咪", "dog": "狗狗", "other": "其他宠物", "unknown": "宠物"}
        species_cn = species_map.get(species, "宠物")
        
        prompt = f"""你是一位经验丰富的宠物兽医助手（注意：你不是真正的医生，仅提供参考建议）。

【宠物信息】
- 名字：{name}
- 物种：{species_cn}
- 品种：{breed}
- 年龄：{age} 岁

【症状描述】
{symptoms}

【任务要求】
请提供以下内容：
1. **可能原因**：列出 2-3 个最可能的病因（按可能性排序）
2. **紧急程度**：🟢 低 / 🟡 中 / 🔴 高（并说明判断依据）
3. **家庭护理建议**：在就医前可以采取的措施
4. **何时就医**：什么情况下必须立即去医院
5. **预防措施**：未来如何避免类似问题

【重要声明】
请在回答开头明确标注："⚠️ 本建议仅供参考，不能替代专业兽医诊断。如症状严重或持续，请立即就医。"

【输出格式】
使用清晰的 Markdown 格式，语气要温和专业，避免引起宠物主人恐慌。

【开始诊断】"""
        
        return prompt
    
    def _build_health_report_prompt(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        构建健康报告的 LLM Prompt
        
        设计原则：
        - 整合历史记录 → 展示趋势分析能力
        - 输出结构化报告 → 便于前端展示或导出
        
        Args:
            pet_profile_dict: 宠物档案字典（包含 recent_records）
        
        Returns:
            str: 格式化的 Prompt 文本
        """
        name = pet_profile_dict.get("name", "未知宠物")
        species = pet_profile_dict.get("species", "unknown")
        breed = pet_profile_dict.get("breed", "未知品种")
        age = pet_profile_dict.get("age", 0)
        weight = pet_profile_dict.get("weight", 0)
        
        species_map = {"cat": "猫咪", "dog": "狗狗", "other": "其他宠物", "unknown": "宠物"}
        species_cn = species_map.get(species, "宠物")
        
        # 格式化健康记录
        records_text = "暂无健康记录"
        if "recent_records" in pet_profile_dict and pet_profile_dict["recent_records"]:
            records_text = ""
            for record in pet_profile_dict["recent_records"]:
                records_text += f"- {record.get('date', '未知日期')} [{record.get('type', '未知类型')}]: {record.get('desc', '无描述')}\n"
        
        prompt = f"""你是一位专业的宠物健康管理师，请根据以下信息生成综合健康报告。

【宠物档案】
- 名字：{name}
- 物种：{species_cn}
- 品种：{breed}
- 年龄：{age} 岁
- 体重：{weight} kg

【健康记录时间线】
{records_text}

【任务要求】
请生成一份结构化的健康报告，包含：
1. **整体评估**：健康状况评分（1-10 分）及简要评价
2. **历史趋势分析**：从健康记录中发现的模式或问题
3. **风险提示**：当前存在的潜在健康风险
4. **改进建议**：具体的行动项（如增加运动、调整饮食、定期体检等）
5. **下次体检建议时间**：根据年龄和健康状况推荐

【输出格式】
使用清晰的 Markdown 格式，包含标题、列表、重点标注。语气要专业且鼓励性强。

【开始生成报告】"""
        
        return prompt
