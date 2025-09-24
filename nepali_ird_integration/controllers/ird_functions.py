import requests
import nepali_datetime


def ir_api_post(json,bill_type):
    header = {
        "Accept": 'application/json',
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNjgzOTQ3OGNiYzkxMTY2YzcwZGUzZjU5OGU3YTMwNjI4ZWNhOGZjODVlMmYzNjBhZmQ3MzlmMTdhZWE5YWFiYWFhMjAyZjc2OTFiMTg5M2EiLCJpYXQiOjE2NTgwNjQwNzEuNjQyNzUyLCJuYmYiOjE2NTgwNjQwNzEuNjQyNzU2LCJleHAiOjE2ODk2MDAwNzEuNjM4NDg3LCJzdWIiOiIxIiwic2NvcGVzIjpbXX0.eiIDfSMWSIvdIGHP7_m6IBYRdVmnLm6ISiNbDfWy9gsfrCv3MNOGUR4FFOdfCy93_1ZnM1lcPVLEoATui03A8bIxELPekt3udbnA9-upuVA8n2y47sTtWB-TOBESbyVd4DPVxSWnEt44Tf_sWoPoIhQiwTbc0FzPvyTLB0F4PZPH9qBnbSjRnvlAabiRAhBuH7qB1lt76bqDaB9vYsLF2tV8AOQRt-AyOyJPGv8o-NKXV52KxcLAaCqInyn-WdIoaQiouRdkumrcrf-gK5HD5PXPitg-yNRDyT6ZoK6B3r9onbNtUk9WHXX_8Lu3CoLoBWq0tjxlIl5s9PJJx6FRqxpF2ZCWZEnpsZP1E--81G26KR1gvtDi-d-KuLt2ONdsSTKf0MngBN64mltg_lNPce-3MdpkP0TiXBoIB8cZ77a2Y8_kIwN-jOnfiW8i19HC6i3VKhQNYVy9Re7J0pp04C_WKJaY8oOdsyhbgaOsClsWEvihKCsBzcsVp66f4FXclNzyPTrjsFJekPkHzyE5UyTuttV7c1vswnqFbOSW3aIfTtGUGAVmnLoAqCt--BQNP9ufeoBaLmpIt8w5c7t1edbLc9fAZa6EJrcFocnKVZzR1UdACQb_xaBzYJdjbWhLeAj77qGNKgG3cxbV4feUne0czonCJe8EYOQIaPL19pE",
    }
    if bill_type=="out_invoice":
        api_url= 'https://cbapi.ird.gov.np/api/bill'
    if bill_type=="out_refund":
        api_url = 'https://cbapi.ird.gov.np/api/billreturn'
    
    response_codes={
                    200:'success',
                    104:'model invalid',
                    100:'API credentials do not match'
                    ,102:'exception while saving bill details , Please check model fields and values'
                    ,103:'Unknown exceptions, Please check API URL and model fields and values ',
                    101:'bill already exists'}

    try:
        response = requests.post(api_url, json=json, headers=header)
        response_code=response.json()
        return {'response_code':str(response_code),'message':response_codes[response_code]}
    except:
        return False
        

def date_dot_format(unformatted_date):
    a=nepali_datetime.date.from_datetime_date(unformatted_date).strftime("%Y.%m.%d")
    return a


