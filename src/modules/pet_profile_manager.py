"""
宠物档案管理主模块

整合双向链表和哈希表，提供完整的宠物档案管理功能

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

模块职责：
- 注册新宠物（自动创建健康时间线）
- 管理宠物健康记录（添加、查看、删除）
- 宠物档案检索（按名字、品种搜索）
- 宠物信息更新和删除

数据结构应用：
- 哈希表（PetProfileManager）：O(1) 快速检索宠物档案
- 双向链表（DoublyLinkedList）：O(n) 健康记录时间线管理

---
【前台接待员】
核心作用：把“档案柜”和“病历本”结合起来，提供具体的服务。
功能：
注册 (register_pet)：在档案柜里建个新号，并给发一本空白的病历本。
添加记录 (add_health_record)：往病历本里写新的一页。
搜索与更新：帮你在档案柜里找宠物，或者修改它们的年龄体重。
工程亮点：它体现了“显式资源释放”，当删除一只宠物时，它会先销毁病历本再注销档案，非常严谨。


"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_structures.doubly_linked_list import DoublyLinkedList, HealthRecordNode
from data_structures.hash_table import PetProfile, PetProfileManager

# 【持久化】数据文件路径配置
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PETS_FILE = DATA_DIR / "pets.json"


class SmartPetProfileSystem:
    """
    智能宠物档案系统
    
    整合双向链表（健康记录时间线）和哈希表（宠物档案快速检索）
    提供完整的宠物管理功能
    
    时间复杂度分析：
    - 注册宠物：O(1) - 哈希表插入
    - 添加健康记录：O(1) - 链表尾部追加
    - 查看记录：O(n) 或 O(count) - 链表遍历
    - 搜索宠物：O(n) - 需要遍历哈希表的所有值
    - 删除宠物：O(1) - 哈希表删除
    """
    
    def __init__(self):
        """初始化智能宠物档案系统"""
        self.profile_manager = PetProfileManager()
        
        # 【持久化】自动加载历史数据
        self._load_from_file()
    
    def register_pet(self, pet_id: str, name: str, breed: str, age: float, 
                     weight: float, gender: str = "unknown", species: str = "dog") -> PetProfile:
        """
        注册新宠物，自动初始化健康时间线
        
        时间复杂度：O(1) - 哈希表插入
        空间复杂度：O(1) - 创建一个新的 PetProfile 和 DoublyLinkedList
        
        Args:
            pet_id: 宠物唯一 ID
            name: 宠物名字
            breed: 品种
            age: 年龄（岁）
            weight: 体重（公斤）
            gender: 性别，"male" / "female" / "unknown"，默认 "unknown"
            species: 物种，"cat" / "dog" / "other"，默认 "dog"
        
        Returns:
            PetProfile: 创建成功的宠物档案对象
        
        Raises:
            ValueError: 如果 pet_id 已存在，或年龄/体重/性别不合法
            TypeError: 如果年龄或体重不是数字
        
        示例：
            >>> system.register_pet("pet001", "小白", "金毛犬", 2, 25.5, "male")
            ✓ 成功注册宠物：小白 (金毛犬, 2岁, 25.5kg, 公)
        """
        # 创建宠物档案（PetProfile 内部会自动创建 DoublyLinkedList）
        pet = PetProfile(pet_id, name, breed, age, weight, gender, species)
        pet.health_timeline = DoublyLinkedList()  # 为每个宠物初始化健康时间线
        
        # 添加到哈希表
        self.profile_manager.add_pet(pet)
        
        print(f"[OK] 成功注册宠物：{pet}")
        
        # 【持久化】自动保存到文件
        self._save_to_file()
        
        return pet
    
    def add_health_record(self, pet_id: str, date: str, event_type: str, 
                          description: str, details: dict = None, 
                          severity: str = "low") -> bool:
        """
        为指定宠物添加健康记录
        
        时间复杂度：O(1) - 链表尾部追加
        空间复杂度：O(1) - 创建一个新的 HealthRecordNode
        
        Args:
            pet_id: 宠物 ID
            date: 日期字符串，格式 "YYYY-MM-DD"
            event_type: 事件类型，如 "vaccine" / "checkup" / "illness" / "feeding"
            description: 事件描述
            details: 详细信息字典（可选），如 {"hospital": "XX医院"}
            severity: 严重程度，"low" / "medium" / "high" / "critical"，默认 "low"
        
        Returns:
            bool: 成功添加返回 True，宠物不存在返回 False
        
        Raises:
            ValueError: 日期格式不正确或严重程度不合法
        
        示例：
            >>> system.add_health_record("pet001", "2026-04-15", "vaccine", 
            ...                          "接种狂犬疫苗", severity="medium")
            ✓ 已为 小白 添加健康记录：接种狂犬疫苗
        """
        # 查找宠物
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"[ERR] 错误：找不到宠物 ID '{pet_id}'")
            return False
        
        try:
            # 创建健康记录节点（HealthRecordNode 内部会校验日期格式）
            record = HealthRecordNode(date, event_type, description, severity, details)
        except ValueError as e:
            print(f"[ERR] 添加失败：{e}")
            return False
        
        # 添加到健康时间线
        pet.health_timeline.append(record)
        
        print(f"[OK] 已为 {pet.name} 添加健康记录：{description}")
        
        # 【持久化】自动保存到文件
        self._save_to_file()
        
        return True
    
    def view_recent_records(self, pet_id: str, count: int = 5) -> list:
        """
        查看最近 n 条健康记录（反向遍历）
        
        时间复杂度：O(count)
        空间复杂度：O(count) - 返回列表需要额外空间
        
        Args:
            pet_id: 宠物 ID
            count: 要查看的记录数量，默认 5
        
        Returns:
            list: 最近 count 条记录的字典列表（从新到旧）
                  如果宠物不存在，返回空列表 []
        
        示例：
            >>> system.view_recent_records("pet001", count=3)
            
            小白 的最近 3 条健康记录：
              1. [2026-04-15] checkup: 复查恢复良好
              2. [2026-04-01] feeding: 更换为低敏狗粮
              3. [2026-03-10] illness: 感冒发烧，服药治疗
        """
        # 查找宠物
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"[ERR] 错误：找不到宠物 ID '{pet_id}'")
            return []
        
        # 反向遍历获取最近记录
        records = pet.health_timeline.traverse_backward(count)
        
        # 打印结果
        print(f"\n{pet.name} 的最近 {len(records)} 条健康记录：")
        if not records:
            print("  暂无健康记录")
        else:
            severity_icon = {
                "low": "[L]",
                "medium": "[M]",
                "high": "[H]",
                "critical": "[C]"
            }
            
            for i, record in enumerate(records, 1):
                icon = severity_icon.get(record["severity"], "[?]")
                print(f"  {i}. {icon} [{record['date']}] {record['type']}: {record['desc']}")
        
        return records
    
    def view_full_timeline(self, pet_id: str) -> list:
        """
        查看完整健康时间线（正向遍历）
        
        时间复杂度：O(n) - n 为记录总数
        空间复杂度：O(n) - 返回列表需要额外空间
        
        Args:
            pet_id: 宠物 ID
        
        Returns:
            list: 完整记录字典列表（从早到晚）
                  如果宠物不存在，返回空列表 []
        
        示例：
            >>> system.view_full_timeline("pet001")
            
            小白 的完整健康时间线：
            健康时间线 (5 条记录):
            ============================================================
              1. 🟡 [2026-01-15] vaccine: 接种狂犬疫苗
              2. 🟢 [2026-02-20] checkup: 常规体检，体重正常
              ...
        """
        # 查找宠物
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"[ERR] 错误：找不到宠物 ID '{pet_id}'")
            return []
        
        # 打印时间线
        print(f"\n{pet.name} 的完整健康时间线：")
        print(pet.health_timeline)
        
        # 返回数据
        return pet.health_timeline.traverse_forward()
    
    def search_by_name(self, keyword: str) -> list:
        """
        按名字搜索宠物（支持模糊匹配）
        
        时间复杂度：O(n) - 需要遍历所有宠物
        空间复杂度：O(k) - k 为匹配的数量
        
        Args:
            keyword: 搜索关键词（支持部分匹配，不区分大小写）
        
        Returns:
            list: 匹配的 PetProfile 对象列表
        
        示例：
            >>> system.search_by_name("小")
            
            找到 2 只匹配的宠物：
              - 小白 (金毛犬, 2岁, 25.5kg, 公)
              - 小花 (布偶猫, 1岁, 4.2kg, 母)
        """
        results = self.profile_manager.search_by_name(keyword)
        
        # 打印结果
        if results:
            print(f"\n找到 {len(results)} 只匹配的宠物：")
            for pet in results:
                status_icon = {
                    "active": "[A]",
                    "inactive": "[I]",
                    "lost": "[L]"
                }.get(pet.status, "[?]")
                print(f"  {status_icon} {pet}")
        else:
            print(f"未找到名字包含 '{keyword}' 的宠物")
        
        return results
    
    def search_by_breed(self, keyword: str) -> list:
        """
        按品种搜索宠物（支持模糊匹配）
        
        时间复杂度：O(n) - 需要遍历所有宠物
        空间复杂度：O(k) - k 为匹配的数量
        
        Args:
            keyword: 品种关键词（支持部分匹配，不区分大小写）
        
        Returns:
            list: 匹配的 PetProfile 对象列表
        
        示例：
            >>> system.search_by_breed("猫")
            
            找到 2 只匹配的宠物：
              - 小花 (布偶猫, 1岁, 4.2kg, 母)
              - 咪咪 (英短蓝猫, 2岁, 5.8kg, 母)
        """
        results = self.profile_manager.search_by_breed(keyword)
        
        # 打印结果
        if results:
            print(f"\n找到 {len(results)} 只品种包含 '{keyword}' 的宠物：")
            for pet in results:
                status_icon = {
                    "active": "[A]",
                    "inactive": "[I]",
                    "lost": "[L]"
                }.get(pet.status, "[?]")
                print(f"  {status_icon} {pet.name} - {pet.breed}")
        else:
            print(f"未找到品种包含 '{keyword}' 的宠物")
        
        return results
    
    def update_pet_info(self, pet_id: str, **kwargs) -> bool:
        """
        更新宠物信息
        
        时间复杂度：O(1) - 哈希表查找 + 字段更新
        空间复杂度：O(1)
        
        Args:
            pet_id: 宠物 ID
            **kwargs: 要更新的字段和值，如 age=3, weight=28.0, status="active"
        
        Returns:
            bool: 成功更新返回 True，宠物不存在返回 False
        
        Raises:
            ValueError: 更新的值不合法（如负数年龄、非法性别）
            TypeError: age 或 weight 不是数字
            AttributeError: 字段名不存在
        
        示例：
            >>> system.update_pet_info("pet001", age=3, weight=28.0)
            ✓ 已更新宠物 小白 的信息
        """
        try:
            self.profile_manager.update_pet(pet_id, **kwargs)
            pet = self.profile_manager.get_pet(pet_id)
            print(f"[OK] 已更新宠物 {pet.name} 的信息")
            
            # 【持久化】自动保存到文件
            self._save_to_file()
            
            return True
        except ValueError as e:
            print(f"[ERR] 更新失败：{e}")
            return False
        except TypeError as e:
            print(f"[ERR] 更新失败：{e}")
            return False
        except AttributeError as e:
            print(f"[ERR] 更新失败：{e}")
            return False
    
    def remove_pet(self, pet_id: str) -> bool:
        """
        删除宠物及其健康记录
        
        时间复杂度：O(1) - 哈希表删除
        空间复杂度：O(1)
        
        Args:
            pet_id: 宠物 ID
        
        Returns:
            bool: 成功删除返回 True，宠物不存在返回 False
        
        注意：
            删除前会先清空健康时间线，显式释放资源
            这体现了工程严谨性，避免潜在内存泄漏
        
        示例：
            >>> system.remove_pet("pet001")
            ✓ 已删除宠物 小白 及其所有健康记录
        """
        # 查找宠物
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"[ERR] 错误：找不到宠物 ID '{pet_id}'")
            return False
        
        # 显式释放资源：清空健康时间线
        pet_name = pet.name
        if pet.health_timeline:
            pet.health_timeline.clear()
            pet.health_timeline = None
        
        # 从哈希表中删除
        self.profile_manager.remove_pet(pet_id)
        
        print(f"[OK] 已删除宠物 {pet_name} 及其所有健康记录")
        
        # 【持久化】自动保存到文件
        self._save_to_file()
        
        return True
    
    def save_medical_record(self, pet_id: str, extraction_data: dict, image_path: str) -> bool:
        """
        API-004: 保存医疗记录到健康时间线
        
        Args:
            pet_id: 宠物 ID
            extraction_data: 提取的结构化数据 (diagnosis, medicines, etc.)
            image_path: 原始病历图片路径
            
        Returns:
            bool: 成功返回 True
        """
        # 1. 校验宠物是否存在
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            raise ValueError(f"Cannot save record for unregistered pet: {pet_id}")
        
        diagnosis = extraction_data.get('diagnosis', '未知诊断')
        
        # 2. 创建 HealthRecordNode
        record = HealthRecordNode(
            date=datetime.now().strftime("%Y-%m-%d"),
            event_type="medical_record",
            description=f"诊断: {diagnosis}",
            severity="high",
            details={
                "image_path": image_path,
                "extraction_data": extraction_data
            }
        )
        
        # 3. 存入双向链表
        pet.health_timeline.append(record)
        print(f"[OK] 已为 {pet.name} 归档医疗记录: {diagnosis}")
        
        # 4. 触发持久化
        self._save_to_file()
        return True

    def filter_medical_records(self, pet_name: str = None, pet_id: str = None, 
                               start_date: str = None, end_date: str = None) -> list:
        """
        API-001: 筛选医疗记录
        
        根据宠物名称、ID 及日期范围组合筛选健康时间线中的病历节点。
        
        Args:
            pet_name: 宠物姓名关键词（模糊匹配）
            pet_id: 宠物唯一标识（精确匹配）
            start_date: 筛选起始日期 (YYYY-MM-DD)
            end_date: 筛选结束日期 (YYYY-MM-DD)
            
        Returns:
            list[dict]: 包含 MedicalRecordView 对象的列表，按时间倒序排列。
            
        Raises:
            ValueError: 日期格式不正确或结束日期早于起始日期。
        """
        # 1. 参数校验
        if not any([pet_name, pet_id, start_date, end_date]):
            raise ValueError("请输入至少一个筛选条件")
        
        # 2. 确定目标宠物集合
        target_pets = []
        if pet_id:
            pet = self.profile_manager.get_pet(pet_id)
            if pet: 
                target_pets.append(pet)
        elif pet_name:
            target_pets = self.profile_manager.search_by_name(pet_name)
        else:
            target_pets = self.profile_manager.get_all_pets()
            
        # 3. 遍历并过滤记录
        results = []
        for pet in target_pets:
            records = pet.health_timeline.traverse_forward()
            for record in records:
                # 3.1 日期过滤
                if start_date and record['date'] < start_date: 
                    continue
                if end_date and record['date'] > end_date: 
                    continue
                
                # 3.2 构造视图对象
                results.append({
                    "pet_name": pet.name,
                    "date": record['date'],
                    "event_type": record['type'],
                    "description": record['desc']
                })
                
        # 4. 排序（时间倒序）并返回
        return sorted(results, key=lambda x: x['date'], reverse=True)

    def show_all_pets(self) -> list:
        """
        显示所有宠物档案
        
        时间复杂度：O(n)
        空间复杂度：O(n) - 返回列表需要额外空间
        
        Returns:
            list: 所有 PetProfile 对象列表
        
        示例：
            >>> system.show_all_pets()
            
            宠物档案列表 (3 只):
            ============================================================
              🟢 ID: pet001 | 小白 (金毛犬, 2岁, 25.5kg, 公)
              🟢 ID: pet002 | 小花 (布偶猫, 1岁, 4.2kg, 母)
              ...
        """
        print(f"\n{self.profile_manager}")
        return self.profile_manager.get_all_pets()
    
    def get_pet_count(self) -> int:
        """
        获取宠物总数
        
        时间复杂度：O(1)
        
        Returns:
            int: 宠物数量
        """
        return self.profile_manager.get_pet_count()
    
    # ==================== 【持久化】核心方法 ====================
    
    def _save_to_file(self):
        """
        将当前所有宠物档案保存到 JSON 文件
        
        设计原则：
        - 无感同步：自动调用，用户无需手动保存
        - 健壮性：捕获 I/O 错误，防止程序崩溃
        - 结构还原：确保双向链表健康记录正确序列化
        
        时间复杂度：O(n) - n 为宠物数量
        空间复杂度：O(n) - 需要构建完整的字典结构
        """
        try:
            # 确保数据目录存在
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            # 序列化所有宠物数据
            pets_data = []
            for pet in self.profile_manager.get_all_pets():
                # 构建宠物字典
                pet_dict = {
                    'pet_id': pet.pet_id,
                    'name': pet.name,
                    'breed': pet.breed,
                    'age': pet.age,
                    'weight': pet.weight,
                    'gender': pet.gender,
                    'species': pet.species,
                    'health_records': []
                }
                
                # 序列化健康记录（双向链表 -> 列表）
                if pet.health_timeline:
                    records = pet.health_timeline.traverse_forward()
                    for record in records:
                        pet_dict['health_records'].append({
                            'date': record['date'],
                            'type': record['type'],
                            'desc': record['desc'],
                            'severity': record['severity'],
                            'details': record.get('details', {})
                        })
                
                pets_data.append(pet_dict)
            
            # 写入 JSON 文件（使用 utf-8 编码和美化格式）
            with open(PETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(pets_data, f, ensure_ascii=False, indent=2)
            
            # print(f"[持久化] ✅ 已保存 {len(pets_data)} 只宠物到 {PETS_FILE}")
            
        except IOError as e:
            print(f"[持久化] ⚠️ 保存失败: {e}")
        except Exception as e:
            print(f"[持久化] ⚠️ 未知错误: {e}")
    
    def _load_from_file(self):
        """
        从 JSON 文件加载历史宠物档案
        
        设计原则：
        - 零侵入性：在 __init__ 中自动调用，不影响外部逻辑
        - 结构还原：将 JSON 数据还原为 PetProfile 对象和 DoublyLinkedList
        - 容错性：文件不存在时静默跳过，不报错
        
        时间复杂度：O(n*m) - n 为宠物数量，m 为每只宠物的平均记录数
        空间复杂度：O(n*m) - 需要重建所有对象
        """
        try:
            # 检查文件是否存在
            if not PETS_FILE.exists():
                # print("[持久化] 📝 未找到历史数据文件，初始化空系统")
                return
            
            # 读取 JSON 文件
            with open(PETS_FILE, 'r', encoding='utf-8') as f:
                pets_data = json.load(f)
            
            if not pets_data:
                # print("[持久化] 📝 历史数据为空，初始化空系统")
                return
            
            # 重建宠物档案
            loaded_count = 0
            for pet_dict in pets_data:
                try:
                    # 创建 PetProfile 对象
                    pet = PetProfile(
                        pet_id=pet_dict['pet_id'],
                        name=pet_dict['name'],
                        breed=pet_dict['breed'],
                        age=pet_dict['age'],
                        weight=pet_dict['weight'],
                        gender=pet_dict.get('gender', 'unknown'),
                        species=pet_dict.get('species', 'dog')
                    )
                    
                    # 初始化健康时间线
                    pet.health_timeline = DoublyLinkedList()
                    
                    # 重建健康记录（列表 -> 双向链表）
                    for record_dict in pet_dict.get('health_records', []):
                        record = HealthRecordNode(
                            date=record_dict['date'],
                            event_type=record_dict['type'],
                            description=record_dict['desc'],
                            severity=record_dict.get('severity', 'low'),
                            details=record_dict.get('details', {})
                        )
                        pet.health_timeline.append(record)
                    
                    # 添加到哈希表
                    self.profile_manager.add_pet(pet)
                    loaded_count += 1
                    
                except Exception as e:
                    print(f"[持久化] ⚠️ 加载宠物 {pet_dict.get('pet_id', 'unknown')} 失败: {e}")
                    continue
            
            if loaded_count > 0:
                print(f"[持久化] ✅ 已加载 {loaded_count} 只宠物的历史数据")
            
        except FileNotFoundError:
            # 文件不存在是正常情况，静默处理
            pass
        except json.JSONDecodeError as e:
            print(f"[持久化] ⚠️ JSON 文件格式错误: {e}")
        except Exception as e:
            print(f"[持久化] ⚠️ 加载失败: {e}")


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  宠物档案管理模块测试")
    print("=" * 60)
    
    # 创建系统
    system = SmartPetProfileSystem()
    print("\n【测试1】注册新宠物")
    
    pet1 = system.register_pet("pet001", "小白", "金毛犬", 2, 25.5, "male")
    pet2 = system.register_pet("pet002", "小花", "布偶猫", 1, 4.2, "female")
    pet3 = system.register_pet("pet003", "旺财", "中华田园犬", 3, 15.0, "male")
    
    print(f"\n当前宠物数量: {system.get_pet_count()}")
    
    # 添加健康记录
    print("\n【测试2】添加健康记录")
    
    # 小白的健康记录
    system.add_health_record("pet001", "2026-01-15", "vaccine", "接种狂犬疫苗", 
                            {"hospital": "爱心宠物医院", "vet_name": "张医生"}, "medium")
    system.add_health_record("pet001", "2026-02-20", "checkup", "常规体检，体重正常", 
                            {"weight": "25.5kg"}, "low")
    system.add_health_record("pet001", "2026-03-10", "illness", "感冒发烧，服药治疗", 
                            {"medicine": "宠物感冒灵"}, "high")
    system.add_health_record("pet001", "2026-04-01", "feeding", "更换为低敏狗粮", 
                            {"brand": "皇家低敏粮"}, "low")
    system.add_health_record("pet001", "2026-04-15", "checkup", "复查恢复良好", 
                            {"vet_name": "李医生"}, "low")
    
    # 小花的健康记录
    system.add_health_record("pet002", "2026-03-01", "vaccine", "接种猫三联疫苗", 
                            severity="medium")
    system.add_health_record("pet002", "2026-04-10", "checkup", "常规体检", 
                            severity="low")
    
    # 测试不存在的宠物
    system.add_health_record("pet999", "2026-04-15", "test", "测试")
    
    # 查看最近记录
    print("\n【测试3】查看最近健康记录")
    system.view_recent_records("pet001", count=3)
    
    # 测试空时间线
    print("\n【测试4】查看空时间线")
    system.view_recent_records("pet003")
    
    # 查看完整时间线
    print("\n【测试5】查看完整健康时间线")
    system.view_full_timeline("pet001")
    
    # 搜索宠物
    print("\n【测试6】搜索宠物")
    
    # 按名字搜索
    print("\n--- 按名字搜索 ---")
    system.search_by_name("小")
    
    # 按品种搜索
    print("\n--- 按品种搜索 ---")
    system.search_by_breed("猫")
    
    # 搜索无结果
    print("\n--- 搜索无结果 ---")
    system.search_by_name("不存在的名字")
    
    # 更新宠物信息
    print("\n【测试7】更新宠物信息")
    system.update_pet_info("pet001", age=3, weight=28.0)
    
    # 测试更新失败（不存在的宠物）
    system.update_pet_info("pet999", age=5)
    
    # 测试更新失败（非法值）
    system.update_pet_info("pet001", age=-1)
    
    # 显示所有宠物
    print("\n【测试8】显示所有宠物")
    system.show_all_pets()
    
    # 删除宠物
    print("\n【测试9】删除宠物")
    
    # 先查看旺财是否有记录
    system.view_recent_records("pet003")
    
    # 删除旺财
    system.remove_pet("pet003")
    
    # 验证删除成功
    print(f"\n删除后宠物数量: {system.get_pet_count()}")
    system.show_all_pets()
    
    # 测试删除不存在的宠物
    system.remove_pet("pet999")
    
    # 边界情况测试
    print("\n【测试10】边界情况测试")
    
    # 重复注册
    try:
        system.register_pet("pet001", "重复", "测试", 1, 1.0)
        print("✗ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 重复 ID 校验成功: {e}")
    
    # 日期格式错误
    result = system.add_health_record("pet001", "2026/13/45", "test", "测试")
    print(f"{'✓' if not result else '✗'} 日期格式校验成功")
    
    # 严重程度错误
    try:
        result = system.add_health_record("pet001", "2026-04-16", "test", "测试", 
                                         severity="invalid")
        print(f"{'✓' if not result else '✗'} 严重程度校验成功")
    except ValueError:
        print("✓ 严重程度校验成功")
    
    print("\n" + "=" * 60)
    print("  所有测试完成！✅")
    print("=" * 60)
