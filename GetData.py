"""Lay du lieu tu trang web Cafef
Day la phien ban su dung ten gia tri de lam index thay vi id"""

import requests
from bs4 import BeautifulSoup as BeauSoup
import re
import numpy
import logging
import os
import pandas

# Cau hinh luu syslog cho chuong trinh
logger = logging.getLogger('pingdetect')
# logger.setLevel(logging.DEBUG)
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
        index_names = []

        # Du lieu trong bang
        datas = []

        rows = table_content.findAll('tr', {'class': ['r_item', 'r_item_a']})
        logger.debug('"rows" VAR is: %s' % rows)

        for row in rows:
            logger.debug('"row" VAR is: %s' % row)
            # bo qua cac hang an vi khong can thiet
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
    pattern = re.compile(r'[12345]+')
    options = tuple([int(opt_text) for opt_text in pattern.findall(text)])
    if 5 in options:
        return 1, 2, 3, 4
    else:
        return options


def get_current_year():
    """Lay nam hien tai"""
    from datetime import datetime
    current_year = datetime.now().year
    return current_year


def is_empty(pandas_data):
    """Kiem tra xem co thu duoc du lieu nao hay khong?
    Tra ve True neu khong co du lieu
    Tra ve False neu co du lieu
    Du lieu dau vao la pandas.DataFrame hoac pandas.Serial
    """

    if isinstance(pandas_data, pandas.DataFrame):
        return pandas_data.isnull().to_numpy().all()
    elif isinstance(pandas_data, pandas.Series):
        return pandas_data.isnull().all()
    else:
        raise TypeError("Du lieu dau vao phai la pandas.Serial hoac pandas.DataFrame")


def get_data_of_many_year(stock, style, name, how_many_year, urlname):
    """Lay du lieu trong nhieu nam va tong hop lai thanh mot bang"""

    df = []
    # year = get_current_year()
    year = 2018  # dung tam trong thoi gian cap nhat cach tinh nam

    url_template = ('http://s.cafef.vn/bao-cao-tai-chinh/{stock_id}/'
                    '{report_style}/'
                    '{year}/0/0/0/0/'
                    '{report_name}-'
                    '{urlname}.chn')

    url = url_template.format(
        stock_id=stock,
        report_style=style,
        year=year,
        report_name=name,
        urlname=urlname,
    )
    logger.debug('"url" VAR is: %s' % url)

    page = requests.get(url)
    page.raise_for_status()

    soup = BeauSoup(page.content, 'lxml')

    years = get_years(soup)
    logger.debug('"years" VAR is: %s' % years)

    # Kiem tra xem nam cuoi cung co du lieu khong
    # while True:

    for year in range(year, year - how_many_year, -4):
        if df is not None:
            # muc dich la tranh phai tai lai trang web mot cach khong can thiet
            url = url_template.format(
                stock_id=stock,
                report_style=style,
                year=year,
                report_name=name,
                urlname=urlname,
            )

            page = requests.get(url)
            page.raise_for_status()

            soup = BeauSoup(page.content, 'lxml')

        # Danh sach cac nam hien co
        years = get_years(soup)

        # Du lieu va chi muc hien tai
        index_names, data = get_data(soup)

        # Tao Dataframe cho cac nam hien tai
        dump_df = pandas.DataFrame(data=data, index=index_names, columns=years)
        dump_df = customize_report(dump_df)
        logger.debug('"dump_df" VAR is: %s' % dump_df)

        how_long = "{first} - {last}".format(first=years[0], last=years[-1])

        df.append((how_long, dump_df))
        logger.debug('"df" VAR is: %s' % df)

    logger.debug('Last "df" VAR is % s' % df)
    return df


report_style = {
    1: ('can-doi-ke-toan', 'BSheet', 'bs [{}].csv'),
    2: ('ket-qua-hoat-dong-kinh-doanh', 'IncSta', 'ist [{}].csv'),
    3: ('luu-chuyen-tien-te-gian-tiep', 'CashFlow', 'cfg [{}].csv'),
    4: ('luu-chuyen-tien-te-truc-tiep', 'CashFlowDirect', 'cft [{}].csv'),
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
    stocks = create_stock_list(input_text.upper())

    print('Nhap vao so thu tu cac loai bao cao ban muon su dung\n'
          '\t[1] Can doi ke toan\n'
          '\t[2] Ket qua hoat dong kinh doanh\n'
          '\t[3] Luu chuyen tien te gian tiep\n'
          '\t[4] Luu chuyen tien te truc tiep\n'
          '\t[5] Tai tat ca\n'
          'Co the tai mot hoac nhieu loai bao cao va phan cach bang dau phay ",". Vi du: 1, 2 hoac 1, 3')

    input_text = input('Tuy chon: ')
    options = create_option_list(input_text)

    # Tai thong tin cua cac ma chung khoan dang niem yet
    basestocks_df = pandas.read_csv('basestocks.csv')
    # Chuyen Index qua cot Symbol (ma chung khoan)
    basestocks_df = basestocks_df.set_index('Symbol')

    for stock in stocks:
        print(f'Chuan bi xu ly ma co phie "{stock}"')
        # Tao thu muc cho ma co phieu
        stock_dir = os.path.join(database_dir, stock)
        os.makedirs(stock_dir, exist_ok=True)
        logger.info('Khoi tao thu muc cho ma co phieu "%s"' % stock)

        # Lay ten cong ty dung cho viec tao duong dan
        try:
            urlname = basestocks_df.at[stock, 'URLName']
        except KeyError:
            print('Khong tim thay ma chung khoan %s trong danh sach niem yet' % stock)
            print('Tien hanh bo qua')
            continue

        for option in options:
            print(f'Chuan bi lay du lieu bao cao "{report_style[option][0]}"')
            report = get_data_of_many_year(stock, report_style[option][1], report_style[option][0], 4, urlname)
            logger.debug('"report" VAR is: %s' % report)
            print(f'Da lay du lieu cua bao cao')

            # luu thanh file ket qua
            for child_report in report:
                how_long, data_frame = child_report

                # Kiem tra xem bang bao cao co du lieu khong
                if is_empty(data_frame):
                    print(f'"{stock}" Khong co du lieu cua bao cao "{report_style[option][0]}"')
                    continue

                print('Chuan bi luu thanh file ket qua')

                file_patch = os.path.join(stock_dir, report_style[option][2].format(how_long))
                data_frame.to_csv(file_patch)
                print('Da luu file "%s" thanh cong' % file_patch)


if __name__ == '__main__':
    main()
    input('Press Enter to quit!')
