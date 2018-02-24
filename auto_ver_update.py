from pywinauto import application
from pywinauto import timings
import time
import os


# Account
with open("private_info.txt", 'r') as f:
    pinfo = f.readlines()
app = application.Application()
app.start("C:/KiwoomFlash3/bin/nkministarter.exe")

title = "번개3 Login"
dlg = timings.WaitUntilPasses(20, 0.5, lambda: app.window_(title=title))

idForm = dlg.Edit0
idForm.SetFocus()
idForm.TypeKeys(pinfo[0])

passForm = dlg.Edit2
passForm.SetFocus()
passForm.TypeKeys(pinfo[1])

certForm = dlg.Edit3
certForm.SetFocus()
certForm.TypeKeys(pinfo[2])

loginBtn = dlg.Button0
loginBtn.Click()

# 업데이트가 완료될 때 까지 대기
while True:
    time.sleep(5)
    with os.popen('tasklist /FI "IMAGENAME eq nkmini.exe"') as f:
        lines = f.readlines()
        if len(lines) >= 3:
            break

# 번개3 종료
time.sleep(30)
os.system("taskkill /im nkmini.exe")

