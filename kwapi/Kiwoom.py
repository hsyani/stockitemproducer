import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3
from kwapi import Localutil as util
from kwapi import KWutil

TR_REQ_TIME_INTERVAL = 0.2
CONDITION_NAME1 = '검색왕 스켈핑'
CONDITION_NAME2 = '검색왕 스켈핑ver1.0'

sendConditionScreenNo = "001"

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.codelist={}

        self.condition_loop = None

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._on_event_connect)
        self.OnReceiveMsg.connect(self._on_receive_msg)
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.OnReceiveRealData.connect(self._on_receive_real_data)
        self.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.OnReceiveConditionVer.connect(self._on_receivec_condition_ver)
        self.OnReceiveTrCondition.connect(self._on_receive_tr_condition)
        self.OnReceiveRealCondition.connect(self._on_receive_real_condition)

    def _on_event_connect(self, err_code):
        util.debug_parent_prt("")
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()
    def _on_receive_msg(self, scrNo, rQName, trCode, msg):
        util.debug_parent_prt("")

        # print(util.whoami() + 'sScrNo: {}, sRQName: {}, sTrCode: {}, sMsg: {}'
        # .format(scrNo, rQName, trCode, msg))
        '''
              [OnReceiveTrData() 이벤트함수]

          void OnReceiveTrData(
          BSTR sScrNo,       // 화면번호
          BSTR sRQName,      // 사용자 구분명
          BSTR sTrCode,      // TR이름
          BSTR sRecordName,  // 레코드 이름
          BSTR sPrevNext,    // 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 1:연속(추가조회) 데이터 있음
          LONG nDataLength,  // 사용안함.
          BSTR sErrorCode,   // 사용안함.
          BSTR sMessage,     // 사용안함.
          BSTR sSplmMsg     // 사용안함.
          )

          조회요청 응답을 받거나 조회데이터를 수신했을때 호출됩니다.
          조회데이터는 이 이벤트 함수내부에서 GetCommData()함수를 이용해서 얻어올 수 있습니다.
        '''
        printData = 'sScrNo: {}, sRQName: {}, sTrCode: {}, sMsg: {}'.format(scrNo, rQName, trCode, msg)
        util.save_log(printData, "시스템메시지", "log")
        pass
    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        util.debug_parent_prt("")
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10005_req":
            self._opt10005(rqname, trcode)
        elif rqname == "opt10015_req":
            self._opt10015(rqname, trcode)
        elif rqname == "opt10030_req":
            self._opt10030(rqname, trcode)
        elif rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opt10086_req":
            self._opt10086(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass
    def _on_receive_real_data(self, jongmokCode, realType, realData):
        util.debug_parent_prt("")

        # print(util.whoami() + 'jongmokCode: {}, {}, realType: {}'
        #         .format(jongmokCode, self.get_master_code_name(jongmokCode),  realType))
        if( realType == "주식호가잔량"):
            # print(util.whoami() + 'jongmokCode: {}, realType: {}, realData: {}'
            #     .format(jongmokCode, realType, realData))
            if( jongmokCode not in self.buyCodeList == 0 ):
                jongmok_name = self.get_master_code_name(jongmokCode)
                # print(util.whoami() + 'error: ' + jongmokCode + ' ' + jongmok_name, end =' ')
            else:
                self.makeHogaJanRyangInfo(jongmokCode)

        if( realType == "주식체결"):
            # print(util.whoami() + 'jongmokCode: {}, realType: {}, realData: {}'
            #     .format(jongmokCode, realType, realData))
            result = ''
            # 잔고가 있는 상태서 주식 체결 실시간 값이 오는 경우 수익율을 계산함
            if( jongmokCode in self.jangoInfo ):
                for col_name in KWutil.dict_jusik['실시간-주식체결']:
                    result = self.get_comm_real_data(jongmokCode, KWutil.name_fid[col_name])
                    if( col_name == '현재가'):
                        current_price = abs(int(result.strip()))
                        self.calculateSuik(jongmokCode, current_price)
                        break
                self.processStopLoss(jongmokCode)

        if( realType == "업종지수" ):
            result = ''
            for col_name in kw_util.dict_jusik['실시간-업종지수']:
                result = self.get_comm_real_data(jongmokCode, kw_util.name_fid[col_name])
                if( col_name == '등락율'):
                    if( jongmokCode == '001'):
                        self.upjongUpdownPercent['코스피'] = result
                    else:
                        self.upjongUpdownPercent['코스닥'] = result
            pass

        if( realType == '장시작시간'):
            # TODO: 장시작 30분전부터 실시간 정보가 올라오는데 이를 토대로 가변적으로 장시작시간을 가늠할수 있도록 기능 추가 필요
            pass
            # print(util.whoami() + 'jongmokCode: {}, realType: {}, realData: {}'
            #     .format(jongmokCode, realType, realData))

            print(util.whoami() + 'jongmokCode: {}, realType: {}, realData: {}'
                .format(jongmokCode, realType, realData))
            pass
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        util.debug_parent_prt("")
        print(gubun)
        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))
    def _on_receivec_condition_ver(self, ret, msg):
        print(util.whoami() + 'ret: {}, msg: {}'
            .format(ret, msg))
        if ret == 1:
            pass


        # print(util.whoami() + 'ret: {}, msg: {}'
        #     .format(ret, msg))
        # if ret == 1:
        #     print('wow')
    # def _on_receivec_condition_ver(self, ret, msg):
    #     print("OnReceiveConditionVer")
    #     data = self.dynamicCall("GetConditionNameList()")
    #     dataList = data.split(';')
    #     del dataList[-1]
    #     print(dataList)
    #     self.myConditionItem = {}
    #     for myCondition in dataList:
    #         myConditionItem = myCondition.split("^")
    #         self.myConditionItem[myConditionItem[1]] = myConditionItem[0]
    #         print(self.myConditionItem)
    #
    #     self.condition_loop.exit()

    def _on_receive_tr_condition(self, screen_no, codeList, condname, index, next):
        util.debug_parent_prt("")
        codes = codeList.split(';')[:-1]
        # 마지막 split 결과 None 이므로 삭제
        for code in codes:
            print('code: {} '.format(code) + self.get_master_code_name(code))
        pass

        # return self.commKwRqData(codeList, 0, len(codeList), 0, CONDITION_NAME, 10)
    def _on_receive_real_condition(self, code, type, conditionName, conditionIndex):
        util.debug_parent_prt("")

        # print(util.whoami() + 'code: {}, type: {}, conditionName: {}, conditionIndex: {}'
        # .format(code, type, conditionName, conditionIndex ))
        typeName = ''
        if type == 'I':
            typeName = '진입'
        else:
            typeName = '이탈'

        if( typeName == '진입'):
            printLog = '{}, status: {}'.format( self.get_master_code_name(code), typeName)
            self.makeConditionOccurInfo(code) # 조건 발생한 경우 무조건 df 저장
            self.sigConditionOccur.emit()
        pass


    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret
    def commTerminate(self):
        self.dynamicCall("CommTerminate()")
    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)
    def get_code_list_by_market(self, market):
        result = self.dynamicCall("GetCodeListByMarket(QString)", market)
        result = result.split(';')
        return result[:-1]
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        """
        키움서버에 TR 요청을 한다.
        조회요청메서드이며 빈번하게 조회요청시, 시세과부하 에러값 -200이 리턴된다.
        :param request_name: string - TR 요청명(사용자 정의)
        :param tr_code: string
        :param next: int - 조회(0: 조회, 2: 남은 데이터 이어서 요청)
        :param screen_no: string - 화면번호(4자리)
        """
        if not self.get_connect_state():
            raise KiwoomConnectError()

        if not (isinstance(rqname, str)
                and isinstance(trcode, str)
                and isinstance(next, int)
                and isinstance(screen_no, str)):
            raise ParameterTypeError()

        return_code = self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next,
                                       screen_no)

        if return_code != ReturnCode.OP_ERR_NONE:
            raise KiwoomProcessingError("comm_rq_data(): " + ReturnCode.CAUSE[return_code])

        # 루프 생성: receive_tr_data() 메서드에서 루프를 종료시킨다.
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def get_repeat_cnt(self, trcode, rqname):
        result = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return result
    def comm_get_data(self, code, real_type, field_name, index, item_name):
        result = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name).strip()
        return result
    def get_comm_real_data(self, realType, fid):
        return self.dynamicCall("GetCommRealData(QString, int)", realType, fid).strip()
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        return self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret
    def get_condition_load(self):
        return self.dynamicCall("GetConditionLoad()")
        self.condition_loop = QEventLoop()
        self.condition_loop.exec_()
    def get_condition_name_list(self):
        result = self.dynamicCall("GetConditionNameList()")
        if result == "":
            raise KiwoomProcessingError("GetConditionNameList(): 사용자 조건식이 없습니다.")
        return result
    def send_condition(self, scrNo, conditionName, index, search):
        self.dynamicCall("SendCondition(QString, QString, int, int)", scrNo, conditionName, index, search)
        self.conditionLoop = QEventLoop()
        self.conditionLoop.exec_()
    def send_condition_stop(self, scrNo, conditionName, index):
        self.dynamicCall("SendConditionStop(QString, QString, int)", scrNo, conditionName, index)
    def commKwRqData(self, arrCode, next, codeCount, typeFlag, rQName, screenNo):
    	self.dynamicCall("CommKwRqData(QString, QBoolean, int, int, QString, QString)", arrCode, next, codeCount, typeFlag, rQName, screenNo)
    def setRealReg(self, screenNo, codeList, fidList, optType):
        return self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screenNo, codeList, fidList, optType)
    def setRealRemove(self, scrNo, delCode):
        self.dynamicCall("SetRealRemove(QString, QString)", scrNo, delCode)
    def getCommData(self, trCode, recordName, index, itemName):
        return self.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, recordName, index, itemName)
    def getCommDataEx(self, trCode, recordName):
        return self.dynamicCall("GetCommDataEx(QString, QString)", trCode, recordName)
    def disconnectRealData(self, scnNo):
        self.dynamicCall("DisconnectRealData(QString)", scnNo)
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name


    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '' or strip_data == '.00':
            strip_data = '0'

        format_data = format(int(strip_data), ',d')
        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    def requestOpw00018(self, account_num):
        self.set_input_value('계좌번호', account_num)
        self.set_input_value('비밀번호', '')  # 사용안함(공백)
        self.set_input_value('비빌번호입력매체구분', '00')
        self.set_input_value('조회구분', '1')

        ret = self.comm_rq_data(account_num, "opw00018", 0, kw_util.sendJusikAccountInfoScreenNo)
        errorString = None
        if (ret != 0):
            errorString = account_num + " commRqData() " + kw_util.parseErrorCode(str(ret))
            print(util.whoami() + errorString)
            util.save_log(errorString, util.whoami(), folder="log")
            return False
        return True

        pass

    def _opw00001(self, rqname, trcode):
        d2_deposit = self.comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self.comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self.comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self.comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self.comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self.comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))

        total_earning_rate = Kiwoom.change_format2(total_earning_rate)

        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)

        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self.get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self.comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self.comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self.comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self.comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self.comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self.comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price, eval_profit_loss_price,
                                                  earning_rate])


    def _opt10005(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "날짜")
            open = self.comm_get_data(trcode, "", rqname, i, "시가")
            # high = self._comm_get_data(trcode, "", rqname, i, "고가")
            # low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self.comm_get_data(trcode, "", rqname, i, "종가")
            # volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            # fluct = self._comm_get_data(trcode, "", rqname, i, "등락률")

            self.basket['date'].append(date)
            self.basket['open'].append(int(open))
            # self.basket['high'].append(int(high))
            # self.basket['low'].append(int(low))
            self.basket['close'].append(int(close))
            # self.dasket['volume'].append(int(volume))
            # self.basket['fluct'].append(fluct)

    def _opt10015(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "일자")
            price = self.comm_get_data(trcode, "", rqname, i, "종가")

            self.basket['date'].append(date)
            self.basket['price'].append(abs(int(price)))

    def _opt10030(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            itemcode = self.comm_get_data(trcode, "", rqname, i, "종목코드")
            itemname = self.comm_get_data(trcode, "", rqname, i, "종목명")
            itemprice = self.comm_get_data(trcode, "", rqname, i, "현재가")
            itemfluct = self.comm_get_data(trcode, "", rqname, i, "등락률")
            itemvolume = self.comm_get_data(trcode, "", rqname, i, "거래량")
            itemamount = self.comm_get_data(trcode, "", rqname, i, "거래금액")
            itembefore = self.comm_get_data(trcode, "", rqname, i, "전일대비")

            self.basket['itemcode'].append(itemcode)
            self.basket['itemname'].append(itemname)
            self.basket['itemprice'].append(int(itemprice))
            self.basket['itemfluct'].append(float(itemfluct))
            self.basket['itemvolume'].append(int(itemvolume))
            self.basket['itemamount'].append(int(itemamount))
            self.basket['itembefore'].append(int(itembefore))

    def _opt10081(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "일자")
            open = self.comm_get_data(trcode, "", rqname, i, "시가")
            high = self.comm_get_data(trcode, "", rqname, i, "고가")
            low = self.comm_get_data(trcode, "", rqname, i, "저가")
            close = self.comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def _opt10086(self, rqname, trcode):
        data_cnt = self.get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            date = self.comm_get_data(trcode, "", rqname, i, "날짜")
            open = self.comm_get_data(trcode, "", rqname, i, "시가")
            high = self.comm_get_data(trcode, "", rqname, i, "고가")
            low = self.comm_get_data(trcode, "", rqname, i, "저가")
            close = self.comm_get_data(trcode, "", rqname, i, "종가")
            volume = self.comm_get_data(trcode, "", rqname, i, "거래량")

            self.singlebasket['date'].append(date)
            self.singlebasket['open'].append(abs(int(open)))
            self.singlebasket['high'].append(abs(int(high)))
            self.singlebasket['low'].append(abs(int(low)))
            self.singlebasket['close'].append(abs(int(close)))
            self.singlebasket['volume'].append(abs(int(volume)))

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def test_getlist(self):
        print("conditionload : " + str(kiwoom.get_condition_load()))
        print("namelist : " + kiwoom.get_condition_name_list())
        result = kiwoom.send_condition(KWutil.sendConditionScreenNo, CONDITION_NAME2, 1, 0)
        print("sendcondition : " + str(result))


class ParameterTypeError(Exception):
    """ 파라미터 타입이 일치하지 않을 경우 발생하는 예외 """
    def __init__(self, msg="파라미터 타입이 일치하지 않습니다."):
        self.msg = msg
    def __str__(self):
        return self.msg

class ParameterValueError(Exception):
    """ 파라미터로 사용할 수 없는 값을 사용할 경우 발생하는 예외 """

    def __init__(self, msg="파라미터로 사용할 수 없는 값 입니다."):
        self.msg = msg

    def __str__(self):
        return self.msg

class KiwoomProcessingError(Exception):
    """ 키움에서 처리실패에 관련된 리턴코드를 받았을 경우 발생하는 예외 """

    def __init__(self, msg="처리 실패"):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg

class KiwoomConnectError(Exception):
    """ 키움서버에 로그인 상태가 아닐 경우 발생하는 예외 """

    def __init__(self, msg="로그인 여부를 확인하십시오"):
        self.msg = msg

    def __str__(self):
        return self.msg

class ReturnCode(object):
    """ 키움 OpenApi+ 함수들이 반환하는 값 """
    OP_ERR_NONE = 0  # 정상처리
    OP_ERR_FAIL = -10  # 실패
    OP_ERR_LOGIN = -100  # 사용자정보교환실패
    OP_ERR_CONNECT = -101  # 서버접속실패
    OP_ERR_VERSION = -102  # 버전처리실패
    OP_ERR_FIREWALL = -103  # 개인방화벽실패
    OP_ERR_MEMORY = -104  # 메모리보호실패
    OP_ERR_INPUT = -105  # 함수입력값오류
    OP_ERR_SOCKET_CLOSED = -106  # 통신연결종료
    OP_ERR_SISE_OVERFLOW = -200  # 시세조회과부하
    OP_ERR_RQ_STRUCT_FAIL = -201  # 전문작성초기화실패
    OP_ERR_RQ_STRING_FAIL = -202  # 전문작성입력값오류
    OP_ERR_NO_DATA = -203  # 데이터없음
    OP_ERR_OVER_MAX_DATA = -204  # 조회가능한종목수초과
    OP_ERR_DATA_RCV_FAIL = -205  # 데이터수신실패
    OP_ERR_OVER_MAX_FID = -206  # 조회가능한FID수초과
    OP_ERR_REAL_CANCEL = -207  # 실시간해제오류
    OP_ERR_ORD_WRONG_INPUT = -300  # 입력값오류
    OP_ERR_ORD_WRONG_ACCTNO = -301  # 계좌비밀번호없음
    OP_ERR_OTHER_ACC_USE = -302  # 타인계좌사용오류
    OP_ERR_MIS_2BILL_EXC = -303  # 주문가격이20억원을초과
    OP_ERR_MIS_5BILL_EXC = -304  # 주문가격이50억원을초과
    OP_ERR_MIS_1PER_EXC = -305  # 주문수량이총발행주수의1%초과오류
    OP_ERR_MIS_3PER_EXC = -306  # 주문수량이총발행주수의3%초과오류
    OP_ERR_SEND_FAIL = -307  # 주문전송실패
    OP_ERR_ORD_OVERFLOW = -308  # 주문전송과부하
    OP_ERR_MIS_300CNT_EXC = -309  # 주문수량300계약초과
    OP_ERR_MIS_500CNT_EXC = -310  # 주문수량500계약초과
    OP_ERR_ORD_WRONG_ACCTINFO = -340  # 계좌정보없음
    OP_ERR_ORD_SYMCODE_EMPTY = -500  # 종목코드없음

    CAUSE = {
        0: '정상처리',
        -10: '실패',
        -100: '사용자정보교환실패',
        -102: '버전처리실패',
        -103: '개인방화벽실패',
        -104: '메모리보호실패',
        -105: '함수입력값오류',
        -106: '통신연결종료',
        -200: '시세조회과부하',
        -201: '전문작성초기화실패',
        -202: '전문작성입력값오류',
        -203: '데이터없음',
        -204: '조회가능한종목수초과',
        -205: '데이터수신실패',
        -206: '조회가능한FID수초과',
        -207: '실시간해제오류',
        -300: '입력값오류',
        -301: '계좌비밀번호없음',
        -302: '타인계좌사용오류',
        -303: '주문가격이20억원을초과',
        -304: '주문가격이50억원을초과',
        -305: '주문수량이총발행주수의1%초과오류',
        -306: '주문수량이총발행주수의3%초과오류',
        -307: '주문전송실패',
        -308: '주문전송과부하',
        -309: '주문수량300계약초과',
        -310: '주문수량500계약초과',
        -340: '계좌정보없음',
        -500: '종목코드없음'
    }

class FidList(object):
    """ receiveChejanData() 이벤트 메서드로 전달되는 FID 목록 """

    CHEJAN = {
        9201: '계좌번호',
        9203: '주문번호',
        9205: '관리자사번',
        9001: '종목코드',
        912: '주문업무분류',
        913: '주문상태',
        302: '종목명',
        900: '주문수량',
        901: '주문가격',
        902: '미체결수량',
        903: '체결누계금액',
        904: '원주문번호',
        905: '주문구분',
        906: '매매구분',
        907: '매도수구분',
        908: '주문/체결시간',
        909: '체결번호',
        910: '체결가',
        911: '체결량',
        10: '현재가',
        27: '(최우선)매도호가',
        28: '(최우선)매수호가',
        914: '단위체결가',
        915: '단위체결량',
        938: '당일매매수수료',
        939: '당일매매세금',
        919: '거부사유',
        920: '화면번호',
        921: '921',
        922: '922',
        923: '923',
        949: '949',
        10010: '10010',
        917: '신용구분',
        916: '대출일',
        930: '보유수량',
        931: '매입단가',
        932: '총매입가',
        933: '주문가능수량',
        945: '당일순매수수량',
        946: '매도/매수구분',
        950: '당일총매도손일',
        951: '예수금',
        307: '기준가',
        8019: '손익율',
        957: '신용금액',
        958: '신용이자',
        959: '담보대출수량',
        924: '924',
        918: '만기일',
        990: '당일실현손익(유가)',
        991: '당일신현손익률(유가)',
        992: '당일실현손익(신용)',
        993: '당일실현손익률(신용)',
        397: '파생상품거래단위',
        305: '상한가',
        306: '하한가'
    }

class RealType(object):
    REALTYPE = {
        '주식시세': {
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '거일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            311: '시가총액(억)'
        },

        '주식체결': {
            20: '체결시간(HHMMSS)',
            10: '체결가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            15: '체결량',
            13: '누적체결량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '전일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            228: '체결강도',
            311: '시가총액(억)',
            290: '장구분',
            691: 'KO접근도'
        },

        '주식호가잔량': {
            21: '호가시간',
            41: '매도호가1',
            61: '매도호가수량1',
            81: '매도호가직전대비1',
            51: '매수호가1',
            71: '매수호가수량1',
            91: '매수호가직전대비1',
            42: '매도호가2',
            62: '매도호가수량2',
            82: '매도호가직전대비2',
            52: '매수호가2',
            72: '매수호가수량2',
            92: '매수호가직전대비2',
            43: '매도호가3',
            63: '매도호가수량3',
            83: '매도호가직전대비3',
            53: '매수호가3',
            73: '매수호가수량3',
            93: '매수호가직전대비3',
            44: '매도호가4',
            64: '매도호가수량4',
            84: '매도호가직전대비4',
            54: '매수호가4',
            74: '매수호가수량4',
            94: '매수호가직전대비4',
            45: '매도호가5',
            65: '매도호가수량5',
            85: '매도호가직전대비5',
            55: '매수호가5',
            75: '매수호가수량5',
            95: '매수호가직전대비5',
            46: '매도호가6',
            66: '매도호가수량6',
            86: '매도호가직전대비6',
            56: '매수호가6',
            76: '매수호가수량6',
            96: '매수호가직전대비6',
            47: '매도호가7',
            67: '매도호가수량7',
            87: '매도호가직전대비7',
            57: '매수호가7',
            77: '매수호가수량7',
            97: '매수호가직전대비7',
            48: '매도호가8',
            68: '매도호가수량8',
            88: '매도호가직전대비8',
            58: '매수호가8',
            78: '매수호가수량8',
            98: '매수호가직전대비8',
            49: '매도호가9',
            69: '매도호가수량9',
            89: '매도호가직전대비9',
            59: '매수호가9',
            79: '매수호가수량9',
            99: '매수호가직전대비9',
            50: '매도호가10',
            70: '매도호가수량10',
            90: '매도호가직전대비10',
            60: '매수호가10',
            80: '매수호가수량10',
            100: '매수호가직전대비10',
            121: '매도호가총잔량',
            122: '매도호가총잔량직전대비',
            125: '매수호가총잔량',
            126: '매수호가총잔량직전대비',
            23: '예상체결가',
            24: '예상체결수량',
            128: '순매수잔량(총매수잔량-총매도잔량)',
            129: '매수비율',
            138: '순매도잔량(총매도잔량-총매수잔량)',
            139: '매도비율',
            200: '예상체결가전일종가대비',
            201: '예상체결가전일종가대비등락율',
            238: '예상체결가전일종가대비기호',
            291: '예상체결가',
            292: '예상체결량',
            293: '예상체결가전일대비기호',
            294: '예상체결가전일대비',
            295: '예상체결가전일대비등락율',
            13: '누적거래량',
            299: '전일거래량대비예상체결률',
            215: '장운영구분'
        },

        '장시작시간': {
            215: '장운영구분(0:장시작전, 2:장종료전, 3:장시작, 4,8:장종료, 9:장마감)',
            20: '시간(HHMMSS)',
            214: '장시작예상잔여시간'
        },

        '업종지수': {
            20: '체결시간',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            15: '거래량',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비(계약,주)'
        },

        '업종등락': {
            20: '체결시간',
            252: '상승종목수',
            251: '상한종목수',
            253: '보합종목수',
            255: '하락종목수',
            254: '하한종목수',
            13: '누적거래량',
            14: '누적거래대금',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            256: '거래형성종목수',
            257: '거래형성비율',
            25: '전일대비기호'
        },

        '주문체결': {
            9201: '계좌번호',
            9203: '주문번호',
            9205: '관리자사번',
            9001: '종목코드',
            912: '주문분류(jj:주식주문)',
            913: '주문상태(10:원주문, 11:정정주문, 12:취소주문, 20:주문확인, 21:정정확인, 22:취소확인, 90,92:주문거부)',
            302: '종목명',
            900: '주문수량',
            901: '주문가격',
            902: '미체결수량',
            903: '체결누계금액',
            904: '원주문번호',
            905: '주문구분(+:현금매수, -:현금매도)',
            906: '매매구분(보통, 시장가등)',
            907: '매도수구분(1:매도, 2:매수)',
            908: '체결시간(HHMMSS)',
            909: '체결번호',
            910: '체결가',
            911: '체결량',
            10: '체결가',
            27: '최우선매도호가',
            28: '최우선매수호가',
            914: '단위체결가',
            915: '단위체결량',
            938: '당일매매수수료',
            939: '당일매매세금'
        },

        '잔고': {
            9201: '계좌번호',
            9001: '종목코드',
            302: '종목명',
            10: '현재가',
            930: '보유수량',
            931: '매입단가',
            932: '총매입가',
            933: '주문가능수량',
            945: '당일순매수량',
            946: '매도매수구분',
            950: '당일총매도손익',
            951: '예수금',
            27: '최우선매도호가',
            28: '최우선매수호가',
            307: '기준가',
            8019: '손익율'
        },

        '주식시간외호가': {
            21: '호가시간(HHMMSS)',
            131: '시간외매도호가총잔량',
            132: '시간외매도호가총잔량직전대비',
            135: '시간외매수호가총잔량',
            136: '시간외매수호가총잔량직전대비'
        }
    }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()
    kiwoom.test_getlist()
