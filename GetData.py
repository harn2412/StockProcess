"""Lay du lieu tu trang web Cafef"""

import requests
from bs4 import BeautifulSoup as BeauSoup
import re
import numpy
import logging
import os
import pandas

# Cau hinh luu syslog cho chuong trinh
logger = logging.getLogger('pingdetect')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              datefmt='%y-%m-%d %H:%M:%S')

# Khai bao log Handler de ghi ket qua vao file log
file = logging.FileHandler('result.log')
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

    pattern = re.compile(r'\s*([\w\d].*[\w\d])\s*')
    search_result = pattern.search(text)
    logger.debug('"search_result" VAR is: %s' % search_result)

    if search_result is not None:
        index = search_result.group(1)
        logger.info('Chuyen doi thanh cong, ket qua thu duoc: %s' % index)
        return index

    else:
        logger.warning('Khong the lam dep phan ten thong so')
        return text


def get_years(page_soup):
    """Lay danh sach cac nam hien co trong trang"""

    years_td = page_soup.find_all('td', {'class': 'h_t'})
    logger.debug('"years_td" VAR is: %s' % years_td)

    if years_td is not None:
        years = [convert_to_number(td.text) for td in years_td]
        logger.info('Lay danh sach cac nam thanh cong, gia tri la: %s' % years)
        return years

    else:
        logger.warning('Khong tim thay danh sach cac nam')
        return None


def get_data(page_soup):
    """Lay cac du lieu co trong trang"""

    table_content = page_soup.find('table', {'id': 'tableContent'})

    if table_content is None:
        logger.warning('Khong tim thay tableContent')
        return None

    else:
        logger.debug('"table_content" VAR is: %s' % table_content)

        # Danh sach cac thong so
        index = []

        # Du lieu trong bang
        data = []

        rows = table_content.findAll('tr', {'class': ['r_item', 'r_item_a']})
        logger.debug('"rows" VAR is: %s' % rows)

        for row in rows:
            # bo qua cac hang an vi lam sai lech ket qua
            logger.debug('"row" VAR is: %s' % row)
            if row.find('tr', {'style': 'display:none'}):
                continue

            cells = row.find_all('td', {'class': 'b_r_c'})
            logger.debug('"cells" VAR is: %s' % cells)

            # Cell dau tien ten cua thong so (value name)
            value_name = get_index_name(cells[0].text)
            logger.debug('"value_name" VAR is: %s' % value_name)
            index.append(value_name)

            # 4 cell ke tiep la du lieu can lay trong hang
            row_data = [
                convert_to_number(cells[1].text),
                convert_to_number(cells[2].text),
                convert_to_number(cells[3].text),
                convert_to_number(cells[4].text),
            ]
            logger.debug('"row_data" VAR is: %s' % row_data)
            data.append(row_data)

    logger.debug('"index" VAR is: %s' % index)
    logger.debug('"data" VAR is: %s' % data)

    return index, data


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


def create_report(columns, index, data):
    """tao ra bang bao cao voi Column la cac nam, Index la cac loai thong tin, data la du lieu trong bang"""
    df = pandas.DataFrame(data=data, index=index, columns=columns)
    return df


def get_current_year():
    """Lay nam hien tai"""
    from datetime import datetime
    current_year = datetime.now().year
    return current_year


def get_data_of_many_year(stock, style, name, how_many_year):
    """Lay du lieu trong nhieu nam va tong hop lai thanh mot bang"""

    df = None
    year = get_current_year()

    url_template = ('http://s.cafef.vn/bao-cao-tai-chinh/{stock_id}/'
                    '{report_style}/'
                    '{year}/0/0/0/0/'
                    '{report_name}.chn')

    url = url_template.format(
        stock_id=stock,
        report_style=style,
        year=year,
        report_name=name,
    )

    page = requests.get(url)
    page.raise_for_status()

    soup = BeauSoup(page.content, 'lxml')

    years = get_years(soup)
    year = years[-1]  # cap nhat lai nam cuoi cung trong bang bao cao

    for year in range(year, year - how_many_year, -4):
        if df is not None:
            # muc dich la tranh phai tai lai trang web mot cach khong can thiet
            url = url_template.format(
                stock_id=stock,
                report_style=style,
                year=year,
                report_name=name,
                )

            page = requests.get(url)
            page.raise_for_status()

            soup = BeauSoup(page.content, 'lxml')

        # Danh sach cac nam hien co
        years = get_years(soup)

        # Du lieu va chi muc hien tai
        index, data = get_data(soup)

        # Tao Dataframe cho cac nam hien tai
        dump_df = pandas.DataFrame(data=data, index=index, columns=years)
        logger.debug('"dump_df" VAR is: %s' % dump_df)

        if df is None:
            df = dump_df
        else:
            logger.debug('"df" VAR is: %s' % df)
            temp_a = set(list(df.index.values))
            temp_b = set(list(dump_df.index.values))

            print(temp_a - temp_b)

            df = df.merge(dump_df)

    return df


report_style = {
    1: ('can-doi-ke-toan', 'BSheet'),
    2: ('ket-qua-hoat-dong-kinh-doanh', 'IncSta'),
    3: ('luu-chuyen-tien-te-gian-tiep', 'CashFlow'),
}


def main():

    # Lay danh sach cac co phieu muon lay du lieu
    print('Nhap vao cac ma co phieu muon lay du lieu, '
          'cac ma co phieu phan cach nhau bang dau phay ",". '
          'Vi du: fpt, aaa, vnm')

    input_text = input('Cac ma co phieu: ')
    stocks = create_stock_list(input_text)

    print('Nhap vao so thu tu cac loai bao cao ban muon su dung\n'
          '\t[1] Can doi ke toan\n'
          '\t[2] Ket qua hoat dong kinh doanh\n'
          '\t[3] Luu chuyen tien te gian tiep\n'
          '\t[4] Tai tat ca\n'
          'Co the tai mot hoac nhieu loai bao cao va phan cach bang dau phay ",". Vi du: 1, 2 hoac 1, 3')

    input_text = input('Tuy chon: ')
    options = create_option_list(input_text)

    for stock in stocks:
        for option in options:

            report = get_data_of_many_year(stock, report_style[option][1], report_style[option][0], 10)

            print(report)


if __name__ == '__main__':
    # main()
    url = 'http://s.cafef.vn/bao-cao-tai-chinh/FPT/BSheet/2014/0/0/0/0/bao-cao-tai-chinh-cong-ty-co-phan-fpt.chn'
    page = requests.get(url)
    soup = BeauSoup(page.content, 'lxml')

    print(get_data(soup))
