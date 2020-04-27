import logging
import pymysql
import json
from json import dumps
from datetime import datetime
import os
import sys
from decimal import Decimal
import boto3

ssm = boto3.client('ssm')
rdshost_parameter = ssm.get_parameter(Name=os.environ['rdshostparam'])
database_parameter = ssm.get_parameter(Name=os.environ['dbparam'])
dbusername_parameter = ssm.get_parameter(Name=os.environ['dbusernameparam'],WithDecryption=True)
dbpassword_parameter = ssm.get_parameter(Name=os.environ['dbpasswordparam'],WithDecryption=True)

database = database_parameter['Parameter']['Value']
rdshost = rdshost_parameter['Parameter']['Value']
username = dbusername_parameter['Parameter']['Value']
password = dbpassword_parameter['Parameter']['Value']
results = []
results_list = []


class AuroraProvider:
    def __init__(self):

    
        try:
            self.conn = pymysql.connect(rdshost, user=username, passwd=password, db=database, connect_timeout=5)
        except:
            print("ERROR: Unexpected error: Could not connect to MySql instance.")
            sys.exit()

        print("SUCCESS: Connection to RDS mysql instance succeeded")
        
    def response(self, data):
            return{
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                
                'body': json.dumps(data),
                'isBase64Encoded': 'false'
            }
            
    def NonCriticalErrors(self, event):
        deviceid = event['pathParameters']['id']
        ErrorLog_list=[]
        ErrorLog_list.clear()
        length = []
        if event['queryStringParameters']['limit'] == '0':
            length = 0
            print(length)
        else:
            length = int(event['queryStringParameters']['limit']) + 1
            print(length)
        with self.conn.cursor() as cur:
            if event['queryStringParameters']['days'] != "all":
                #print("""SELECT device_id,code,TimeStamp,description,level,report_time FROM omnipump.pump_error_log where device_id = '%s' and timestamp > now() - INTERVAL %s Day and level in('med','minor','info') order by TimeStamp desc,report_time desc limit %s,50""" %(event['pathParameters']['id'],event['queryStringParameters']['days'],length))
                #cur.execute("""SELECT device_id,code,TimeStamp,description,level,report_time FROM omnipump.pump_error_log where device_id = '%s' and timestamp > now() - INTERVAL %s Day and level in('med','minor','info') order by TimeStamp desc,report_time desc limit %s,50""" %(event['pathParameters']['id'],event['queryStringParameters']['days'],length))
                cur.execute("""Select DateTime from Devices where device_id = '%s' """ %(deviceid))
                deviceresult = cur.fetchone()
                date = deviceresult[0].strftime('%Y-%m-%d')
                
                cur.execute("""SELECT E.* FROM omnipump.pump_error_log E JOIN(
                SELECT MIN(timestamp) AS timestamp,D.side,D.data_source,D.level,D.description,D.code,D.report_time,D.device_id FROM omnipump.pump_error_log D  LEFT  JOIN
                (SELECT A.side,A.data_source,A.level,A.description,A.code,A.report_time,A.device_id FROM omnipump.pump_error_log A JOIN
                (SELECT MIN(timestamp) AS timestamp,device_id, side,  data_source, code, level, description,report_time FROM omnipump.pump_error_log where device_id= '%s'
                and TimeStamp < '%s' group by device_id, side,  data_source, code, level, description,   report_time) B
                ON A.timestamp=B.timestamp AND A.device_id= '%s' and A.level not in ('major','supermajor')
                AND A.description=B.description AND A.side=B.side AND A.data_source=B.data_source AND A.code=B.code AND A.level=B.level AND
                A.timestamp=B.timestamp AND A.report_time=B.report_time ) C
                ON  D.side=C.side AND D.data_source=C.data_source
                AND D.level=C.level AND D.description=C.description AND D.code=C.code AND D.report_time=C.report_time
                AND D.device_id=C.device_id WHERE D.device_id= '%s' AND D.level not in ('major','supermajor') and D.timestamp >= '%s' AND C.side IS  NULL
                group by D.side,D.data_source,D.level,D.description,D.code,D.report_time,D.device_id HAVING MIN(timestamp)  between DATE_ADD(now(), INTERVAL -%s DAY) and now() ) F
                ON E.side=F.side AND E.data_source=F.data_source
                AND E.level=F.level AND E.description=F.description AND E.code=F.code AND E.report_time=F.report_time
                AND E.device_id=F.device_id AND E.timestamp=F.timestamp order by TimeStamp desc,report_time desc limit %s,50""" %(deviceid,date,deviceid,deviceid,date,event['queryStringParameters']['days'],length))
                results = cur.fetchall()
            else:
                cur.execute("""SELECT E.* FROM omnipump.pump_error_log E JOIN(
                SELECT MIN(timestamp) AS timestamp,D.side,D.data_source,D.level,D.description,D.code,D.report_time,D.device_id FROM omnipump.pump_error_log D  LEFT  JOIN
                (SELECT A.side,A.data_source,A.level,A.description,A.code,A.report_time,A.device_id FROM omnipump.pump_error_log A JOIN
                (SELECT MIN(timestamp) AS timestamp,device_id, side,  data_source, code, level, description,report_time FROM omnipump.pump_error_log where device_id= '%s'
                and TimeStamp < '2020-04-05' group by device_id, side,  data_source, code, level, description,   report_time) B
                ON A.timestamp=B.timestamp AND A.device_id= '%s' and A.level not in ('major','supermajor')
                AND A.description=B.description AND A.side=B.side AND A.data_source=B.data_source AND A.code=B.code AND A.level=B.level AND
                A.timestamp=B.timestamp AND A.report_time=B.report_time ) C
                ON  D.side=C.side AND D.data_source=C.data_source
                AND D.level=C.level AND D.description=C.description AND D.code=C.code AND D.report_time=C.report_time
                AND D.device_id=C.device_id WHERE D.device_id= '%s' AND D.level not in ('major','supermajor') and D.timestamp >= "2020-04-05" AND C.side IS  NULL
                group by D.side,D.data_source,D.level,D.description,D.code,D.report_time,D.device_id  F
                ON E.side=F.side AND E.data_source=F.data_source
                AND E.level=F.level AND E.description=F.description AND E.code=F.code AND E.report_time=F.report_time
                AND E.device_id=F.device_id AND E.timestamp=F.timestamp order by TimeStamp desc,report_time desc limit %s,50""" %(deviceid,deviceid,deviceid,length))
                results = cur.fetchall()
            for row in results:
                cur.execute(""" select pump_type from Pump_Version where device_id = '%s' """ %(deviceid))
                pump = cur.fetchone()
                if pump != None:
                    pumptype = pump[0].strip("\r\n")
                else:
                    pumptype = ''
                resultsarray= {'device_id':row[1],'code':row[5],'TimeStamp':str(row[9]),'description':row[7],'level':row[6],'report_time':str(row[10]),'pump_type':pumptype}
                ErrorLog_list.append(resultsarray)
                #print(devices_list)
        return ErrorLog_list

    
def lambda_handler(event, context):
    print(event)
    data_list=[]
    repo = AuroraProvider()
    res_Non_Critical_ErrorLogs = repo.NonCriticalErrors(event)
    data={"Non_Critical_ErrorLogs":res_Non_Critical_ErrorLogs}
    print(data)
    res = repo.response(data)
    return (res)    
    conn.close
    

   
   
   
    
    