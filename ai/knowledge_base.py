from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"


def load_knowledge_base() -> str:
    """Reads all .txt and .md files from knowledge_base folder and returns one string."""
    content_parts = []
    
    # Find all .txt and .md files
    for file_path in sorted(KB_DIR.glob("*")):
        if file_path.suffix in (".txt", ".md"):
            content_parts.append(f"\n--- {file_path.name.upper()} ---\n")
            content_parts.append(file_path.read_text(encoding="utf-8"))
    
    return "\n".join(content_parts)


# Test it
if __name__ == "__main__":
    kb = load_knowledge_base()
    print(kb[:500])  # Print first 500 characters
    print(f"\n\nTotal characters: {len(kb)}")