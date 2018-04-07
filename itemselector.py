
from userutil import Kiwoom as kwapi
from userutil import Timeutil as tu
from userutil import Fileutil as fu

import sys, os
import time

import pandas as pd

from PyQt5.QtWidgets import *

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10
FILEDIR = './itemlist'
LastMarketDay = tu.getOpenMarketDateFromToday(tu.isWeekend())
# LastMarketDay=str(20180328)
# print(type(LastMarketDay))

#
class ItemSelector:
    def __init__(self):
        self.kiwoom = kwapi.Kiwoom()
        self.kiwoom.comm_connect()

    def run(self):
        print("running here")

    def get_code_list(self):
        self.kospi_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSPI)
        self.kosdaq_codes = self.kiwoom.get_code_list_by_market(MARKET_KOSDAQ)

    def get_item_daily_price(self, code='033180'):
        self.kiwoom.singlebasket = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': [],
                                    'status': []}
        self.kiwoom.set_input_value("종목코드", code)
        self.kiwoom.set_input_value("조회일자", LastMarketDay)

        self.kiwoom.comm_rq_data("opt10086_req", "opt10086", 0, "0124")

        df = pd.DataFrame(self.kiwoom.singlebasket,
                          columns=['date', 'open', 'high', 'low', 'close', 'volume', 'stauts'],
                          index=self.kiwoom.singlebasket['date'])
        time.sleep(0.3)

        return df

    def get_items_basic_info(self, code='033180'):
        self.kiwoom.basket = {'itemno': [], 'itemname': [], 'open': [], 'high': [], 'low': [],
                              'close': [], 'lastclose': [], 'low250': [], 'volume': [], 'profit': []}
        self.kiwoom.set_input_value("종목코드", code)
        try:
            self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0286")
        except Exception:
            pass
        df = pd.DataFrame(self.kiwoom.basket,
                          columns=['itemno', 'itemname', 'open', 'high', 'low',
                                   'close', 'lastclose', 'low250', 'volume', 'profit'])
        df['profit'].fillna(0)
        time.sleep(0.3)

        return df

    def get_top_volume(self, marketcode=MARKET_KOSPI, sort=1, care=1):
        self.kiwoom.basket = {'itemcode': [], 'itemname': [], 'itemprice': [], 'itemfluct': [], 'itemvolume': [], 'itemamount': [], 'itembefore': []}
        self.kiwoom.set_input_value("시장구분", marketcode)
        self.kiwoom.set_input_value("정렬구분", sort)
        self.kiwoom.set_input_value("관리종목포함", care)
        self.kiwoom.comm_rq_data("opt10030_req", "opt10030", 0, "0184")

        df = pd.DataFrame(self.kiwoom.basket, columns=['itemname', 'itemprice', 'itemfluct', 'itemvolume', 'itemamount', 'itembefore'],
                       index=self.kiwoom.basket['itemcode'])
        # print(df)
        return df

    def merge_and_filter_by_vol_pri_fluct(self, df1, df2):
        frames = [df1, df2]
        df = pd.concat(frames)

        df = df [df['itemvolume'] > 100000]
        df = df [df['itemprice'] > 3000]
        df = df [df ['itemfluct'] > 4]

        df = df.sort_values(by = 'itemvolume', ascending=False)
        return df

    def filter_items(self, df):
        # filter by gap and low250 and add profit
        profits = []
        for oneitem in df.index.values:
            res, profit = self.is_filter_by_gap_low250(oneitem)
            if res:
                df = df.drop(oneitem)
            else:
                profits.append(profit)
        df['profit'] = profits
        df['selection'] = 'x'

        return df


    def is_filter_by_gap_low250(self, code):
        # print(code)
        df = self.get_items_basic_info(code)

        todayopen = df.at[0, 'open']
        lastdayclose = df.at[0, 'lastclose']
        low250 = abs(df.at[0, 'low250'])
        profit = df.at[0, 'profit']

        gap = (todayopen - lastdayclose) / lastdayclose * 100
        # print(code, gap)

        if gap > 5 or todayopen > low250*1.3:
            return True, profit
        else:
            return False, profit

    def drop_etf_item(self, df):
        df.drop(['233740', '263700', '233160', '278240'])

    def stock_item_selector(self):
        # KOSPI 종목 거래량 상위 100 get
        kospi_items = self.get_top_volume('001', 1, 1)
        # KOSDAQ 종목 거래량 상위 100 get
        kosdaq_items = self.get_top_volume('101', 1, 1)
        # 조건식 필터
        df = self.merge_and_filter_by_vol_pri_fluct(kospi_items, kosdaq_items)

        # for oneitem exception without profit:
        # df = df.drop(['950170', '263770'])
        # print(df)

        # 4프로 이상 Gap 필터
        df = self.filter_items(df)
        print(df)
        try:
            df.to_csv(FILEDIR + '/' + str(LastMarketDay) + '.txt', encoding='utf-8')
        except:
            os.mkdir(FILEDIR)
            df.to_csv(FILEDIR + '/' + str(LastMarketDay) + '.txt', encoding='utf-8')
        print("File created in csv")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("Find stock items for " + str(LastMarketDay))
    sl = ItemSelector()
    sl.stock_item_selector()
    fu.uploadfile(FILEDIR, LastMarketDay + '.txt')
    print("today successful finish")