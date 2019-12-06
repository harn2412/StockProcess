"""Lay du lieu tu trang web Cafef
Day la phien ban su dung ten gia tri de lam index thay vi id"""

import requests
from bs4 import BeautifulSoup as BeauSoup
import re
import numpy
import logging
import os
import pandas
from time import sleep
from math import ceil

# Cau hinh luu syslog cho chuong trinh
logger = logging.getLogger('pingdetect')
logger.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              datefmt='%y-%m-%d %H:%M:%S')

# Khai bao log Handler de ghi ket qua vao file log
file = logging.FileHandler('result.log', 'a', 'utf-8')
file.setLevel(logging.DEBUG)
file.setFormatter(formatter)
logger.addHandler(file)

# Khai bao log Handler de in ket qua ra ngoai man hinh
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)


def convert_to_number(text):
    """Chuyen doi ket qua thanh so int hoac so float"""

    pattern = re.compile(r'-?[\d,.]+')
    search_result = pattern.search(text)
    logger.debug('"search_result" VAR is: %s' % search_result)

    if search_result is not None:
        num_text = search_result.group().replace(',', '')
        logger.debug('"num_text" VAR is: %s' % num_text)

        try:  # thu chuyen thanh so int
            result = int(num_text)
            logger.info('Chuyen doi qua INT thanh cong, gia tri la: %s' % result)
        except ValueError:
            logger.info('Chuyen doi qua INT that bai')
            try:  # thu chuyen thanh so float
                result = float(num_text)
                logger.info('Chuyen doi qua FLOAT thanh cong, gia tri la: %s' % result)
            except ValueError:
                logger.warning('Khong the chuyen doi "%s" ra INT hoac FLOAT' % num_text)
                print('Khong phai Int hoac Float')
                result = numpy.nan

    else:
        result = numpy.nan

    return result


def get_index_name(text):
    """Lam dep phan ten cua cac thong so"""

    pattern = re.compile(r'\s*(\w.*\w)\s*')
    search_result = pattern.search(text)

    logger.debug('"search_result" VAR is: %s' % search_result)

    if search_result is not None:

        index_name = search_result.group(1)
        logger.info('Chuyen doi thanh cong, ket qua thu duoc: %s' % index_name)
        return index_name

    else:
        logger.warning('Khong the lam dep phan ten thong so')
        return text


def get_data(page_soup):
    """Lay cac du lieu co trong trang"""

    table_content = page_soup.find('table', {'id': 'tableContent'})

    if table_content is None:
        logger.warning('Khong tim thay tableContent')
        return None

    else:
        logger.debug('"table_content" VAR is: %s' % table_content)

        # Danh sach cac thong so
        index_names = []

        # Du lieu trong bang
        datas = []

        rows = table_content.findAll('tr', {'class': ['r_item', 'r_item_a']})
        logger.debug('"rows" VAR is: %s' % rows)

        for row in rows:
            logger.debug('"row" VAR is: %s' % row)
            # # bo qua cac hang an vi khong can thiet
            # tr_style = row.get('style')
            # if tr_style is not None and 'display:none' in tr_style:
            #     logger.info('Phat hien hang bi an, tien hanh bo qua')
            #     continue

            cells = row.find_all('td', {'class': 'b_r_c'})
            logger.debug('"cells" VAR is: %s' % cells)

            # Cell dau tien ten cua thong so (value name)
            value_name = get_index_name(cells[0].text)
            logger.debug('"value_name" VAR is: %s' % value_name)
            index_names.append(value_name)

            # 4 cell ke tiep la du lieu can lay trong hang
            row_data = [
                convert_to_number(cells[1].text),
                convert_to_number(cells[2].text),
                convert_to_number(cells[3].text),
                convert_to_number(cells[4].text),
            ]
            logger.debug('"row_data" VAR is: %s' % row_data)
            datas.append(row_data)

    logger.debug('"index_name" VAR is: %s' % index_names)
    logger.debug('"data" VAR is: %s' % datas)

    return index_names, datas


def create_stock_list(text):
    """Lam ra danh sach cac ma co phieu"""
    pattern = re.compile(r'[\w\d]+')
    stocks = pattern.findall(text)
    return stocks


def create_option_list(text):
    """Lam ra danh sach cac tuy chon bao cao muon tai ve"""
    pattern = re.compile(r'[1234]+')
    options = tuple([int(opt_text) for opt_text in pattern.findall(text)])
    if 4 in options:
        return 1, 2, 3
    else:
        return options


def get_current_year_quarter():
    """Lay nam va quy hien tai"""
    from datetime import datetime
    now = datetime.now()
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    return current_year, current_quarter


