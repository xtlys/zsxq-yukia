import json
import argparse
from datetime import datetime

def get_sort_key(item):
    """
    安全地获取用于排序的datetime对象。
    处理缺失或格式错误的 'create_time'。
    """
    time_str = item.get('create_time')
    if not time_str:
        # 将没有时间的条目放在最前面
        print(f"警告: 找到一个没有 'create_time' 的条目 (ID: {item.get('topic_id')})。")
        return datetime.min
    try:
        # fromisoformat 可以直接解析 "2025-10-16T15:49:04.119+0800" 这种格式
        return datetime.fromisoformat(time_str)
    except ValueError:
        print(f"警告: 无法解析时间字符串 '{time_str}' (ID: {item.get('topic_id')})。")
        # 将格式错误的条目也放在最前面
        return datetime.min

def generate_markdown_content(qa_list):
    """
    将Q&A列表转换为带有TOC和可跳转锚点的Markdown字符串。
    """
    
    # --- 1. 初始化TOC和内容列表 ---
    toc_lines = ["# Q&A 合订本\n", "# 目录\n"]
    content_lines = []
    
    if not qa_list:
        toc_lines.append("未找到任何 Q&A 内容。")
        return "".join(toc_lines)

    # --- 2. 遍历列表，同时生成TOC和内容 ---
    for index, qa in enumerate(qa_list, start=1):
        
        # --- 2a. 准备TOC条目 ---
        
        topic_id = qa.get('topic_id', 'unknown-id')
        anchor = f"qa-{topic_id}"
        
        time_obj = get_sort_key(qa)
        if time_obj == datetime.min:
            time_str_simple = "时间无效"
        else:
            time_str_simple = time_obj.strftime('%Y-%m-%d %H:%M')
            
        # --- START: 新增逻辑 - 截取问题标题 ---
        # 1. 获取完整的 'question_text'
        question_head = qa.get('question_text', '')
        
        if not question_head:
            question_preview = "（无问题内容）"
        else:
            # 2. 截取前15个字
            question_preview = question_head[:20]
            # 3. 'trim' - 移除换行符并去除首尾空格
            question_preview = question_preview.replace('\n', ' ').strip()
            # 4. 如果原文本更长，添加省略号
            if len(question_head) > 20:
                question_preview += "..."
        # --- END: 新增逻辑 ---
            
        # 创建新的TOC链接文本
        toc_text = f"[{time_str_simple}] - {question_preview}"
        
        # 添加带序号的TOC条目
        toc_lines.append(f"{index}. [{toc_text}](#{anchor})")
        
        
        # --- 2b. 准备内容条目 ---
        
        content_lines.append("\n---\n")
        content_lines.append(f'<a id="{anchor}"></a>')
        
        time_str_full = qa.get('create_time', 'N/A')
        content_lines.append(f"# {index}. {time_str_simple} (ID: {topic_id})")
        
        # 准备问题正文
        questioner = qa.get('questioner_name', '匿名')
        # (我们已经将全文保存在 'question_head' 变量中)
        formatted_question = "> " + question_head.replace('\n', '\n> ')
        
        content_lines.append(f"\n**提问：{questioner}**")
        content_lines.append(formatted_question)
        
        # 准备回答正文
        answerer = qa.get('answerer_name', '匿名')
        answer_text = qa.get('answer_text', '（无回答内容）')
        
        content_lines.append(f"\n**回答：{answerer}**")
        content_lines.append(f"\n{answer_text}\n")
    
    # --- 3. 组合TOC和内容 ---
    return "\n".join(toc_lines) + "\n" + "\n".join(content_lines)

def create_markdown_compilation(input_file, output_file):
    """
    读取JSON文件，排序，并生成Markdown合订本。
    """
    
    print(f"正在从 {input_file} 读取数据...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            qa_list = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到输入文件 {input_file}")
        return
    except json.JSONDecodeError:
        print(f"错误: 无法解析 {input_file}。请确保它是一个有效的JSON文件。")
        return
    except Exception as e:
        print(f"读取文件时发生意外错误: {e}")
        return

    if not isinstance(qa_list, list) or not qa_list:
        print("JSON文件为空或格式不正确（顶层不是一个列表）。")
        return

    print(f"找到了 {len(qa_list)} 条 Q&A。正在按 'create_time' 排序...")
    
    # 2. 按时间排序
    qa_list.sort(key=get_sort_key)
    
    print("排序完成。正在生成Markdown内容...")
    
    # 3. 生成Markdown (现在包含TOC)
    markdown_content = generate_markdown_content(qa_list)
    
    # 4. 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"\n成功！带有TOC的合订本已生成并保存到: {output_file}")
    except Exception as e:
        print(f"写入Markdown文件时发生错误: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将Q&A JSON文件转换为排序后的Markdown合订本。")
    
    parser.add_argument("input_file", help="包含Q&A数据的源JSON文件路径 (例如: all_qas_output.json)。")
    
    parser.add_argument("output_file", help="要生成的目标Markdown文件路径 (例如: compilation.md)。")
    
    args = parser.parse_args()
    
    create_markdown_compilation(args.input_file, args.output_file)