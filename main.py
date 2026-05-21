"""
智能宠物喂食管理系统 - 主程序入口

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

模块职责：
- 提供菜单驱动的命令行交互界面 (CLI)
- 整合档案管理模块与 AI 健康顾问
- 处理用户输入校验与异常捕获

架构设计：
- 采用模块化导入，确保在 Windows/Linux/macOS 下路径兼容
- 实现健壮的错误处理机制，防止因非法输入或 LLM 服务不可用导致程序崩溃
"""

import sys
from pathlib import Path

# ==================== 路径配置 ====================
# 将 src 目录和项目根目录加入搜索路径，确保跨平台兼容性
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from modules.pet_profile_manager import SmartPetProfileSystem
from ai_assistant.pet_health_advisor import PetHealthAdvisor
from modules.medical_ocr import MedicalOCRService
from modules.medical_extractor import MedicalInfoExtractor


def print_header():
    """打印系统欢迎横幅"""
    print("\n" + "=" * 50)
    print("   欢迎进入智能宠物喂食管理系统 (Phase 1)")
    print("=" * 50)
    print("   [1] 注册新宠物")
    print("   [2] 查看宠物列表")
    print("   [3] 添加健康记录")
    print("   [4] 咨询 AI 管家")
    print("   [5] 手动压缩记忆")
    print("   [6] 手动提取对话摘要")
    print("   [7] 上传病历 (自动提取)")
    print("   [8] 筛选病历记录")
    print("   [0] 退出系统")
    print("-" * 50)


def register_pet_flow(system):
    """[1] 注册新宠物的交互流程
    
    工程规范说明：
    - 输入校验：对数值型输入进行 try-except 捕获，防止非数字导致崩溃。
    - 封装原则：通过 system.get_pet_count() 获取状态，严禁直接访问底层哈希表。
    - 用户体验：提供清晰的选项映射，并在成功后展示完整摘要。
    """
    print("\n>>> 正在注册新宠物...")
    try:
        # 1. 基础信息录入
        name = input("请输入宠物姓名: ").strip()
        if not name:
            print("[ERR] 姓名不能为空！")
            return

        # 2. 物种选择
        species_map = {"1": "dog", "2": "cat", "3": "other"}
        print("请选择物种: 1.狗狗  2.猫咪  3.其他")
        species_choice = input("请输入选项编号: ").strip()
        species = species_map.get(species_choice, "unknown")

        # 3. 品种与性别录入
        breed = input("请输入品种: ").strip()
        
        gender_map = {"1": "male", "2": "female"}
        gender_choice = input("请选择性别: 1.公  2.母: ").strip()
        gender = gender_map.get(gender_choice, "unknown")
        if gender == "unknown":
            print("[WARN] 未识别的性别选项，已默认设为 '未知'")
        
        # 4. 数值型输入校验（健壮性核心）
        try:
            age = float(input("请输入年龄(岁): "))
            weight = float(input("请输入体重(kg): "))
        except ValueError:
            print("[ERR] 年龄和体重必须是数字！")
            return

        # 5. 调用核心业务逻辑（遵循封装原则）
        pet_count = system.get_pet_count()
        pet_id = f"pet_{pet_count + 1:03d}"
        system.register_pet(pet_id, name, breed, age, weight, gender=gender, species=species)
        
    except Exception as e:
        print(f"[ERR] 注册过程中发生未知错误：{e}")


def list_pets_flow(system):
    """[2] 查看宠物列表的交互流程"""
    print("\n>>> 当前系统中的所有宠物：")
    pets = system.show_all_pets()
    if not pets:
        print("  暂无宠物档案，请先注册。")


def add_record_flow(system):
    """[3] 添加健康记录的交互流程"""
    print("\n>>> 正在添加健康记录...")
    
    # 1. 选择宠物
    pet_name = input("请输入宠物姓名: ").strip()
    matches = system.search_by_name(pet_name)
    if not matches:
        print(f"[ERR] 找不到名为 '{pet_name}' 的宠物。")
        return
    target_pet = matches[0]
    pet_id = target_pet.pet_id
    
    # 2. 录入记录信息
    try:
        date = input("请输入日期 (YYYY-MM-DD): ").strip()
        print("事件类型: 1.疫苗  2.体检  3.生病  4.喂养")
        type_map = {"1": "vaccine", "2": "checkup", "3": "illness", "4": "feeding"}
        type_choice = input("请选择类型编号: ").strip()
        event_type = type_map.get(type_choice, "other")
        
        desc = input("请输入详细描述: ").strip()
        
        # 3. 调用业务逻辑
        system.add_health_record(pet_id, date, event_type, desc)
    except Exception as e:
        print(f"[ERR] 记录添加失败：{e}")


