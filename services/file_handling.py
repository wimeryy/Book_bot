


BOOK_PATH = r'C:\Users\wimer\PycharmProjects\pythonProject\BookBot\Book\book.txt'
PAGE_SIZE = 1050

book: dict[int, str] = {}


def _get_part_text(text: str, start: int, size: int) -> tuple[str, int]:
    ch = ',.!:;?'
    ssize = size
    if len(text) <= size + start:
        ssize = len(text) - start
    else:
        for i in range(size + start - 1, start, -1):
            if text[i] in ch and text[i + 1] not in ch:
                break
            ssize -= 1
    return [text[start: start + ssize], ssize]

def prepare_book(path: str) -> None:
    with open(path, 'r', encoding='utf-8') as file:

        content = file.read()
        page_number = 1

        while content:
            page_text, length = _get_part_text(content, 0, PAGE_SIZE)
            page_text = page_text.lstrip()
            book[page_number] = page_text
            page_number += 1
            content = content[length:]

prepare_book(BOOK_PATH)





