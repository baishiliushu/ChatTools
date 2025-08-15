import json
import re

# 定义身份表露关键词的正则表达式
identity_pattern = re.compile(r'我叫|我是|我叫做|我的名字|我的名字是|我的名称|我的名称是|我的版本|我的型号')


def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, \
            open(output_file, 'w', encoding='utf-8') as outfile:

        for line in infile:
            try:
                # 解析外层JSON
                entry = json.loads(line.strip())
                assistant_str = entry["assistant"]

                # 尝试解析内层JSON
                try:
                    assistant_data = json.loads(assistant_str)
                    content = assistant_data.get("content", "")
                except:
                    # 如果内层不是JSON，直接使用字符串
                    content = assistant_str

                # 检查是否包含身份关键词
                if not identity_pattern.search(content):
                    outfile.write(line)
            except (json.JSONDecodeError, KeyError):
                # 如果解析失败，保留原始行
                outfile.write(line)


if __name__ == "__main__":
    input_file = "different_user_data.txt"
    output_file = "all_no_shenfen_data.txt"
    process_file(input_file, output_file)
    print(f"处理完成！结果已保存到 {output_file}")