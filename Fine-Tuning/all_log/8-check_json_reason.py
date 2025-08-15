import json


def validate_assistant_json(file_path):
    """
    验证JSON Lines文件中assistant字段的JSON格式
    :param file_path: JSON Lines文件路径
    :return: 验证结果统计
    """
    valid_count = 0
    invalid_count = 0
    invalid_lines = []

    with open(file_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, 1):
            try:
                # 解析整行JSON
                record = json.loads(line.strip())
                assistant_str = record.get("assistant", "")

                # 尝试解析assistant字段
                json.loads(assistant_str)
                valid_count += 1

            except (json.JSONDecodeError, TypeError) as e:
                invalid_count += 1
                invalid_lines.append({
                    "line_number": line_number,
                    "error_type": type(e).__name__,
                    "error_msg": str(e),
                    "content": assistant_str[:100] + "..." if len(assistant_str) > 100 else assistant_str
                })

    return {
        "total_records": valid_count + invalid_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "invalid_lines": invalid_lines
    }


# 使用示例
if __name__ == "__main__":
    result = validate_assistant_json("cleaned_original_format_data.json")

    print(f"总记录数: {result['total_records']}")
    print(f"有效JSON数: {result['valid_count']}")
    print(f"无效JSON数: {result['invalid_count']}")

    if result['invalid_count'] > 0:
        print("\n无效记录详情:")
        for item in result['invalid_lines']:
            print(f"行号 {item['line_number']} - 错误类型: {item['error_type']}")
            print(f"错误信息: {item['error_msg']}")
            print(f"内容片段: {item['content']}\n")