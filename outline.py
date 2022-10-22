from collections import OrderedDict
from typing import Optional
from PyPDF2 import PdfReader, PdfWriter, generic, constants
from re import match


def get_writer_with_content(reader: PdfReader):
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(reader.metadata)
    writer.clone_reader_document_root(reader)
    # bugfix
    del writer._root_object[constants.Core.OUTLINES]
    return writer


def copy_outline_from_obj(writer: PdfWriter, outline_obj_list: list[dict],
                          parent: Optional[generic.IndirectObject] = None):
    for entry in outline_obj_list:
        outline_item = writer.add_outline_item(entry["title"], entry["page"], parent=parent)
        if "children" in entry:
            copy_outline_from_obj(writer, entry["children"], outline_item)


def get_outline_obj(reader: PdfReader, outline, d=0):
    result = []
    parent = None
    for item, index in zip(outline, range(len(outline))):
        if isinstance(item, list):
            parent['children'] = get_outline_obj(reader, item, d=d + 1)
        else:
            # print(d, index, item.title)
            result.append({
                "title": item.title,
                "page": reader.get_destination_page_number(item)
                if isinstance(item.page, generic.IndirectObject) else item.page
            })
            parent = result[-1]
    return result


def from_txt_to_outline_obj(text, page_offset):
    def get_indent(depth):
        return " " * 4 * depth

    def parse_data(text, page_offset):
        m = match(r"(.*) \((\d+)\)$", text)
        if not m:
            m = match(r"(.*) \(#(\d+)\)$", text)
            page_offset = 0
        return {
            "title": m.group(1).strip(),
            "page": int(m.group(2)) - 1 + page_offset
        }

    outline_entries: list[str] = text.split("\n")
    root = []
    ancestors = []
    previous_entry_obj = None
    depth = 0
    parent = None
    for text_outline_entry in outline_entries:
        entry_obj = OrderedDict(parse_data(text_outline_entry, page_offset))
        # deeper depth
        if text_outline_entry.startswith(get_indent(depth + 1)):
            ancestors.append(previous_entry_obj)
            parent = previous_entry_obj
            depth += 1
        # same depth
        elif text_outline_entry.startswith(get_indent(depth)):
            pass
        # shallower depth
        else:
            next_depth = next(
                filter(lambda d: text_outline_entry.startswith(get_indent(d)), reversed(range(depth + 1))))
            for i in range(depth - next_depth):
                ancestors.pop()
            depth = next_depth
            parent = ancestors[-1] if len(ancestors) > 0 else None
        if parent:
            parent["children"] = parent.get("children", None) or []
            parent["children"].append(entry_obj)
        else:
            root.append(entry_obj)
        previous_entry_obj = entry_obj
    return root


def outline_obj_to_txt_outline(outline_obj, page_offset=0):
    def to_list(obj):
        result = []
        for outline_entry in obj:
            page = outline_entry["page"] + 1 - page_offset
            result.append(f'{outline_entry["title"]} ({page if page >= 0 else "#" + str(page + page_offset)})')
            if "children" in outline_entry:
                for child in to_list(outline_entry["children"]):
                    result.append(" " * 4 + child)
        return result

    return "\n".join(to_list(outline_obj))


def export_outline(pdf_path, output_path, page_offset=0):
    reader = PdfReader(pdf_path)
    obj = get_outline_obj(reader, reader.outline)
    txt_outline = outline_obj_to_txt_outline(obj, page_offset)
    with open(output_path, "w") as f:
        f.write(txt_outline)


def import_outline(pdf_path, input_path, page_offset=0):
    with open(input_path, "r") as f:
        outline_obj = from_txt_to_outline_obj(f.read(), page_offset)

    reader = PdfReader(pdf_path)
    writer = get_writer_with_content(reader)
    copy_outline_from_obj(writer, outline_obj)
    writer.write(pdf_path)
