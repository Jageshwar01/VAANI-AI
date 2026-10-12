"""Fix social presentation block in brain.py to mute STT during AI generation."""
import re

path = r"c:\Users\Maxx\Desktop\ALL Project\VaaniAi\core\brain.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the presentation trigger block in social mode (lines ~741-756)
# Match the block using regex so CRLF vs LF doesn't matter
pattern = re.compile(
    r"(            # ── Presentation trigger ──+\r?\n"
    r"            if any\(word in text_lower for word in presentation_keywords\):\r?\n"
    r"                print\(\"\[SOCIAL\] Presentation triggered!\"\)\r?\n)"
    r"(                knowledge_context.*?continue\r?\n)",
    re.DOTALL
)

replacement_body = (
    "                # FIX: Mute STT during AI generation (60s) to discard noise\r\n"
    "                self.stt.mute()\r\n"
    "                knowledge_context = self.knowledge.get_context_string(\"presentation self introduction VaaniAI\")\r\n"
    "                script = self.chat_engine.respond(\r\n"
    "                    user_text=\"Give your full 1-minute university presentation. Use the knowledge context provided.\",\r\n"
    "                    person_name=person,\r\n"
    "                    mode=\"presentation\",\r\n"
    "                    memories=None,\r\n"
    "                    language_mode=self.language_mode,\r\n"
    "                    knowledge_context=knowledge_context,\r\n"
    "                )\r\n"
    "                # FIX: Flush noise accumulated during generation, then unmute\r\n"
    "                self.stt.flush()\r\n"
    "                self.stt.unmute()\r\n"
    "                self.speak(script)\r\n"
    "                self.stt.flush()  # Discard any STT picked up during presentation\r\n"
    "                self.memory.add_memory(person, text, script, \"social\")\r\n"
    "                continue\r\n"
)

m = pattern.search(content)
if m:
    new_content = content[:m.start(2)] + replacement_body + content[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: Social presentation block fixed.")
else:
    print("NOT FOUND — printing surrounding lines for debugging:")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if "Presentation trigger" in line and "SOCIAL" in lines[i+1] if i+1 < len(lines) else False:
            for j in range(max(0, i-1), min(len(lines), i+20)):
                print(f"{j+1}: {repr(lines[j])}")
            break
    # Fallback: just search for the block
    idx = content.find("[SOCIAL] Presentation triggered!")
    if idx != -1:
        print("Found at char", idx)
        print(repr(content[idx-200:idx+400]))
