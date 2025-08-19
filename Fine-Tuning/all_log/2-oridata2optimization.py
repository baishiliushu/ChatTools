import re
from collections import defaultdict


def process_dialogues(file_content):
    # 分割文件内容为不同时间戳的对话块
    timestamp_blocks = re.split(r'(?=【请求时间】)', file_content)[1:]

    processed_blocks = []
    valid_timestamps = []

    for block in timestamp_blocks:
        # 解析时间戳ID
        timestamp_match = re.search(r'【请求时间】([^\n]+)\(ID: ([^)]+)\)', block)
        if not timestamp_match:
            continue

        timestamp_str = timestamp_match.group(1).strip()
        timestamp_id = timestamp_match.group(2)

        # 提取所有对话轮次
        turns = []
        turn_matches = re.finditer(
            r'【对话轮次 (\d+)】(\w+):\s*([\s\S]*?)(?=\n【对话轮次 |\Z)',
            block
        )

        for match in turn_matches:
            turn_num = int(match.group(1))
            speaker = match.group(2)
            content = match.group(3).strip()
            turns.append((turn_num, speaker, content))

        # 重组有效对话对 (user + assistant)
        valid_pairs = []
        i = 0
        while i < len(turns):
            if i + 1 < len(turns) and turns[i][1] == 'user' and turns[i + 1][1] == 'assistant':
                valid_pairs.append((turns[i], turns[i + 1]))
                i += 2  # 跳过已配对的两条
            else:
                i += 1  # 跳过孤立的user

        # 如果没有有效对话对，跳过整个时间戳
        if not valid_pairs:
            continue

        # 重新编号对话轮次
        renumbered_block = []
        new_turn_num = 1
        for (user_turn, assistant_turn) in valid_pairs:
            # 添加user轮次
            renumbered_block.append(f"【对话轮次 {new_turn_num}】user:\n{user_turn[2]}")
            # 添加assistant轮次
            renumbered_block.append(f"【对话轮次 {new_turn_num}】assistant:\n{assistant_turn[2]}")
            # 添加分隔符
            renumbered_block.append("-" * 50)
            new_turn_num += 1

        # 重建时间戳块
        processed_block = f"【请求时间】{timestamp_str} (ID: {timestamp_id})\n" + "\n".join(renumbered_block)
        processed_blocks.append(processed_block)
        valid_timestamps.append(timestamp_id)

    return "\n".join(processed_blocks), valid_timestamps


# 示例使用
if __name__ == "__main__":
    with open("all_dialogues.txt", "r", encoding="utf-8") as f:
        content = f.read()

    processed_content, valid_timestamps = process_dialogues(content)

    # 保存处理后的文件
    with open("all_opt_data.txt", "w", encoding="utf-8") as f:
        f.write(processed_content)

    print(f"处理完成，有效时间戳ID: {valid_timestamps}")