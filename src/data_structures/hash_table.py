"""
哈希表封装 - 用于快速检索宠物档案

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

数据结构选型理由：
- 通过 pet_id 查询是最高频操作，哈希表 O(1) 最优
- 支持动态增删，比数组灵活
- 简单高效，适合小规模数据（个人用户通常 1-5 只宠物）

技术说明：
- Python 的 dict 底层就是哈希表实现
- 提供 O(1) 的查找、插入、删除效率
- 冲突解决：Python dict 使用开放寻址法 + 伪随机探测

---
【档案柜】
核心作用：定义了宠物的基本样子（PetProfile）以及如何快速找到它们（PetProfileManager）。
数据结构：哈希表 (Hash Table)。
为什么用它：当你输入 pet001 时，它能瞬间（O(1) 复杂度）告诉你这只宠物的名字、年龄、体重以及它是猫还是狗（species 字段）。
关键改动：最近我们给它增加了 species 字段，让它能区分“猫咪”和“狗狗”，为后续的细分赛道做准备。

"""

from datetime import datetime


class PetProfile:
    """宠物档案类"""
    
    def __init__(self, pet_id, name, breed, age, weight, gender="unknown", species="unknown"):
        """
        初始化宠物档案
        
        Args:
            pet_id: 宠物唯一 ID（哈希表的 key）
            name: 宠物名字
            breed: 品种
            age: 年龄（岁）
            weight: 体重（公斤）
            gender: 性别，"male" / "female" / "unknown"，默认 "unknown"
            species: 物种，"cat" (猫咪) / "dog" (狗狗) / "other" (其他)，默认 "unknown"
        
        Raises:
            ValueError: 年龄或体重为负数时抛出
            ValueError: 性别取值不合法时抛出
            ValueError: 物种取值不合法时抛出
        """
        # 类型检查
        if not isinstance(age, (int, float)):
            raise TypeError(f"年龄必须是数字，收到 {type(age).__name__}")
        if not isinstance(weight, (int, float)):
            raise TypeError(f"体重必须是数字，收到 {type(weight).__name__}")
        
        # 数据校验
        if age < 0:
            raise ValueError(f"年龄不能为负数：{age}")
        if weight < 0:
            raise ValueError(f"体重不能为负数：{weight}")
        
        valid_genders = ["male", "female", "unknown"]
        if gender not in valid_genders:
            raise ValueError(f"性别错误：'{gender}'，必须是 {valid_genders} 之一")
        
        valid_species = ["cat", "dog", "other", "unknown"]
        if species not in valid_species:
            raise ValueError(f"物种错误：'{species}'，必须是 {valid_species} 之一")
        
        self.pet_id = pet_id
        self.name = name
        self.breed = breed
        self.age = age
        self.weight = weight
        self.gender = gender
        self.species = species
        
        # 扩展字段
        self.allergies = []                    # 过敏源列表
        self.medications = []                  # 药物清单
        self.health_timeline = None            # 关联的健康时间线（DoublyLinkedList）
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 创建时间
        self.status = "active"                 # 状态："active" / "inactive" / "lost"
    
    def __str__(self):
        """字符串表示：名字 (品种, 物种, 年龄岁, 体重kg, 性别)"""
        gender_map = {"male": "公", "female": "母", "unknown": "未知"}
        species_map = {"cat": "猫", "dog": "狗", "other": "其他", "unknown": "未知"}
        gender_str = gender_map.get(self.gender, "未知")
        species_str = species_map.get(self.species, "未知")
        return f"{self.name} ({self.breed}, {species_str}, {self.age}岁, {self.weight}kg, {gender_str})"
    
    def __repr__(self):
        """详细表示（用于调试）"""
        return (f"PetProfile(id={self.pet_id}, name={self.name}, breed={self.breed}, "
                f"age={self.age}, weight={self.weight}, gender={self.gender}, "
                f"status={self.status})")


