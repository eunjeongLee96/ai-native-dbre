from pathlib import Path


RUNBOOK_DIR = Path(__file__).parent.parent / "runbooks"


def load_runbook(file_path):
    """Markdown 파일을 읽음."""
    return file_path.read_text(encoding="utf-8")


def split_into_chunks(content):
    """Markdown의 ## 섹션을 기준으로 Chunk를 생성함."""

    chunks = []

    current_section = None
    current_lines = []

    for line in content.splitlines():

        # ## 로 시작하면 새로운 Section
        if line.startswith("## "):

            # 이전 Section이 있으면 Chunk로 저장
            if current_section is not None:
                chunks.append({
                    "section": current_section,
                    "content": "\n".join(current_lines).strip()
                })

            # 새로운 Section 시작
            current_section = line.replace("## ", "").strip()
            current_lines = []

        # Section 안의 내용 저장
        elif current_section is not None:
            current_lines.append(line)

    # 마지막 Section 저장
    if current_section is not None:
        chunks.append({
            "section": current_section,
            "content": "\n".join(current_lines).strip()
        })

    return chunks

# ======================================================

file_path = RUNBOOK_DIR / "connection-spike.md"

content = load_runbook(file_path)

chunks = split_into_chunks(content)


for chunk_no, chunk in enumerate(chunks, start=1):

    print("=" * 60)
    print(f"Chunk No : {chunk_no}")
    print(f"Source   : {file_path.name}")
    print(f"Section  : {chunk['section']}")
    print("-" * 60)
    print(chunk["content"])
    print()
