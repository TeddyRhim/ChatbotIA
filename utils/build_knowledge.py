import os
import re
import json



data_raw_path = os.path.join("data", "data_raw", "data_raw.txt")
with open(data_raw_path, "r", encoding="utf-8") as f:
    data_raw = f.read()


sections = re.split(r'\n([A-Z &]+)\n', data_raw)
knowledge_dict = {}
for i in range(1, len(sections), 2):
    title = sections[i].strip()
    content = sections[i+1].strip()
    knowledge_dict[title] = content


knowledge_fragments = []

for section, content in knowledge_dict.items():
    lines = content.split("\n")
    fragment = []
    for line in lines:
        line = line.strip()
        if line.startswith("-"):
            if fragment:
                knowledge_fragments.append({"section": section, "text": " ".join(fragment)})
                fragment = []
            fragment.append(line[1:].strip())
        else:
            if line:
                fragment.append(line)
    if fragment:
        knowledge_fragments.append({"section": section, "text": " ".join(fragment)})

knowledge_path = os.path.join("data", "knowledge", "knowledge.json")

with open(knowledge_path, "w", encoding="utf-8") as f:
    json.dump(knowledge_fragments, f, indent=4, ensure_ascii=False)