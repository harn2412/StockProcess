"""
Chuong trinh dung de chuyen doi ket qua CSV thu duoc thanh file Excel theo
mau da tao truoc do
"""

import os
import pandas as pd
from openpyxl import load_workbook
from shutil import copyfile


def dframe_num_format(dframe, csv_type):
    """Function dung de chuyen cac cot thong tin ve gia tri float vi cac
    cot do bi xem nhu str"""

    if csv_type in ('bs.csv', 'ist.csv'):
        start_point = 2
    elif csv_type == 'cf.csv':
        start_point = 1

    for column in dframe.columns[start_point:]:
        dframe[column] = pd.to_numeric(dframe[column], errors='coerce')

    return dframe


def csv_to_excel(csv_dir_path, excel_file_path):
    """Function dung de chuyen cac file bao cao tai chinh vao Worksheet
    tuong ung trong file Excel"""
    
    worksheet_name = {}
    
    for r, d, f in os.walk(csv_dir_path):
    # r: root ; d: directory ; f : file
        for file in f:
            if "bs" in file and "Quý" in file:
                worksheet_name[file] = 'Quarterly BS input (CafeF)'
            elif "bs" in file and "Quý" not in file:
                worksheet_name[file] = 'BS Input (CafeF)'
            elif "cf" in file and "Quý" in file:
                worksheet_name[file] = 'Quarterly CS input (CafeF)'
            elif "cf" in file and "Quý" not in file:
                worksheet_name[file] = 'CS input (CafeF)'
            elif "ist" in file and "Quý" in file:
                worksheet_name[file] = 'Quarterly IS input (Cafef)'
            elif "ist" in file and "Quý" not in file:
                worksheet_name[file] = 'IS input (CafeF)'

    # Mo file Excel dung de luu ket qua
    book = load_workbook(excel_file_path)

    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        # Cac buoc chuan bi de khong bi ghi de file
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

        for csv_file in worksheet_name.keys():
            csv_file_bath = os.path.join(csv_dir_path, csv_file)

            # Kiem tra xem file co ton tai khong
            if os.path.exists(csv_file_bath):
                print('Chuan bi chuyen doi tap tin %s' % csv_file)
                try:
                    dframe = pd.read_csv(csv_file_bath)
                except pd.errors.ParserError:
                    print('file bi loi, tien hanh bo qua')
                    continue

                # Chuyen gia tri ve dang so

                dframe.to_excel(writer, worksheet_name[csv_file], index=False)
                print('Hoan tat chuyen doi.')
            else:
                print('khong tim thay tap tin "%s", tien hanh bo qua' %
                      csv_file)
        writer.save()


def main():
    # Thu muc goc
    cwd = os.getcwd()

    # Thu muc chua du lieu cac co phieu duoi dang CSV
    csv_database_dir = 'database'
    csv_database_dir_path = os.path.join(cwd, csv_database_dir)

    # Thu muc chua du lieu Excel sau khi chuyen doi
    excel_dir_name = 'excel_result'
    excel_dir_path = os.path.join(cwd, excel_dir_name)

    # File Excel mau
    xlsx_template = 'Template.xlsx'

    # Liet ke het tat ca cac ma co phieu (folder) dang co trong thu muc
    # database

    stocks = next(os.walk(csv_database_dir_path))[1]
    print('Danh sach cac ma co phieu: ')
    print(', '.join(stocks))

    # Bat dau qua trinh xu ly
    for stock in stocks:
        print('Chuan bi xu ly ma co phieu "%s" ...' % stock)
        # Duong dan thu muc chua cac tap tin CSV tuong ung voi ma co phieu
        stock_dir_path = os.path.join(csv_database_dir_path, stock)

        # Copy file Excel tuong ung voi ma co phieu
        file_result_path = os.path.join(excel_dir_path, stock + '.xlsx')
        copyfile(xlsx_template, file_result_path)
        print('Da khoi tao file ket qua tai duong dan:')
        print(file_result_path)

        print('Bat dau chuyen doi ...')
        csv_to_excel(stock_dir_path, file_result_path)
        print('Chuyen doi hoan tat.')

    pass


if __name__ == '__main__':
    main()