class PetProfileManager:
    """
    宠物档案管理器（基于字典实现的哈希表）
    
    Python 的 dict 底层就是哈希表实现，提供 O(1) 的查找效率
    
    哈希表特性：
    - 插入：O(1) 平均时间复杂度
    - 查找：O(1) 平均时间复杂度
    - 删除：O(1) 平均时间复杂度
    - 最坏情况：O(n) 当发生大量哈希冲突时（但 Python dict 优化很好，极少出现）
    """
    
    def __init__(self):
        """初始化空的宠物档案管理器"""
        self.profiles = {}  # {pet_id: PetProfile} 哈希表
    
    def add_pet(self, pet_profile):
        """
        添加宠物档案
        
        时间复杂度：O(1) 平均情况
        空间复杂度：O(1)
        
        Args:
            pet_profile: PetProfile 对象
        
        Raises:
            TypeError: 如果传入的不是 PetProfile 对象
            ValueError: 如果 pet_id 已存在
        """
        if not isinstance(pet_profile, PetProfile):
            raise TypeError(f"必须传入 PetProfile 对象，收到 {type(pet_profile).__name__}")
        
        if pet_profile.pet_id in self.profiles:
            raise ValueError(f"宠物 ID '{pet_profile.pet_id}' 已存在")
        
        self.profiles[pet_profile.pet_id] = pet_profile
    
    def get_pet(self, pet_id):
        """
        快速获取宠物档案
        
        时间复杂度：O(1) 平均情况
        
        Args:
            pet_id: 宠物 ID
        
        Returns:
            PetProfile 对象或 None（如果不存在）
        """
        return self.profiles.get(pet_id)
    
    def remove_pet(self, pet_id):
        """
        删除宠物档案
        
        时间复杂度：O(1) 平均情况
        
        Args:
            pet_id: 宠物 ID
        
        Returns:
            bool: 成功删除返回 True，未找到返回 False
        """
        if pet_id in self.profiles:
            del self.profiles[pet_id]
            return True
        return False
    
    def update_pet(self, pet_id, **kwargs):
        """
        更新宠物信息（如年龄、体重变化）
        
        时间复杂度：O(1) 平均情况（查找） + O(k)（更新 k 个字段）
        
        Args:
            pet_id: 宠物 ID
            **kwargs: 要更新的字段和值，如 age=3, weight=5.5
        
        Raises:
            ValueError: 如果 pet_id 不存在
            AttributeError: 如果字段名不存在
        
        示例：
            >>> manager.update_pet("pet001", age=3, weight=5.5)
            >>> manager.update_pet("pet001", status="inactive")
        """
        pet = self.get_pet(pet_id)
        if not pet:
            raise ValueError(f"宠物 ID '{pet_id}' 不存在")
        
        for key, value in kwargs.items():
            if hasattr(pet, key):
                # 类型检查
                if key in ["age", "weight"] and not isinstance(value, (int, float)):
                    raise TypeError(f"{key} 必须是数字，收到 {type(value).__name__}")
                
                # 特殊字段校验
                if key == "age" and value < 0:
                    raise ValueError(f"年龄不能为负数：{value}")
                if key == "weight" and value < 0:
                    raise ValueError(f"体重不能为负数：{value}")
                if key == "gender" and value not in ["male", "female", "unknown"]:
                    raise ValueError(f"性别错误：'{value}'")
                if key == "status" and value not in ["active", "inactive", "lost"]:
                    raise ValueError(f"状态错误：'{value}'")
                
                setattr(pet, key, value)
            else:
                raise AttributeError(f"宠物档案没有 '{key}' 字段")
    
    def get_all_pets(self):
        """
        获取所有宠物档案
        
        时间复杂度：O(n)
        空间复杂度：O(n) - 返回列表需要额外空间
        
        Returns:
            list: PetProfile 对象列表
        """
        return list(self.profiles.values())
    
    def search_by_name(self, name):
        """
        按名字搜索宠物（支持模糊匹配）
        
        时间复杂度：O(n) - 需要遍历所有宠物
        空间复杂度：O(k) - k 为匹配的数量
        
        Args:
            name: 宠物名字（支持部分匹配，不区分大小写）
        
        Returns:
            list: 匹配的 PetProfile 对象列表
        
        示例：
            >>> manager.search_by_name("小")  # 匹配 "小白", "小花"
            >>> manager.search_by_name("bai")  # 匹配 "小白", "Bailey"
        """
        results = []
        name_lower = name.lower()
        
        for pet in self.profiles.values():
            if name_lower in pet.name.lower():
                results.append(pet)
        
        return results
    
    def search_by_breed(self, breed):
        """
        按品种搜索宠物（支持模糊匹配）
        
        时间复杂度：O(n)
        空间复杂度：O(k) - k 为匹配的数量
        
        Args:
            breed: 品种名称（支持部分匹配，不区分大小写）
        
        Returns:
            list: 匹配的 PetProfile 对象列表
        
        示例：
            >>> manager.search_by_breed("金毛")  # 匹配 "金毛犬", "金毛寻回犬"
        """
        results = []
        breed_lower = breed.lower()
        
        for pet in self.profiles.values():
            if breed_lower in pet.breed.lower():
                results.append(pet)
        
        return results
    
    def get_active_pets(self):
        """
        获取所有状态为 "active" 的宠物
        
        时间复杂度：O(n)
        空间复杂度：O(k) - k 为活跃宠物数量
        
        Returns:
            list: 活跃的 PetProfile 对象列表
        """
        return [pet for pet in self.profiles.values() if pet.status == "active"]
    
    def get_pet_count(self):
        """
        获取宠物数量
        
        时间复杂度：O(1)
        
        Returns:
            int: 宠物总数
        """
        return len(self.profiles)
    
    def is_empty(self):
        """
        判断是否为空
        
        时间复杂度：O(1)
        
        Returns:
            bool: 空返回 True，否则返回 False
        """
        return len(self.profiles) == 0
    
    def clear(self):
        """
        清空所有宠物档案
        
        时间复杂度：O(1)
        """
        self.profiles.clear()
    
    def __str__(self):
        """
        字符串表示 - 格式化输出所有宠物
        
        Returns:
            str: 格式化的宠物列表
        """
        if self.is_empty():
            return "暂无宠物档案"
        
        lines = [f"宠物档案列表 ({self.get_pet_count()} 只):"]
        lines.append("=" * 60)
        
        for pet in self.profiles.values():
            status_icon = {
                "active": "[A]",
                "inactive": "[I]",
                "lost": "[L]"
            }.get(pet.status, "[?]")
            
            lines.append(f"  {status_icon} ID: {pet.pet_id} | {pet}")
        
        return "\n".join(lines)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  哈希表测试 - 宠物档案管理")
    print("=" * 60)
    
    # 创建管理器
    manager = PetProfileManager()
    print("\n【测试1】创建空管理器")
    print(f"宠物数量: {manager.get_pet_count()}")
    print(f"是否为空: {manager.is_empty()}")
    print(manager)
    
    # 添加宠物
    print("\n【测试2】添加宠物档案")
    pets_data = [
        ("pet001", "小白", "金毛犬", 2, 25.5, "male"),
        ("pet002", "小花", "布偶猫", 1, 4.2, "female"),
        ("pet003", "旺财", "中华田园犬", 3, 15.0, "male"),
        ("pet004", "咪咪", "英短蓝猫", 2, 5.8, "female"),
    ]
    
    for pet_id, name, breed, age, weight, gender in pets_data:
        pet = PetProfile(pet_id, name, breed, age, weight, gender)
        manager.add_pet(pet)
        print(f"✓ 已添加: {pet}")
    
    print(f"\n宠物数量: {manager.get_pet_count()}")
    print(manager)
    
    # 获取宠物
    print("\n【测试3】获取宠物（O(1) 查找）")
    pet = manager.get_pet("pet001")
    if pet:
        print(f"✓ 找到 pet001: {pet}")
        print(f"  创建时间: {pet.created_at}")
        print(f"  状态: {pet.status}")
    
    # 测试不存在的 ID
    missing_pet = manager.get_pet("pet999")
    print(f"✗ pet999 不存在: {missing_pet}")
    
    # 更新宠物
    print("\n【测试4】更新宠物信息")
    print(f"更新前 - 小白: {manager.get_pet('pet001')}")
    manager.update_pet("pet001", age=3, weight=28.0)
    print(f"更新后 - 小白: {manager.get_pet('pet001')}")
    
    # 测试更新不存在的字段
    try:
        manager.update_pet("pet001", invalid_field="test")
        print("✗ 应该抛出 AttributeError")
    except AttributeError as e:
        print(f"✓ 字段校验成功: {e}")
    
    # 搜索功能
    print("\n【测试5】搜索功能测试")
    
    # 按名字搜索
    name_results = manager.search_by_name("小")
    print(f"\n按名字搜索 '小': 找到 {len(name_results)} 只")
    for pet in name_results:
        print(f"  - {pet.name}")
    
    # 按品种搜索
    breed_results = manager.search_by_breed("猫")
    print(f"\n按品种搜索 '猫': 找到 {len(breed_results)} 只")
    for pet in breed_results:
        print(f"  - {pet.name} ({pet.breed})")
    
    # 获取所有宠物
    print(f"\n【测试6】获取所有宠物")
    all_pets = manager.get_all_pets()
    print(f"总数: {len(all_pets)} 只")
    
    # 删除宠物
    print("\n【测试7】删除宠物")
    print(f"删除前数量: {manager.get_pet_count()}")
    success = manager.remove_pet("pet003")
    print(f"删除 pet003: {'✓ 成功' if success else '✗ 失败'}")
    print(f"删除后数量: {manager.get_pet_count()}")
    
    # 测试删除不存在的 ID
    result = manager.remove_pet("pet999")
    print(f"删除 pet999: {'✗ 正确返回 False' if not result else '✓ 错误'}")
    
    # 状态管理
    print("\n【测试8】状态管理测试")
    manager.update_pet("pet002", status="inactive")
    print(f"小花状态已更新为: {manager.get_pet('pet002').status}")
    
    active_pets = manager.get_active_pets()
    print(f"活跃宠物数量: {len(active_pets)}")
    for pet in active_pets:
        print(f"  - {pet.name} ({pet.status})")
    
    # 边界情况测试
    print("\n【测试9】边界情况测试")
    
    # 添加重复 ID
    try:
        duplicate_pet = PetProfile("pet001", "重复", "测试", 1, 1.0)
        manager.add_pet(duplicate_pet)
        print("✗ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 重复 ID 校验成功: {e}")
    
    # 类型校验
    try:
        manager.add_pet("不是 PetProfile 对象")
        print("✗ 应该抛出 TypeError")
    except TypeError as e:
        print(f"✓ 类型校验成功: {e}")
    
    # 负数年龄/体重校验
    try:
        bad_pet = PetProfile("pet_bad", "测试", "测试", -1, 5.0)
        print("✗ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 年龄校验成功: {e}")
    
    try:
        bad_pet = PetProfile("pet_bad", "测试", "测试", 1, -5.0)
        print("✗ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 体重校验成功: {e}")
    
    # 性别校验
    try:
        bad_pet = PetProfile("pet_bad", "测试", "测试", 1, 5.0, "invalid")
        print("✗ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 性别校验成功: {e}")
    
    # 更新负数年龄
    try:
        manager.update_pet("pet001", age=-5)
        print("✗ 应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 更新年龄校验成功: {e}")
    
    # 清空测试
    print("\n【测试10】清空管理器")
    manager.clear()
    print(f"清空后数量: {manager.get_pet_count()}")
    print(f"是否为空: {manager.is_empty()}")
    print(manager)
    
    print("\n" + "=" * 60)
    print("  所有测试完成！✅")
    print("=" * 60)