def create_year_quarter_header(last_year, last_quarter, how_many):
    """Tao mot danh sach cac quy va nam dem lui tuong ung voi nam cuoi cung
    :type last_year: int
    :type last_quarter: int
    :type how_many: int
    """

    dump_quarters = [4, 3, 2, 1]
    quarters = dump_quarters[-last_quarter:] + dump_quarters[:-last_quarter]

    # Tao chui cac quy tuong ung do dai can thiet
    long_quarters = quarters * int(ceil(how_many / 4))
    quarters = long_quarters[:how_many]

    headers = []
    for quarter in quarters:
        if quarter == 4:
            last_year -= 1
        header = 'Quý {}-{}'.format(quarter, last_year)
        headers.append(header)

    headers.reverse()  # de cho dung voi bo cuc cua data

    return headers


def countdown_quarter(year, quarter, step):
    """Dem lui quy
    :type year: int
    :type quarter: int
    :type step: int
    """
    year_quarter_list = []

    for i in range(step):
        if quarter > 1:
            quarter -= 1
        else:
            quarter = 4
            year -= 1

        year_quarter_list.append((year, quarter))

    return year_quarter_list


def get_data_of_many_quarter(stock, style, name, how_many_quarter):
    """Lay du lieu trong nhieu quy va tong hop lai thanh mot bang"""

    df = None
    year, quarter = get_current_year_quarter()
    quarter -= 1  # vi quy hien tai chac chan khong co du lieu

    url_template = ('http://s.cafef.vn/bao-cao-tai-chinh/{stock_id}/'
                    '{report_style}/'
                    '{year}/{quarter}/0/0/0/'
                    '{report_name}.chn')

    url = url_template.format(
        stock_id=stock,
        report_style=style,
        year=year,
        quarter=quarter,
        report_name=name,
    )

    logger.debug('"url" VAR is: %s' % url)

    columns = create_year_quarter_header(year, quarter, 4)
    logger.debug('"colums" VAR is: %s' % columns)

    # kiem thu xem Quy hien tai co du lieu hay khong?
    right_quarter = False
    retry = 0

    while right_quarter is not True:
        try_time = 10
        for i in range(0, try_time):
            page = requests.get(url)
            page.raise_for_status()
            soup = BeauSoup(page.content, 'lxml')

            index_names, data = get_data(soup)
            dump_df = pandas.DataFrame(data, index=index_names, columns=columns)
            dump_df = dump_df.fillna(0)
            logger.debug('"dump_df" VAR is: %s' % dump_df)
            last_column = dump_df[columns[-1]].tolist()
            logger.debug('"last_column" VAR is: %s' % last_column)

            if set(last_column) == {0}:
                print('Khong tim thay du lieu, thu tai lai trang ...')
            else:
                right_quarter = True
                df = dump_df
                break
            sleep(3)

        else:
            print('Khong tim thay du lieu trong cot "%s"' % columns[-1])
            print('Lui lai mot quy de lay du lieu')
            retry += 1
            print("Tien hanh cap nhat lai thong tin URL va du lieu tuong ung")
            year, quarter = countdown_quarter(year, quarter, 1)[-1]
            url = url_template.format(
                stock_id=stock,
                report_style=style,
                year=year,
                quarter=quarter,
                report_name=name,
            )
            columns = create_year_quarter_header(year, quarter, 4)
            print("Da cap nhat lai URL moi voi gia tri: %s" % url)
            print("Tien hanh thu lai lan %s" % retry)

        if retry >= 3:
            print('Khong the tim thay du lieu trong cot cuoi cung, de nghi kiem tra lai')
            break
    else:
        print('Da tim thay du lieu cho cot cuoi cung')

    if right_quarter is False:
        return None

    # Neu tim thay quy chinh xac thi tien hanh lay du lieu
    # Tiep tuc tai cac du lieu con thieu
    if how_many_quarter > 4:
        full_quarter_list = countdown_quarter(year, quarter, how_many_quarter - 4)
        logger.debug('"full_quarter_list" VAR is: %s' % full_quarter_list)
        for year, quarter in full_quarter_list[3::4]:  # bat dau tu 3 la vi gia tri dau tien da tien len 1 san
            url = url_template.format(
                stock_id=stock,
                report_style=style,
                year=year,
                quarter=quarter,
                report_name=name,
            )
            page = requests.get(url)
            page.raise_for_status()
            soup = BeauSoup(page.content, 'lxml')

            index_names, data = get_data(soup)
            columns = create_year_quarter_header(year, quarter, 4)
            logger.debug('"columns" VAR is: %s' % columns)
            dump_df = pandas.DataFrame(data, index=index_names, columns=columns)

            # df = dump_df.merge(df, how='outer', right_index=True, left_index=True)
            df = pandas.concat([dump_df, df], axis=1)

    # df = customize_report(df)
    logger.debug('"df" VAR is: %s' % df)
    df_header = df.columns
    logger.debug('"df" VAR is: %s' % df_header)
    how_long = '{}-{}'.format(df_header[0], df_header[-1])
    return how_long, df


