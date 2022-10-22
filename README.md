# Description

It is a PDF outline editor as an alternative to proprietary PDF editors.

I built it for myself to replace [handyoutliner](https://handyoutlinerfo.sourceforge.net/) that I was not able to run it on macOS. 

# Usage

Export the table of content read from the PDF file
```python
from outline import export_outline, import_outline

if __name__ == "__main__":
    export_outline("target.pdf", "toc.txt", 13)
```

Example of toc.txt (offset 13 has been applied except for the first entry)
```
You can skip offsetting page number with # symbol (#5)
Ch1. First Chapter at page 1 (1)
    Define children with indentation of 4 spaces (5)
        Or children of children (10)
Ch2. Something else at page 30 (30)
```

Import TOC from toc.txt and write to the PDF file
```python
from outline import export_outline, import_outline

if __name__ == "__main__":
    import_outline("target.pdf", "toc.txt", 13)
```