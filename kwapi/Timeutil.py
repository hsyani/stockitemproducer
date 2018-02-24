import datetime

# 0~4 : weekday
# 5,6 : weekend

def gettoday():
    today = datetime.datetime.today().strftime("%Y%m%d")
    if datetime.datetime.today().weekday() is 5:
        today = int(today) - 1
    elif datetime.datetime.today().weekday() is 6:
        today = int(today) - 2

    return today

if __name__ == "__main__":
    gettoday()