report_style = {
    1: ('can-doi-ke-toan', 'BSheet', 'bs [{}].csv'),
    2: ('ket-qua-hoat-dong-kinh-doanh', 'IncSta', 'ist [{}].csv'),
    3: ('luu-chuyen-tien-te-gian-tiep', 'CashFlow', 'cf [{}].csv'),
}


def customize_report(report):
    """Hieu chinh lai DataFrame report"""

    # Thay the cac ket qua NaN bang 0
    report = report.fillna(0)
    logger.debug('"report" VAR is: % s' % report)

    for column in report.columns:
        logger.debug('"column" VAR is: %s' % column)
        # Kiem tra va xoa cac hang khong chua du lieu
        if set(report[column].to_list()) == {0}:
            # y nghia la cot chi co chua gia tri 0
            report = report.drop(column, axis=1)
            logger.info('Cot "%s" khong co gia tri, tien hanh xoa' % column)
            continue

        # Doi cac gia tri ve INT cho gon nhe
        report[column] = pandas.to_numeric(report[column], downcast='signed')

    return report


def main():
    # Duong dan cua thu muc cai dat
    installed_dir = os.path.dirname(os.path.realpath(__file__))
    logger.info('Thu muc cai dat la: %s' % installed_dir)

    # Tao thu muc chua ket qua
    database_dir = os.path.join(installed_dir, 'database')
    os.makedirs(database_dir, exist_ok=True)
    logger.info('Khoi tao thu muc chua ket qua: %s' % database_dir)

    # Lay danh sach cac co phieu muon lay du lieu
    print('Nhap vao cac ma co phieu muon lay du lieu, '
          'cac ma co phieu phan cach nhau bang dau phay ",". '
          'Vi du: fpt, aaa, vnm')

    input_text = input('Cac ma co phieu: ')
    stocks = create_stock_list(input_text)

    # Danh sach cac co phieu bi thieu du lieu Quy gan nhat
    loss_last_quarter = []
    # Danh sach cac co phieu bi thieu hoan toan du lieu
    loss_report = []

    print('Nhap vao so thu tu cac loai bao cao ban muon su dung\n'
          '\t[1] Can doi ke toan\n'
          '\t[2] Ket qua hoat dong kinh doanh\n'
          '\t[3] Luu chuyen tien te gian tiep\n'
          '\t[4] Tai tat ca\n'
          'Co the tai mot hoac nhieu loai bao cao va phan cach bang dau phay ",". Vi du: 1, 2 hoac 1, 3')

    input_text = input('Tuy chon: ')
    options = create_option_list(input_text)

    for stock in stocks:
        print('===***===')
        print('Dang tien hanh su ly ma co phieu "%s"' % stock)
        # Tao thu muc cho ma co phieu
        stock_dir = os.path.join(database_dir, stock)
        os.makedirs(stock_dir, exist_ok=True)
        logger.info('Khoi tao thu muc cho ma co phieu "%s"' % stock)

        for option in options:
            report_long_name = report_style[option][0]
            report_short_name = report_style[option][1]
            how_many_quarter = 8
            report = get_data_of_many_quarter(stock,
                                              report_short_name,
                                              report_long_name,
                                              how_many_quarter)

            # Ghi nhan loi khong tim thay du lieu
            if report is None:
                logger.warning('"%s" Khong tim thay du lieu cua bao cao "%s"' % (stock, report_long_name))
                loss_report.append((stock, report_long_name))
                continue

            how_long, data_frame = report

            # Ghi nhan cac co phieu thieu du lieu cua quy gan nhat
            year, quarter = get_current_year_quarter()
            year, quarter = countdown_quarter(year, quarter, 1)[0]
            last_quarter = 'Quý {}-{}'.format(quarter, year)
            if list(data_frame)[-1] != last_quarter:
                logger.warning(
                    '"%s" Khong tim thay du lieu cua quy gan nhat cua bao cao "%s"' % (stock, report_long_name))
                loss_last_quarter.append((stock, report_long_name))

            # luu thanh file ket qua
            file_patch = os.path.join(stock_dir, report_style[option][2].format(how_long))
            data_frame.to_csv(file_patch)
            logger.info('Da luu file "%s" thanh cong' % file_patch)

        print('Da su ly xong ma co phieu "%s", chuan bi chuyen qua ma tiep theo ...' % stock)

    if loss_last_quarter:
        print('Cac co phieu bi thieu du lieu Quy gan nhat, bao gom: ')
        for stock, report_long_name in loss_last_quarter:
            print('\t- "{}": {}'.format(stock, report_long_name))

    if loss_report:
        print('Cac co phieu khong tim thay du lieu, bao gom: ')
        for stock, report_long_name in loss_report:
            print('\t- "{}": {}'.format(stock, report_long_name))


if __name__ == '__main__':
    main()
