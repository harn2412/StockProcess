"""Dung de cap nhat danh sach cac co phieu va
 lay phan ten dung cho vao duong dan khi lay du lieu"""

import re


def raw(url):
    """Lay du lieu json cua cac cong ty niem yet va tra ve dang type"""
    import requests
    import json
    # ma nguon trang web
    data_raw = requests.get(url).text
    # trich xuat du lieu json cac cong ty tu ma nguon
    data_json = json.loads(re.search(r'jsonData = (.*);', data_raw).group(1))

    return tuple(data_json)


def urlname(symbol, url):
    """Lay phan ten cong ty dung cho duong dan URL"""

    pattern = f'{symbol}-(.*)\\.chn'
    name = re.search(pattern, url)
    if not name:
        raise ValueError('Khong tim ra ten cong ty trong URL')

    return name.group(1)


if __name__ == "__main__":
    import pandas
    import os

    # Duong dan de lay du lieu cac cong ty dang niem yet
    data_url = "http://s.cafef.vn/screener.aspx#data"

    # Noi luu tap tin ket qua
    pwd = os.getcwd()
    filename = 'basestocks.csv'
    filepatch = os.path.join(pwd, filename)

    # Tao DataFrame tu du lieu cac cong ty thu duoc
    data = raw(data_url)
    data_df = pandas.DataFrame(data)

    # Chuyen Index qua Symbol (Ma chung khoang cua cong ty)
    # data_df = data_df.set_index('Symbol')

    # Tao them cot URLName chua ten cong ty dung trong URL
    data_df['URLName'] = data_df.apply(
        lambda row: urlname(row['Symbol'], row['Url']), axis=1
    )

    # Luu thanh file ket qua
    data_df.to_csv(filepatch)
