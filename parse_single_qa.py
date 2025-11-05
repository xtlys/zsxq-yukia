import json
import argparse
from pathlib import Path

def parse_single_topic_file(file_path):
    """
    尝试从单个JSON文件中解析 'resp_data.topic' 结构。
    
    参数:
        file_path (Path): 指向单个json文件的Path对象。
        
    返回:
        dict: 如果成功，返回一个Q&A字典。
        None: 如果文件有效，但不是q&a或未找到topic。
        
    抛出:
        json.JSONDecodeError: 如果文件不是有效的JSON。
        Exception: 其他文件读取或键错误。
    """
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # 导航到 'resp_data' -> 'topic'
    topic = data.get('resp_data', {}).get('topic', {})
    
    # 如果没有 'topic' 对象，或者它不是 'q&a' 类型，则返回 None
    if not topic or topic.get('type') != 'q&a' or 'question' not in topic or 'answer' not in topic:
        return None
    
    # 如果是 Q&A，则提取数据
    try:
        topic_id = topic.get('topic_id')
        create_time = topic.get('create_time')
        
        question_data = topic.get('question', {})
        answer_data = topic.get('answer', {})
        
        questioner_name = question_data.get('owner', {}).get('name')
        question_text = question_data.get('text')
        answerer_name = answer_data.get('owner', {}).get('name')
        answer_text = answer_data.get('text')
        
        # 构建Q&A字典并返回
        extracted_qa = {
            'topic_id': topic_id,
            'create_time': create_time,
            'questioner_name': questioner_name,
            'question_text': question_text,
            'answerer_name': answerer_name,
            'answer_text': answer_text
        }
        return extracted_qa
        
    except Exception as e:
        # 捕获可能的内部结构错误
        raise Exception(f"提取字段时出错: {e}")


def process_directory(input_dir, output_file):
    """
    遍历目录中的所有JSON文件，使用“单个topic”逻辑解析它们，
    并将所有Q&A聚合到一个输出文件中。
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
    files_processed = 0
    files_failed = 0
    total_qa_extracted = 0

    print(f"在 '{input_dir}' 中找到了 {total_files_found} 个 .json 文件。开始处理...")

    # 3. 遍历和解析每个文件
    for file_path in json_files:
        print(f"\n--- 正在处理: {file_path.name} ---")
        try:
            # 调用单个文件的解析函数
            qa_item = parse_single_topic_file(file_path)
            
            files_processed += 1
            
            if qa_item:
                all_extracted_qas.append(qa_item)
                total_qa_extracted += 1
                print(f"  [+] 成功: 提取了 1 条 Q&A。")
            else:
                print("  [i] 信息: 文件有效，但在 'resp_data' 中未找到 'q&a' 类型的 'topic'。")
            
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
    print(f"成功处理的文件:         {files_processed}")
    print(f"解析失败的文件:         {files_failed}")
    print("-" * 30)
    print(f"提取的 Q&A 总数:      {total_qa_extracted}")
    print("="*30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从一个目录中提取所有'单个topic'的Q&A数据。")
    
    parser.add_argument("input_dir", help="包含Q&A数据的源目录路径。")
    
    parser.add_argument("output_file", help="用于保存所有聚合结果的目标JSON文件路径。")
    
    args = parser.parse_args()
    
    process_directory(args.input_dir, args.output_file)