import re

class MarkdownTreeParser:
    """
    针对 MinerU 产出的 Markdown，通过检测 # 标题层级构造嵌套的 JSON 树状结构。
    """
    @staticmethod
    def parse_to_tree(content: str):
        lines = content.split('\n')
        root = {"title": "Root", "content": "", "children": [], "level": 0}
        stack = [root]

        current_text = []
        
        # 匹配标题，例如 # 标题1, ## 标题2
        header_regex = re.compile(r'^(#{1,6})\s+(.*)$')

        for line in lines:
            match = header_regex.match(line)
            if match:
                # 在进入新标题前，保存上一个标题的累积正文
                if current_text:
                    stack[-1]["content"] = "\n".join(current_text).strip()
                    current_text = []

                level = len(match.group(1))
                title = match.group(2).strip()
                
                new_node = {
                    "title": title,
                    "content": "",
                    "children": [],
                    "level": level
                }

                # 寻找父节点：弹出栈直到找到 level 比当前小的节点
                while len(stack) > 1 and stack[-1]["level"] >= level:
                    stack.pop()
                
                stack[-1]["children"].append(new_node)
                stack.append(new_node)
            else:
                current_text.append(line)

        # 保存最后一截正文
        if current_text and stack:
            stack[-1]["content"] = "\n".join(current_text).strip()

        return root["children"]
