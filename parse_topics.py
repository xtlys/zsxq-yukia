import json
import argparse
from pathlib import Path

def parse_single_file(file_path):
    """
    解析单个JSON文件并提取Q&A数据。
    
    参数:
        file_path (Path): 指向单个json文件的Path对象。
        
    返回:
        list: 包含该文件中所有Q&A字典的列表。
        
    抛出:
        json.JSONDecodeError: 如果文件不是有效的JSON。
        Exception: 其他文件读取或键错误。
    """
    
    extracted_qas = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    topics = data.get('resp_data', {}).get('topics', [])
    
    for topic in topics:
        # 确保这是一个q&a类型的条目，并且包含问题和答案
        if topic.get('type') == 'q&a' and 'question' in topic and 'answer' in topic:
            try:
                # 提取字段
                topic_id = topic.get('topic_id')
                create_time = topic.get('create_time')
                
                question_data = topic['question']
                answer_data = topic['answer']
                
                questioner_name = question_data.get('owner', {}).get('name')
                question_text = question_data.get('text')
                answerer_name = answer_data.get('owner', {}).get('name')
                answer_text = answer_data.get('text')
                
                # 将所有提取的数据添加到结果列表
                extracted_qas.append({
                    'topic_id': topic_id,
                    'create_time': create_time,
                    'questioner_name': questioner_name,
                    'question_text': question_text,
                    'answerer_name': answerer_name,
                    'answer_text': answer_text
                })
            except KeyError as e:
                # 即使在有效的q&a中，如果内部结构损坏，也打印警告
                print(f"  [!] 警告: 跳过 {file_path.name} 中的一个条目，因为缺少键：{e}")
    
    return extracted_qas

def process_directory(input_dir, output_file):
    """
    遍历目录中的所有JSON文件，解析它们，并将所有Q&A聚合到
    一个输出文件中。
    """
    
    input_path = Path(input_dir)
    if not input_path.is_dir():
        print(f"错误: 输入路径 '{input_dir}' 不是一个有效的目录。")
        return

    # 1. 查找所有 .json 文件
    json_files = list(input_path.glob('*.json'))
    
    if not json_files:
        print(f"在 '{input_dir}' 中没有找到 .json 文件。")
        return

    # 2. 初始化聚合器和摘要计数器
    all_extracted_qas = []
    total_files_found = len(json_files)
    files_processed_successfully = 0
    files_failed = 0
    total_qa_extracted = 0

    print(f"在 '{input_dir}' 中找到了 {total_files_found} 个 .json 文件。开始处理...")

    # 3. 遍历和解析每个文件
    for file_path in json_files:
        print(f"\n--- 正在处理: {file_path.name} ---")
        try:
            # 调用单个文件的解析函数
            qas_from_file = parse_single_file(file_path)
            
            if qas_from_file:
                all_extracted_qas.extend(qas_from_file)
                num_extracted = len(qas_from_file)
                total_qa_extracted += num_extracted
                print(f"  [+] 成功: 提取了 {num_extracted} 条 Q&A。")
            else:
                print("  [i] 信息: 文件有效，但在 'topics' 中未找到 'q&a' 条目。")
            
            files_processed_successfully += 1
            
        except json.JSONDecodeError:
            print(f"  [!] 错误: 无法解析 {file_path.name}。它不是一个有效的JSON文件。")
            files_failed += 1
        except PermissionError:
            print(f"  [!] 错误: 没有读取 {file_path.name} 的权限。")
            files_failed += 1
        except Exception as e:
            print(f"  [!] 错误: 处理 {file_path.name} 时发生意外错误: {e}")
            files_failed += 1

    # 4. 将所有聚合的数据写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_extracted_qas, f, ensure_ascii=False, indent=4)
        
        print(f"\n--- 所有聚合数据已保存到: {output_file} ---")

    except Exception as e:
        print(f"\n[!] 严重错误: 无法写入输出文件 {output_file}。错误: {e}")

    # 5. 打印最终的解析摘要
    print("\n" + "="*30)
    print("      Parse Summary      ")
    print("="*30)
    print(f"总共找到的 .json 文件: {total_files_found}")
    print(f"成功处理的文件:         {files_processed_successfully}")
    print(f"解析失败的文件:         {files_failed}")
    print("-" * 30)
    print(f"提取的 Q&A 总数:      {total_qa_extracted}")
    print("="*30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从一个目录中的所有JSON文件中提取Q&A数据。")
    
    # 将参数从 'input_file' 改为 'input_dir'
    parser.add_argument("input_dir", help="包含Q&A数据的源目录路径。")
    
    parser.add_argument("output_file", help="用于保存所有聚合结果的目标JSON文件路径。")
    
    args = parser.parse_args()
    
    process_directory(args.input_dir, args.output_file)