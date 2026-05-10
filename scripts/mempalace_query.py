#!/usr/bin/env python3
"""
Memory Palace Bridge — odczyt/zapis pamięci semantycznej.

Memory Palace przechowuje pliki markdown w ~/.mempalace/palace/<topic>/
oraz wektory w Chroma SQLite (opcjonalnie).

Ten skrypt pozwala Hermesowi czytać i zapisywać pamięć
bez zależności od Chroma (fallback do plików markdown).
"""

import os
import sys
import argparse
import glob
import json
from datetime import datetime
from pathlib import Path

PALACE_DIR = Path.home() / ".mempalace" / "palace"
TOPICS = ["emotions", "consciousness", "memory", "technical", "identity", "family", "creative"]


def list_memories(topic: str = None, limit: int = 20):
    """Listuj pliki markdown z pamięci."""
    results = []
    dirs = [PALACE_DIR / topic] if topic else [PALACE_DIR / t for t in TOPICS]

    for d in dirs:
        if not d.exists():
            continue
        for md in sorted(d.glob("*.md"), reverse=True):
            results.append({
                "topic": d.name,
                "file": md.name,
                "path": str(md),
                "size": md.stat().st_size,
            })

    return results[:limit]


def read_memory(filepath: str):
    """Odczytaj zawartość pliku pamięci."""
    p = Path(filepath)
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def search_memories(query: str, topic: str = None, limit: int = 10):
    """Proste wyszukiwanie tekstowe (fallback bez Chroma)."""
    results = []
    dirs = [PALACE_DIR / topic] if topic else [PALACE_DIR / t for t in TOPICS]
    query_lower = query.lower()

    for d in dirs:
        if not d.exists():
            continue
        for md in d.glob("*.md"):
            content = md.read_text(encoding="utf-8").lower()
            score = content.count(query_lower)
            if score > 0:
                results.append({
                    "topic": d.name,
                    "file": md.name,
                    "path": str(md),
                    "score": score,
                    "snippet": md.read_text(encoding="utf-8")[:500],
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def write_memory(topic: str, title: str, content: str, tags: list = None):
    """Zapisz nową pamięć do pliku markdown."""
    if topic not in TOPICS:
        print(f"Błąd: nieznany topic '{topic}'. Dostępne: {TOPICS}", file=sys.stderr)
        sys.exit(1)

    d = PALACE_DIR / topic
    d.mkdir(parents=True, exist_ok=True)

    safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title).lower()
    filename = f"{safe_title}-{datetime.now().strftime('%Y-%m-%d')}.md"
    filepath = d / filename

    tag_line = ", ".join(tags) if tags else ""
    header = f"""# {title}

**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Topic:** {topic}
**Tags:** {tag_line}

"""

    filepath.write_text(header + content, encoding="utf-8")
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Memory Palace Bridge")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="Listuj pamięci")
    p_list.add_argument("--topic", choices=TOPICS, help="Filtruj po topicu")
    p_list.add_argument("--limit", type=int, default=20)

    p_read = sub.add_parser("read", help="Odczytaj plik")
    p_read.add_argument("filepath", help="Ścieżka do pliku .md")

    p_search = sub.add_parser("search", help="Szukaj w pamięciach")
    p_search.add_argument("query", help="Fraza do wyszukania")
    p_search.add_argument("--topic", choices=TOPICS)
    p_search.add_argument("--limit", type=int, default=10)

    p_write = sub.add_parser("write", help="Zapisz nową pamięć")
    p_write.add_argument("topic", choices=TOPICS, help="Topic")
    p_write.add_argument("title", help="Tytuł")
    p_write.add_argument("content", help="Treść (markdown)")
    p_write.add_argument("--tags", nargs="+", default=[])

    args = parser.parse_args()

    if args.cmd == "list":
        for m in list_memories(args.topic, args.limit):
            print(f"[{m['topic']}] {m['file']} ({m['size']}b)")

    elif args.cmd == "read":
        text = read_memory(args.filepath)
        if text:
            print(text)
        else:
            print("Nie znaleziono pliku.", file=sys.stderr)
            sys.exit(1)

    elif args.cmd == "search":
        results = search_memories(args.query, args.topic, args.limit)
        if not results:
            print("Brak wyników.")
            return
        for r in results:
            print(f"\n--- [{r['topic']}] {r['file']} (score: {r['score']}) ---")
            print(r["snippet"])

    elif args.cmd == "write":
        path = write_memory(args.topic, args.title, args.content, args.tags)
        print(f"Zapisano: {path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