def ai_consult_flow(system, advisor):
    """[4] 咨询 AI 管家的交互流程（连续对话子模式）
    
    功能特性：
    - 进入 while True 循环，支持多轮对话
    - 特殊指令：/list 查看历史、/archive 精准提取摘要、/debug 切换调试模式
    - 退出时自动归档最后一段对话
    - 支持动态开启/关闭调试模式，实时显示计数器、Token 估算等技术细节
    """
    print("\n>>> 正在连接 AI 管家...")
    pet_name = input("请输入您要咨询的宠物姓名: ").strip()
    
    # 根据姓名查找宠物（模糊匹配）
    matches = system.search_by_name(pet_name)
    if not matches:
        print(f"[ERR] 找不到名为 '{pet_name}' 的宠物，请检查姓名是否正确。")
        return
    
    # 默认取第一个匹配的宠物
    target_pet = matches[0]
    print(f"\n已选中宠物：{target_pet}")
    
    # 准备发送给 AI 的数据字典（接口隔离原则）
    pet_data = {
        "name": target_pet.name,
        "species": target_pet.species,
        "breed": target_pet.breed,
        "age": target_pet.age,
        "weight": target_pet.weight,
        "gender": target_pet.gender,
        "recent_records": target_pet.health_timeline.traverse_backward(5)
    }
    
    # 【关键步骤】注入宠物上下文到 System Prompt
    advisor.set_current_pet_context(pet_data)
    
    # 初始化调试模式状态
    is_debug_mode = False
    
    # 进入连续对话子模式
    print("\n" + "=" * 60)
    print("   AI 宠物健康管家 - 连续对话模式")
    print("=" * 60)
    print("   输入 'exit' 或 'quit' 退出")
    print("   输入 '/list' 查看历史记录")
    print("   输入 '/archive <轮次>' 精准提取摘要（如 /archive 1,3-5）")
    print("   输入 '/debug' 切换调试模式（显示计数器、Token 等）")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n[你]: ").strip()
            
            if not user_input:
                continue
            
            # 1. 退出检测
            if user_input.lower() in ['exit', 'quit', '返回', 'q']:
                print("\n[系统] 已结束本次咨询，正在为您保存记录...")
                # 强制保存最后一段对话
                summary = advisor.get_medical_summary(force=True)
                if summary:
                    print(f"\n--- 问诊记录 ---\n{summary}\n----------------")
                print("[OK] 记录已保存，返回主菜单。")
                
                # 【关键步骤】重置上下文，防止信息串台
                advisor.reset_context()
                break
            
            # 2. 特殊指令检测
            if user_input.startswith('/list'):
                history_display = advisor.get_history_display()
                print(f"\n{history_display}")
                continue
            
            if user_input.startswith('/archive'):
                expression = user_input[len('/archive'):].strip()
                if not expression:
                    print("[系统] 请指定轮次，格式：/archive 1,3-5")
                    continue
                result = advisor.extract_summary_by_rounds(expression)
                print(result)
                continue
            
            # 【新增】动态调试模式切换
            if user_input.lower() == '/debug':
                is_debug_mode = not is_debug_mode
                advisor.client.debug_mode = is_debug_mode
                status = "✅ 已开启" if is_debug_mode else "❌ 已关闭"
                print(f"\n[调试模式] {status}")
                if is_debug_mode:
                    print("   ✓ 将显示计数器状态、Token 估算、API 请求详情")
                    print("   ✓ 将显示压缩/提取触发判定过程")
                else:
                    print("   ✓ 仅显示 AI 回复和必要系统提示")
                continue
            
            # 3. 正常对话（使用双模态咨询接口）
            if is_debug_mode:
                print("\n🤖 AI 管家思考中...（调试模式）")
            else:
                print("\n🤖 AI 管家思考中...")
            
            # 调用统一的咨询接口，自动识别意图并切换模式
            response = advisor.consult(user_input)
            
            # 【已移除】流式输出时已打印，无需重复
            # print(f"\n[AI 管家]: {response}")
            
            # 【可选】调试模式下显示响应长度
            if is_debug_mode:
                print(f"\n[调试] 完整响应长度: {len(response)} 字符")
            
            # 【已移除】consult() 内部已自动处理提取逻辑，无需重复调用
            
        except RuntimeError as e:
            print(f"[WARN] AI 服务暂时不可用，请稍后重试。({e})")
        except KeyboardInterrupt:
            print("\n\n[系统] 检测到中断信号，正在保存记录...")
            advisor.get_medical_summary(force=True)
            print("[OK] 记录已保存，返回主菜单。")
            
            # 【关键步骤】重置上下文
            advisor.reset_context()
            break
        except Exception as e:
            print(f"[ERR] 咨询过程中发生未知错误：{e}")


