import os

def create_version_file(
    version="1.0.0.0",
    company_name="Your Company",
    file_description="Stratigraphic Column Maker",
    internal_name="stratcol",
    copyright_notice="Copyright © 2025 Your Name",
    original_filename="stratcol.exe",
    product_name="Stratigraphic Column Maker"
):
    
    version_template = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version.replace('.', ',')}),
    prodvers=({version.replace('.', ',')}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{company_name}'),
        StringStruct(u'FileDescription', u'{file_description}'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'{internal_name}'),
        StringStruct(u'LegalCopyright', u'{copyright_notice}'),
        StringStruct(u'OriginalFilename', u'{original_filename}'),
        StringStruct(u'ProductName', u'{product_name}'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_template)
    
    print("version_info.txt created successfully!")

if __name__ == "__main__":
    create_version_file(
        version="1.0.0.0",
        company_name="EGI",
        file_description="Stratigraphic Column Maker - A tool for creating geological stratigraphic columns",
        internal_name="stratcol",
        copyright_notice="Copyright © 2025 EGI. All rights reserved.",
        original_filename="Stratigraphic Column Maker.exe",
        product_name="Stratigraphic Column Maker"
    )