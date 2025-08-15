import json


def split_by_assistant_type(input_file, output_type2, output_type3):
    # 初始化存储数据的列表
    type2_data = []
    type3_data = []

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                assistant = entry['assistant']

                # 处理assistant字段（可能是字符串或字典）
                if isinstance(assistant, str):
                    assistant_data = json.loads(assistant)
                else:
                    assistant_data = assistant

                # 根据type值分类
                if str(assistant_data.get('type')) == '2':
                    type2_data.append(entry)
                elif str(assistant_data.get('type')) == '3':
                    type3_data.append(entry)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"处理行时出错: {line.strip()}, 错误: {e}")

    # 写入type2文件
    with open(output_type2, 'w', encoding='utf-8') as f2:
        for item in type2_data:
            f2.write(json.dumps(item, ensure_ascii=False) + '\n')

    # 写入type3文件
    with open(output_type3, 'w', encoding='utf-8') as f3:
        for item in type3_data:
            f3.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"拆分完成! type2: {len(type2_data)}条, type3: {len(type3_data)}条")


# 使用示例
if __name__ == "__main__":
    input_json = "cleaned_original_format_data.json"
    output_type2 = "type2_responses.json"
    output_type3 = "type3_responses.json"

    split_by_assistant_type(input_json, output_type2, output_type3)