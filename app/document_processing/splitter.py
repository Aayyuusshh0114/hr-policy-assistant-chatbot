import re


class TextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("Invalid chunk size or overlap.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_pages(self, pages: list[str]) -> list[list[str]]:
        return [self.split_text(page) for page in pages]

    def split_text(self, text: str) -> list[str]:
        normalized = re.sub(r"[ \t]+", " ", text)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            maximum_end = min(start + self.chunk_size, len(normalized))
            end = maximum_end

            if maximum_end < len(normalized):
                search_start = start + self.chunk_size // 2
                candidates = [
                    normalized.rfind(separator, search_start, maximum_end)
                    for separator in ("\n\n", "\n", ". ", " ")
                ]
                boundary = max(candidates)
                if boundary > start:
                    end = boundary + (1 if normalized[boundary] == "." else 0)

            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(normalized):
                break
            start = max(end - self.chunk_overlap, start + 1)

        return chunks

