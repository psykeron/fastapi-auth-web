from typing import Generator, List, Tuple, TypeVar

T = TypeVar("T")
_TOTAL_CHUNKS_TYPE = int
_CURRENT_CHUNK_TYPE = int


def chunks(
    lst: List[T], n: int
) -> Generator[Tuple[_CURRENT_CHUNK_TYPE, _TOTAL_CHUNKS_TYPE, List[T]], None, None]:
    if n <= 0:
        raise ValueError("n must be greater than 0")

    total_chunks = len(lst) / n
    total_chunks = int(total_chunks) + 1 if total_chunks % 1 != 0 else int(total_chunks)
    current_chunk = 0
    for i in range(0, len(lst), n):
        current_chunk += 1
        yield current_chunk, total_chunks, lst[i : i + n]
