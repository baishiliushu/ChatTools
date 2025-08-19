import re


def process_dialog_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 分割内容为不同的请求时间块
    blocks = re.split(r'-{50,}', content)
    processed_blocks = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 提取请求时间行
        request_time_match = re.search(r'【请求时间】[^\n]+', block)
        if not request_time_match:
            continue

        request_line = request_time_match.group(0)
        # 提取所有对话轮次
        turns = re.findall(
            r'(【对话轮次 \d+】user:[^【]*(?:【对话轮次 \d+】assistant:[^【]*)?)',
            block,
            re.DOTALL
        )

        if not turns:
            # 如果没有找到对话轮次，保留整个块
            processed_blocks.append(block)
            continue

        # 获取最后一轮对话
        last_turn = turns[-1].strip()

        # 修改轮次标记为【对话轮次 1】
        last_turn = re.sub(
            r'【对话轮次 \d+】',
            '【对话轮次 1】',
            last_turn
        )

        # 构建新块内容
        new_block = f"{request_line}\n{last_turn}"
        processed_blocks.append(new_block)

    # 组合处理后的块，保留原始分隔符格式
    result = '\n' + '-' * 50 + '\n'.join(processed_blocks)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result.strip())


# 使用示例
process_dialog_file('all_opt_data.txt', 'all_single_data.txt')