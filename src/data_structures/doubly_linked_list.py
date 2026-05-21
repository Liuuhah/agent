"""
双向链表实现 - 用于存储宠物健康记录时间线

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

数据结构选型理由：
- 健康记录是时序数据，需要前后遍历
- 新记录频繁添加到尾部，链表O(1)优于数组O(n)
- 反向遍历查看最近记录是高频操作
- 支持动态插入和删除，比数组灵活

---
【病历本】
核心作用：记录每一只宠物的健康历史（疫苗、体检、生病等）。
数据结构：双向链表 (Doubly Linked List)。
为什么用它：
时间顺序：病历是按时间发生的，链表天然适合这种前后相连的关系。
反向查看：医生（用户）通常最关心“最近几次”的情况，双向链表可以从后往前翻（traverse_backward），效率极高。

"""

import re
import uuid
from datetime import datetime


class HealthRecordNode:
    """健康记录节点类"""
    
    def __init__(self, date, event_type, description, severity="low", details=None):
        """
        初始化健康记录节点
        
        Args:
            date: 日期字符串，格式必须为 "YYYY-MM-DD"
            event_type: 事件类型，如 "vaccine"（疫苗）/ "checkup"（体检）/ "illness"（生病）/ "feeding"（喂食）
            description: 事件描述
            severity: 严重程度，"low" / "medium" / "high" / "critical"，默认 "low"
            details: 详细信息字典（可选），如 {"hospital": "XX宠物医院", "vet_name": "张医生"}
        
        Raises:
            ValueError: 日期格式不正确时抛出
        """
        # 日期格式校验
        if not self._validate_date(date):
            raise ValueError(f"日期格式错误：'{date}'，必须为 'YYYY-MM-DD' 格式")
        
        # 严重程度校验
        valid_severities = ["low", "medium", "high", "critical"]
        if severity not in valid_severities:
            raise ValueError(f"严重程度错误：'{severity}'，必须是 {valid_severities} 之一")
        
        self.record_id = str(uuid.uuid4())[:8]  # 生成8位唯一标识
        self.date = date
        self.event_type = event_type
        self.description = description
        self.severity = severity
        # 使用 copy() 避免多个节点共享同一个字典对象（边界情况处理）
        self.details = details.copy() if details else {}
        self.prev = None  # 前驱指针
        self.next = None  # 后继指针
    
    @staticmethod
    def _validate_date(date_str):
        """
        校验日期格式是否为 YYYY-MM-DD
        
        Args:
            date_str: 日期字符串
        
        Returns:
            bool: 格式正确返回 True，否则返回 False
        """
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        
        # 进一步校验日期是否合法（如 2026-13-45 是不合法的）
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def __str__(self):
        """字符串表示：[日期] 类型: 描述 (严重程度)"""
        return f"[{self.date}] {self.event_type}: {self.description} ({self.severity})"
    
    def __repr__(self):
        """详细表示（用于调试）"""
        return (f"HealthRecordNode(id={self.record_id}, date={self.date}, "
                f"type={self.event_type}, severity={self.severity})")


