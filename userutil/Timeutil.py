import datetime, os
import pandas as pd

# 0~4 : weekday
# 5,6 : weekend

def getOpenMarketDateFromToday(date=str(20180522)):
# input : yyyymmdd as str
# output : last market openday from today as str
    curtime = datetime.datetime.now().time()

    year = int(date[0:4])
    month = int(date[4:6])
    day = int(date[6:8])

    if curtime.hour >= 0 and curtime.hour < 9:
        if day == 1:
            month = month - 1
            day = 31
        else:
            day = day - 1

    tmpdate = datetime.datetime(year, month, day).strftime("%Y%m%d")

    # print("aa", tmpdate)

    dir = os.path.dirname(os.path.abspath(__file__)).split('userutil')[0]
    excelname = '2018_krx_holiday.xls'
    df_hdays = pd.read_excel(dir+'data\\'+excelname)

    hdays = df_hdays["일자 및 요일"].str.extract('(\d{4}-\d{2}-\d{2})', expand=False)
    hdays = pd.to_datetime(hdays)
    hdays.name = '날짜'

    # adays = pd.date_range('2018-01-01', '2018-12-31')
    mdays = pd.date_range('2018-01-01', '2018-12-31', freq='B')

    mdays = mdays.drop(hdays)

    while True:
        try:
            tmpdate = datetime.datetime(year, month, day).strftime("%Y%m%d")
            mdays.get_loc(tmpdate)
            locno = mdays.get_loc(tmpdate)
            # print("MarketDay was : ", tmpdate, mdays.get_loc(tmpdate))
            # print("MarketDay : ", tmpdate)
            return tmpdate
        except:
            if day == 1:
                month = month - 1
                day = 31
            else:
                day = day - 1

def isWeekend():
# return today as datetime64 type
    today = datetime.datetime.today().strftime("%Y%m%d")
    # if datetime.datetime.today().weekday() is 5:
    #     today = int(today) - 1
    # elif datetime.datetime.today().weekday() is 6:
    #     today = int(today) - 2
    # today = pd.to_datetime(str(today))
    return today

if __name__ == "__main__":
    # getOpenMarketDateFromToday(isWeekend())
    getOpenMarketDateFromToday()

