import re
import json


def process_file(input_file, output_file):
    # 读取文件内容
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分割成不同的对话轮次块
    blocks = re.split(r'(?=\【请求时间\】)', content)
    cleaned_blocks = []

    for block in blocks:
        if not block.strip():
            continue

        # 检查是否包含"Reference Materials:"
        if "Reference Materials:" in block:
            continue

        # 提取assistant内容
        assistant_match = re.search(r'【对话轮次 \d】assistant:(.*?)(?=\n\【请求时间\】|\Z)', block, re.DOTALL)
        if not assistant_match:
            continue

        assistant_content = assistant_match.group(1).strip()

        # 检查assistant内容是否完全是JSON格式
        try:
            # 尝试解析整个内容
            json.loads(assistant_content)
            is_pure_json = True
        except:
            # 检查是否以JSON开头
            if re.match(r'^\s*\{', assistant_content):
                # 尝试提取JSON部分
                json_match = re.search(r'(\{.*\})', assistant_content, re.DOTALL)
                if json_match:
                    try:
                        json.loads(json_match.group(1))
                        is_pure_json = False  # 混合内容
                    except:
                        is_pure_json = False
                else:
                    is_pure_json = False
            else:
                is_pure_json = False

        # 保留纯JSON格式的块
        if is_pure_json:
            # 移除"【对话轮次 1】"前缀
            cleaned_block = re.sub(r'【对话轮次 \d】', '', block)
            cleaned_blocks.append(cleaned_block)

    # 写入处理后的内容
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(cleaned_blocks))


# 使用示例
input_file = 'all_single_data.txt'
output_file = 'all_no_illegal_ass_tolong_user.txt'
process_file(input_file, output_file)