def search_records_flow(system):
    """[8] 筛选病历记录的交互流程
    
    根据 Spec 要求，支持按宠物名称、编号和日期范围组合筛选。
    """
    print("\n>>> 正在启动病历筛选助手...")
    
    # 1. 获取用户输入
    pet_name = input("请输入宠物姓名（可选）: ").strip()
    pet_id = input("请输入宠物编号（可选）: ").strip()
    start_date = input("请输入起始日期 YYYY-MM-DD（可选）: ").strip()
    end_date = input("请输入结束日期 YYYY-MM-DD（可选）: ").strip()
    
    # 2. 调用业务逻辑
    try:
        records = system.filter_medical_records(
            pet_name if pet_name else None,
            pet_id if pet_id else None,
            start_date if start_date else None,
            end_date if end_date else None
        )
    except ValueError as e:
        print(f"[ERR] {e}")
        return
    
    # 3. 展示结果
    if not records:
        print("[系统] 未找到符合条件的病历记录")
    else:
        print(f"\n共找到 {len(records)} 条记录：")
        print("-" * 60)
        for i, r in enumerate(records, 1):
            print(f"{i}. [{r['date']}] {r['pet_name']} - {r['description']}")
        print("-" * 60)


def upload_medical_record_flow(system, advisor):
    """[5] 上传病历并自动提取的交互流程"""
    print("\n>>> 正在启动智能病历助手...")
    
    # 1. 选择宠物
    pet_name = input("请输入宠物姓名: ").strip()
    matches = system.search_by_name(pet_name)
    if not matches:
        print(f"[ERR] 找不到名为 '{pet_name}' 的宠物。")
        return
    target_pet = matches[0]
    pet_id = target_pet.pet_id
    
    # 2. 输入图片路径（原型阶段简化为输入路径）
    image_path = input("请输入病历照片路径 (或按回车使用测试图片): ").strip()
    if not image_path:
        # 自动构建项目根目录下的测试图片绝对路径，防止因工作目录不同导致找不到文件
        image_path = str(project_root / "data" / "uploads" / "test_record.png")
        print(f"[系统] 使用默认测试图片: {image_path}")
    
    try:
        # 3. 执行 OCR (API-001)
        ocr_service = MedicalOCRService()
        print("[系统] 正在识别图片文字...")
        raw_text = ocr_service.process_medical_image(image_path)
        
        # 【新增】完整打印 OCR 识别结果，供用户核对
        print("\n" + "=" * 60)
        print("   📄 OCR 完整识别结果")
        print("=" * 60)
        print(raw_text)
        print("=" * 60 + "\n")
        
        # 4. 提取结构化信息 (API-002)
        extractor = MedicalInfoExtractor(advisor)
        print("[系统] AI 正在分析病历内容...")
        extraction_data = extractor.extract_structured_info(raw_text)
        
        # 5. 展示提取结果供校对
        print("\n--- 提取结果校对 ---")
        doc_type = extraction_data.get('document_type', 'unknown')
        
        if doc_type == 'blood_test':
            # 血常规化验单
            pet_info = extraction_data.get('pet_info', {})
            print(f"文档类型: 血常规化验单")
            print(f"宠物信息: {pet_info.get('name', '未知')} ({pet_info.get('breed', '未知')}, {pet_info.get('age', '未知')}岁)")
            print(f"\n化验指标（共 {len(extraction_data.get('test_results', []))} 项）:")
            
            # 标记异常指标
            abnormal_items = []
            for item in extraction_data.get('test_results', []):
                flag = "⚠️ 异常" if item.get('abnormal') else "✅ 正常"
                print(f"  {item.get('name')}: {item.get('value')} {item.get('unit')} {flag}")
                if item.get('abnormal'):
                    abnormal_items.append(item)
            
            if abnormal_items:
                print(f"\n⚠️ 发现 {len(abnormal_items)} 项异常指标:")
                for item in abnormal_items:
                    print(f"  - {item.get('name')}: {item.get('value')} (参考范围: {item.get('lower_limit')}-{item.get('upper_limit')})")
        else:
            # 诊断病历
            print(f"文档类型: 诊断病历")
            print(f"诊断: {extraction_data.get('diagnosis')}")
            print(f"药品: {extraction_data.get('medicines')}")
        confirm = input("确认归档吗？(y/n): ").strip().lower()
        
        if confirm == 'y':
            # 6. 生成康复建议 (API-003)
            print("[系统] 正在生成分析建议...")
            
            if doc_type == 'blood_test':
                # 针对血常规生成解读建议
                test_results = extraction_data.get('test_results', [])
                abnormal_items = [item for item in test_results if item.get('abnormal')]
                advice = extractor.generate_recovery_advice(
                    pet_id, 
                    f"血常规异常指标：{', '.join([item.get('name') for item in abnormal_items])}",
                    []
                )
            else:
                # 针对诊断病历生成康复建议
                advice = extractor.generate_recovery_advice(
                    pet_id, 
                    extraction_data.get('diagnosis'), 
                    extraction_data.get('medicines')
                )
            
            print(f"\n🩺 AI 分析建议:\n{advice}\n")
            
            # 7. 保存记录 (API-004)
            system.save_medical_record(pet_id, extraction_data, image_path)
            print("[OK] 病历已成功归档至健康时间线！")
        else:
            print("[系统] 已取消归档。")
            
    except Exception as e:
        print(f"[ERR] 处理失败: {e}")