class DoublyLinkedList:
    """双向链表实现 - 宠物健康记录时间线"""
    
    def __init__(self):
        """初始化空链表"""
        self.head = None   # 头节点（最早的记录）
        self.tail = None   # 尾节点（最新的记录）
        self.size = 0      # 链表大小
    
    def append(self, node):
        """
        在尾部添加节点（添加最新记录）
        
        时间复杂度：O(1)
        空间复杂度：O(1)
        
        Args:
            node: HealthRecordNode 对象
        
        Raises:
            TypeError: 如果传入的不是 HealthRecordNode 对象
        """
        if not isinstance(node, HealthRecordNode):
            raise TypeError(f"必须传入 HealthRecordNode 对象，收到 {type(node).__name__}")
        
        if not self.head:
            # 空链表：新节点既是头也是尾
            self.head = self.tail = node
        else:
            # 非空链表：添加到尾部
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        
        self.size += 1
    
    def traverse_forward(self):
        """
        从前向后遍历（时间正序：从早到晚）
        
        时间复杂度：O(n)
        空间复杂度：O(n) - 返回列表需要额外空间
        
        Returns:
            list: 包含所有记录字典的列表
                  [{"date": ..., "type": ..., "desc": ..., "severity": ..., "details": ...}, ...]
        
        边界情况处理：
        - 空链表：返回空列表 []
        - 防死循环保护：最大迭代次数 size * 2
        """
        records = []
        current = self.head
        max_iterations = self.size * 2  # 防死循环保护
        iterations = 0
        
        while current and iterations < max_iterations:
            records.append({
                "record_id": current.record_id,
                "date": current.date,
                "type": current.event_type,
                "desc": current.description,
                "severity": current.severity,
                "details": current.details
            })
            current = current.next
            iterations += 1
        
        return records
    
    def traverse_backward(self, count=5):
        """
        从后向前遍历 N 个节点（查看最近记录）
        
        时间复杂度：O(count)
        空间复杂度：O(count)
        
        Args:
            count: 要获取的记录数量，默认 5
        
        Returns:
            list: 最近 count 条记录的字典列表（从新到旧）
        
        边界情况处理：
        - 空链表：返回空列表 []
        - count > 链表长度：返回全部记录，不报错
        - count <= 0：返回空列表
        """
        if count <= 0:
            return []
        
        records = []
        current = self.tail
        
        while current and len(records) < count:
            records.append({
                "record_id": current.record_id,
                "date": current.date,
                "type": current.event_type,
                "desc": current.description,
                "severity": current.severity,
                "details": current.details
            })
            current = current.prev
        
        return records
    
    def delete_by_record_id(self, record_id):
        """
        删除指定 record_id 的记录
        
        时间复杂度：O(n) - 需要遍历查找
        空间复杂度：O(1)
        
        Args:
            record_id: 要删除的记录唯一标识
        
        Returns:
            bool: 成功删除返回 True，未找到返回 False
        
        边界情况处理：
        - 删除头节点：更新 self.head
        - 删除尾节点：更新 self.tail
        - 删除唯一节点：self.head = self.tail = None
        - 未找到 record_id：返回 False
        """
        current = self.head
        
        while current:
            if current.record_id == record_id:
                # 找到要删除的节点，调整指针
                
                # 调整前驱节点的 next 指针
                if current.prev:
                    current.prev.next = current.next
                else:
                    # 删除的是头节点
                    self.head = current.next
                
                # 调整后继节点的 prev 指针
                if current.next:
                    current.next.prev = current.prev
                else:
                    # 删除的是尾节点
                    self.tail = current.prev
                
                # 如果是唯一节点，删除后 head 和 tail 都应为 None
                if self.size == 1:
                    self.head = None
                    self.tail = None
                
                self.size -= 1
                return True
            
            current = current.next
        
        # 未找到
        return False
    
    def find_by_date(self, date):
        """
        查找指定日期的所有记录
        
        时间复杂度：O(n)
        空间复杂度：O(k) - k 为匹配的记录数
        
        Args:
            date: 日期字符串 "YYYY-MM-DD"
        
        Returns:
            list: 匹配的记录字典列表（可能有多条）
        """
        results = []
        current = self.head
        
        while current:
            if current.date == date:
                results.append({
                    "record_id": current.record_id,
                    "date": current.date,
                    "type": current.event_type,
                    "desc": current.description,
                    "severity": current.severity,
                    "details": current.details
                })
            current = current.next
        
        return results
    
    def find_by_type(self, event_type):
        """
        查找某类型的所有记录（如查看所有疫苗记录）
        
        时间复杂度：O(n)
        空间复杂度：O(k) - k 为匹配的记录数
        
        Args:
            event_type: 事件类型，如 "vaccine" / "checkup" / "illness" / "feeding"
        
        Returns:
            list: 匹配的记录字典列表
        """
        results = []
        current = self.head
        
        while current:
            if current.event_type == event_type:
                results.append({
                    "record_id": current.record_id,
                    "date": current.date,
                    "type": current.event_type,
                    "desc": current.description,
                    "severity": current.severity,
                    "details": current.details
                })
            current = current.next
        
        return results
    
    def find_by_date_range(self, start_date, end_date):
        """
        查找某个时间段内的记录（如最近一个月的体检记录）
        
        时间复杂度：O(n)
        空间复杂度：O(k) - k 为匹配的记录数
        
        Args:
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"
        
        Returns:
            list: 在时间段内的记录字典列表（按时间正序）
        """
        results = []
        current = self.head
        
        while current:
            # 字符串比较即可（YYYY-MM-DD 格式支持字典序比较）
            if start_date <= current.date <= end_date:
                results.append({
                    "record_id": current.record_id,
                    "date": current.date,
                    "type": current.event_type,
                    "desc": current.description,
                    "severity": current.severity,
                    "details": current.details
                })
            current = current.next
        
        return results
    
    def find_by_severity(self, severity_level):
        """
        查找特定严重程度的记录（如查看紧急就医记录）
        
        时间复杂度：O(n)
        空间复杂度：O(k) - k 为匹配的记录数
        
        Args:
            severity_level: 严重程度，"low" / "medium" / "high" / "critical"
        
        Returns:
            list: 匹配的记录字典列表
        """
        results = []
        current = self.head
        
        while current:
            if current.severity == severity_level:
                results.append({
                    "record_id": current.record_id,
                    "date": current.date,
                    "type": current.event_type,
                    "desc": current.description,
                    "severity": current.severity,
                    "details": current.details
                })
            current = current.next
        
        return results
    
    def is_empty(self):
        """
        判断链表是否为空
        
        时间复杂度：O(1)
        
        Returns:
            bool: 空返回 True，否则返回 False
        """
        return self.size == 0
    
    def get_size(self):
        """
        获取链表大小（记录数量）
        
        时间复杂度：O(1)
        
        Returns:
            int: 链表中的节点数量
        """
        return self.size
    
    def clear(self):
        """
        清空链表
        
        时间复杂度：O(1)
        """
        self.head = None
        self.tail = None
        self.size = 0
    
    def __str__(self):
        """
        字符串表示 - 格式化输出健康时间线
        
        Returns:
            str: 格式化的时间线字符串
        """
        if self.is_empty():
            return "健康时间线：暂无记录"
        
        records = self.traverse_forward()
        lines = [f"健康时间线 ({self.size} 条记录):"]
        lines.append("=" * 60)
        
        for i, record in enumerate(records, 1):
            severity_icon = {
                "low": "[L]",
                "medium": "[M]",
                "high": "[H]",
                "critical": "[C]"
            }.get(record["severity"], "[?]")
            
            lines.append(f"  {i}. {severity_icon} [{record['date']}] {record['type']}: {record['desc']}")
        
        return "\n".join(lines)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  双向链表测试 - 宠物健康记录时间线")
    print("=" * 60)
    
    # 创建链表
    timeline = DoublyLinkedList()
    print("\n【测试1】创建空链表")
    print(f"链表大小: {timeline.get_size()}")
    print(f"是否为空: {timeline.is_empty()}")
    print(timeline)
    
    # 添加记录
    print("\n【测试2】添加健康记录")
    records_data = [
        ("2026-01-15", "vaccine", "接种狂犬疫苗", "medium", {"hospital": "爱心宠物医院", "vet_name": "张医生"}),
        ("2026-02-20", "checkup", "常规体检，体重正常", "low", {"weight": "5.2kg"}),
        ("2026-03-10", "illness", "感冒发烧，服药治疗", "high", {"medicine": "宠物感冒灵"}),
        ("2026-04-01", "feeding", "更换为低敏狗粮", "low", {"brand": "皇家低敏粮"}),
        ("2026-04-15", "checkup", "复查恢复良好", "low", {"vet_name": "李医生"}),
    ]
    
    for date, event_type, desc, severity, details in records_data:
        node = HealthRecordNode(date, event_type, desc, severity, details)
        timeline.append(node)
        print(f"✓ 已添加: {node}")
    
    print(f"\n链表大小: {timeline.get_size()}")
    print(timeline)
    
    # 正向遍历
    print("\n【测试3】正向遍历（完整时间线）")
    all_records = timeline.traverse_forward()
    for i, record in enumerate(all_records, 1):
        print(f"  {i}. {record['date']} - {record['type']}")
    
    # 反向遍历
    print("\n【测试4】反向遍历（最近3条记录）")
    recent_records = timeline.traverse_backward(3)
    for i, record in enumerate(recent_records, 1):
        print(f"  {i}. {record['date']} - {record['desc']}")
    
    # 测试 count 超限
    print("\n【测试5】反向遍历 - count 超限（请求10条，实际5条）")
    many_records = timeline.traverse_backward(10)
    print(f"返回记录数: {len(many_records)}（应该返回全部5条）")
    
    # 查找测试
    print("\n【测试6】查找功能测试")
    
    # 按日期查找
    date_records = timeline.find_by_date("2026-04-15")
    print(f"\n按日期查找 (2026-04-15): 找到 {len(date_records)} 条记录")
    for r in date_records:
        print(f"  - {r['desc']}")
    
    # 按类型查找
    vaccine_records = timeline.find_by_type("vaccine")
    print(f"\n按类型查找 (vaccine): 找到 {len(vaccine_records)} 条记录")
    for r in vaccine_records:
        print(f"  - {r['date']}: {r['desc']}")
    
    # 按时间范围查找
    range_records = timeline.find_by_date_range("2026-02-01", "2026-04-01")
    print(f"\n按时间范围查找 (2026-02-01 ~ 2026-04-01): 找到 {len(range_records)} 条记录")
    for r in range_records:
        print(f"  - {r['date']}: {r['desc']}")
    
    # 按严重程度查找
    critical_records = timeline.find_by_severity("high")
    print(f"\n按严重程度查找 (high): 找到 {len(critical_records)} 条记录")
    for r in critical_records:
        print(f"  - {r['date']}: {r['desc']}")
    
    # 删除测试
    print("\n【测试7】删除功能测试")
    target_id = all_records[2]["record_id"]  # 删除第三条记录（illness）
    print(f"准备删除 record_id: {target_id}")
    success = timeline.delete_by_record_id(target_id)
    print(f"删除结果: {'✓ 成功' if success else '✗ 失败'}")
    print(f"删除后链表大小: {timeline.get_size()}")
    print(timeline)
    
    # 边界情况测试
    print("\n【测试8】边界情况测试")
    
    # 删除不存在的 ID
    result = timeline.delete_by_record_id("nonexistent_id")
    print(f"删除不存在的 ID: {'✗ 正确返回 False' if not result else '✓ 错误'}")
    
    # 日期格式校验
    try:
        bad_node = HealthRecordNode("2026/13/45", "test", "测试")
        print("✗ 日期校验失败：应该抛出 ValueError")
    except ValueError as e:
        print(f"✓ 日期格式校验成功: {e}")
    
    # 类型校验
    try:
        timeline.append("不是节点对象")
        print("✗ 类型校验失败：应该抛出 TypeError")
    except TypeError as e:
        print(f"✓ 类型校验成功: {e}")
    
    # details 字典隔离测试
    print("\n【测试9】details 字典隔离测试")
    shared_details = {"hospital": "测试医院"}
    node1 = HealthRecordNode("2026-05-01", "checkup", "记录1", details=shared_details)
    node2 = HealthRecordNode("2026-05-02", "checkup", "记录2", details=shared_details)
    
    # 修改 node1 的 details
    node1.details["vet_name"] = "新医生"
    
    print(f"node1 details: {node1.details}")
    print(f"node2 details: {node2.details}")
    print(f"原始 shared_details: {shared_details}")
    if "vet_name" not in node2.details:
        print("✓ 字典隔离成功：node2 不受 node1 影响")
    else:
        print("✗ 字典隔离失败：node2 被污染了")
    
    # 清空测试
    print("\n【测试10】清空链表")
    timeline.clear()
    print(f"清空后大小: {timeline.get_size()}")
    print(f"是否为空: {timeline.is_empty()}")
    print(timeline)
    
    print("\n" + "=" * 60)
    print("  所有测试完成！✅")
    print("=" * 60)
