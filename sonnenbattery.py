import requests
import sqlite3
import time
import argparse
from time import gmtime, strftime
import syslog

def parseTheArgs():
    parser = argparse.ArgumentParser(description='Request the Sonnen Battery API and write the data to the SQL DB')
    parser.add_argument('period', metavar='periode', type=int,
                        help='an integer for the time in seconds to wait until two API requests')
    parser.add_argument('-d', dest='verbose', action='store_true',
                        help='print debugging information')
    parser.add_argument('db', metavar='database', type=str,
                        help='the complete path/name to the DB')
    parser.add_argument('-m', dest='mock', action='store_true',
                        help='use mocked data instead requesting from the API')

    args = parser.parse_args()
    return args


def getSonnenData():
    try:
        r = requests.get('http://SB-41059:8080/api/v1/status')
        return r.json()
    except requests.exceptions.ConnectionError as err:
        print ("Error, connection to sonnen battery could be established")
        print (err)
        return None

def str2Epoch(strDate):
    pattern = '%Y-%m-%d %H:%M:%S'
    return int(time.mktime(time.strptime(strDate, pattern)))

def main():
    args = parseTheArgs()
    period = args.period

#    syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)

    conn = sqlite3.connect(args.db)
#    conn = sqlite3.connect('/home/mike/git/sonnenbattery/sonnen.sql')
    c = conn.cursor()

    sqlInsert = """
        INSERT INTO sonnen_sonnenbattery
        (consumption, frequency, gridConsumption, isSystemInstalled, pacTotal, production, rsoc, timestamp, usoc,
        uAC, uBat)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    while True:
        if args.mock == True:
            sonnenData={}
            sonnenData['Consumption_W']=1234
            sonnenData['Fac']=50
            sonnenData['GridFeedIn_W']=500
            sonnenData['IsSystemInstalled']=1
            sonnenData['Pac_total_W']=0
            sonnenData['Production_W']=500
            sonnenData['RSOC']=5
            sonnenData['Timestamp']=strftime("%Y-%m-%d %H:%M:%S", gmtime())
            sonnenData['USOC']=0
            sonnenData['Uac']=230
            sonnenData['Ubat']=48
        else:
            sonnenData = getSonnenData()
            if sonnenData == None:
                if args.verbose == True:
                    print("Could not connect to sonnen battery. Retry in %s seconds",period)
                time.sleep(period - 0.1)
                continue

        if args.verbose == True:
            print(sonnenData)
        syslog.syslog(syslog.LOG_ERR | syslog.LOG_USER, str(sonnenData))
        ts = str2Epoch(sonnenData['Timestamp'])
        myrow = (
            sonnenData['Consumption_W'],
            sonnenData['Fac'],
            -sonnenData['GridFeedIn_W'],
            sonnenData['IsSystemInstalled'],
            -sonnenData['Pac_total_W'],
            sonnenData['Production_W'],
            sonnenData['RSOC'],
            sonnenData['Timestamp'],
#            ts,
            sonnenData['USOC'],
            sonnenData['Uac'],
            sonnenData['Ubat']
        )
        c.execute(sqlInsert, myrow)

        conn.commit()
        time.sleep(period-0.05)

    conn.close()

# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()