def main():
    """主程序入口"""
    import os
    import sys
    import time
    
    # 检测 Conda 环境激活状态（解决 VS Code 首次运行中断问题）
    conda_default_env = os.environ.get('CONDA_DEFAULT_ENV')
    
    # 如果环境未激活，主动初始化 Conda 环境
    # 这样可以确保所有必要的环境变量都被正确设置
    if not conda_default_env:
        print("[系统] 检测到环境未激活，正在初始化...")
        
        # 尝试找到 Conda 安装路径并初始化环境
        try:
            # 方法1: 从当前 Python 解释器路径推断 Conda 环境路径
            python_exe = sys.executable  # 例如: D:/ruanjian/Anaconda_envs/envs/smart-pet-system/python.exe
            
            # 正确的路径推断：向上两级得到环境根目录
            env_path = os.path.dirname(os.path.dirname(python_exe))  # D:/ruanjian/Anaconda_envs/envs/smart-pet-system
            
            # 检查是否正确（应该包含 python.exe 或 python3.exe）
            if not os.path.exists(os.path.join(env_path, 'python.exe')) and \
               not os.path.exists(os.path.join(env_path, 'python3.exe')):
                # 如果不正确，再向上一级
                env_path = os.path.dirname(env_path)
            
            env_name = os.path.basename(env_path)  # smart-pet-system
            
            # 设置必要的环境变量（模拟 conda activate 的效果）
            os.environ['CONDA_DEFAULT_ENV'] = env_name
            os.environ['CONDA_PREFIX'] = env_path
            
            # 将环境的 Scripts/bin 目录添加到 PATH
            scripts_dir = os.path.join(env_path, 'Scripts')
            if os.path.exists(scripts_dir):
                os.environ['PATH'] = scripts_dir + os.pathsep + os.environ.get('PATH', '')
            
            print(f"[OK] 环境已初始化: {env_name}")
            
        except Exception as e:
            print(f"[WARN] 环境初始化失败: {e}，将继续运行但可能缺少某些环境变量")
        
        # 短暂等待，确保环境完全就绪
        time.sleep(0.5)
    
    print("正在初始化系统组件...")
    
    try:
        # 初始化核心模块
        system = SmartPetProfileSystem()
        advisor = PetHealthAdvisor()
        print("[OK] 系统初始化完成！\n")
    except Exception as e:
        print(f"[ERR] 系统启动失败：{e}")
        return

    while True:
        try:
            print_header()
            choice = input("请输入您的选择: ").strip()
        except KeyboardInterrupt:
            # VS Code 环境激活完成时发送的中断信号
            # 忽略此信号，重新显示菜单
            print("\n[系统] 检测到中断信号，正在重试...")
            time.sleep(0.5)
            continue

        if choice == '1':
            register_pet_flow(system)
        elif choice == '2':
            list_pets_flow(system)
        elif choice == '3':
            add_record_flow(system)
        elif choice == '4':
            ai_consult_flow(system, advisor)
        elif choice == '5':
            print("\n>>> 正在执行记忆压缩...")
            try:
                advisor.compress_memory()
                print("[OK] 已为您清理了冗余的对话细节，保留了关键信息。这有助于 AI 在长对话中保持清醒。")
            except Exception as e:
                print(f"[ERR] 压缩失败：{e}")
        elif choice == '6':
            print("\n>>> 正在提取 AI 管家对话摘要...")
            try:
                summary = advisor.get_medical_summary(force=True)
                if summary:
                    print(f"\n--- 对话摘要 ---\n{summary}\n----------------")
                    print("[OK] 已成功提取本次问诊精华，并保存至 D:\\chat-log 目录。您可以随时查阅宠物的健康档案。")
                else:
                    print("暂无可提取的对话摘要（建议至少进行一轮有效问诊）。")
            except Exception as e:
                print(f"[ERR] 提取失败：{e}")
        elif choice == '7':
            upload_medical_record_flow(system, advisor)
        elif choice == '8':
            search_records_flow(system)
        elif choice == '0':
            print("\n感谢使用智能宠物喂食管理系统，再见！👋")
            break
        else:
            print("[ERR] 无效的选择，请输入 0-7 之间的数字。")


if __name__ == "__main__":
    main()
