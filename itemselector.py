
from kwapi import Kiwoom as kwapi
from kwapi import Timeutil as tu

import sys, os
import time

import pandas as pd

from PyQt5.QtWidgets import *
from pandas import DataFrame

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

TODAY = tu.gettoday()

class ItemSelector:
    def __init__(self):
        self.kiwoom = kwapi.Kiwoom()
        self.kiwoom.comm_connect()

    def run(self):
        print("running here")

    def get_code_list(self):
        self.kospi_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSPI)
        self.kosdaq_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSDAQ)


    def get_items_attr(self, code):
        self.kiwoom.singlebasket = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': [],
                                    'status': []}
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("조회일자", TODAY)

        self.kiwoom.comm_rq_data("opt10086_req", "opt10086", 0, "0124")

        df = DataFrame(self.kiwoom.singlebasket, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'stauts'],
                       index=self.kiwoom.singlebasket['date'])
        time.sleep(0.3)

        return df

    def get_top_volume(self, marketcode=MARKET_KOSPI, sort=1, care=1):
        self.kiwoom.basket = {'itemcode': [], 'itemname': [], 'itemprice': [], 'itemfluct': [], 'itemvolume': [], 'itemamount': [], 'itembefore': []}
        self.kiwoom.set_input_value("시장구분", marketcode)
        self.kiwoom.set_input_value("정렬구분", sort)
        self.kiwoom.set_input_value("관리종목포함", care)

        self.kiwoom.comm_rq_data("opt10030_req", "opt10030", 0, "0184")

        df = DataFrame(self.kiwoom.basket, columns=['itemname', 'itemprice', 'itemfluct', 'itemvolume', 'itemamount', 'itembefore'],
                       index=self.kiwoom.basket['itemcode'])

        return df

    def merge_and_filter_by_vol_pri_fluct(self, df1, df2):
        frames = [df1, df2]
        df = pd.concat(frames)

        df = df [df['itemvolume'] > 100000]
        df = df [df['itemprice'] > 3000]
        df = df [df ['itemfluct'] > 5]

        df = df.sort_values(by = 'itemvolume', ascending=False)
        return df

    def filter_by_gap(self, df):
        for oneitem in df.index.values:
            if(self.is_filter_by_gap(oneitem)):
                df = df.drop(oneitem)
        return df


    def is_filter_by_gap(self, code):
        df = self.get_items_attr(code)

        todayopen = df['open'][0]
        lastdayclose = df['close'][1]
        gap = (todayopen - lastdayclose) / lastdayclose * 100
        if gap > 5:
            return True
        else:
            return False


    def stock_item_selector(self):
        # KOSPI 종목 거래량 상위 100 get
        kospi_items = self.get_top_volume('001', 1, 1)
        # KOSDAQ 종목 거래량 상위 100 get
        kosdaq_items = self.get_top_volume('101', 1, 1)
        # 조건식 필터
        df = self.merge_and_filter_by_vol_pri_fluct(kospi_items, kosdaq_items)
        # 5프로 이상 Gap 필터
        df = self.filter_by_gap(df)
        print(df)
        try:
            df.to_csv('./itemlist/'+str(TODAY)+'.csv', encoding='utf-8')
        except:
            os.mkdir('./itemlist/')
            df.to_csv('./itemlist/'+str(TODAY)+'.csv', encoding='utf-8')


if __name__ == "__main__":
    app = QApplication(sys.argv)

    print("Find stock items for " + str(TODAY))
    sl = ItemSelector()
    sl.stock_item_selector()
    print("today successful finish")