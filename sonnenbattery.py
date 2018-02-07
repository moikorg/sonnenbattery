import requests
import time
import argparse
from time import gmtime, strftime
import logging
from pythonjsonlogger import jsonlogger
import mysql.connector
import configparser


def configSectionMap(config, section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


def connectDB():
    config = configparser.ConfigParser()
    config.read('config.rc')

    conn = mysql.connector.connect(host=configSectionMap(config, "DB")['host'],
                                   user=configSectionMap(config, "Credentials")['username'],
                                   password=configSectionMap(config, "Credentials")['password'],
                                   db=configSectionMap(config, "DB")['db'],
                                   port=configSectionMap(config, "DB")['port'],
                                   charset = 'utf8')
    return conn





def parseTheArgs() -> object:
    parser = argparse.ArgumentParser(description='Request the Sonnen Battery API and write the data to the SQL DB')
    parser.add_argument('period', metavar='periode', type=int,
                        help='an integer for the time in seconds to wait until two API requests')
    parser.add_argument('-d', dest='verbose', action='store_true',
                        help='print debugging information')
    parser.add_argument('db', metavar='database', type=str,
                        help='the complete path/name to the DB')
    parser.add_argument('-m', dest='mock', action='store_true',
                        help='use mocked data instead requesting from the API')
    parser.add_argument('-l', help='path and filename of logfile, default=/var/log/sonnen.json',
                        default='/var/log/sonnen.json')
    parser.add_argument('-1', dest='oneshot', action='store_true',
                        help='one shot execution',)

    args = parser.parse_args()
    return args


def getSonnenData():
    try:
        r = requests.get('http://SB-41059:8080/api/v1/status')
        return r.json()
    except requests.exceptions.ConnectionError as err:
        print("Error, connection to sonnen battery could be established")
        print(err)
        return None

def str2Epoch(strDate):
    pattern = '%Y-%m-%d %H:%M:%S'
    return int(time.mktime(time.strptime(strDate, pattern)))


def main():
    args = parseTheArgs()
    period = args.period

    #    handler = logging.StreamHandler()
    handler = logging.FileHandler(args.l)

    format_str = '%(message)%(levelname)%(name)%(asctime)'
    formatter = jsonlogger.JsonFormatter(format_str)
    handler.setFormatter(formatter)
    logger = logging.getLogger('sonnenbattery')
    logger.addHandler(handler)
    logger.propagate = False

    conn = connectDB()
    c = conn.cursor()

    sqlInsert = """
        INSERT INTO sonnen_sonnenbattery
        (consumption, frequency, gridConsumption, pacTotal, production, rsoc, usoc,
        uAC, uBat, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    while True:
        if args.mock:
            sonnenData={}
            sonnenData['Consumption_W'] = 6182
            sonnenData['Fac'] = 50
            sonnenData['GridFeedIn_W'] = -780
            sonnenData['Pac_total_W'] = 2501
            sonnenData['Production_W'] = 2900
            sonnenData['RSOC'] = 5
            sonnenData['Timestamp'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            sonnenData['USOC'] = 0
            sonnenData['Uac'] = 230
            sonnenData['Ubat'] = 48
        else:
            sonnenData = getSonnenData()
            if sonnenData == None:
                if args.verbose:
                    print("Could not connect to sonnen battery. Retry in %s seconds",period)
                error_str = "Could not connect to sonnen battery. Retry in " + period + "seconds"
                logger.error(error_str)
                time.sleep(period - 0.1)
                continue

        if args.verbose:
            print(sonnenData)
        logger.info('success', extra=sonnenData)
        myrow = (
            sonnenData['Consumption_W'],
            sonnenData['Fac'],
            sonnenData['GridFeedIn_W'],
            sonnenData['Pac_total_W'],
            sonnenData['Production_W'],
            sonnenData['RSOC'],
            sonnenData['USOC'],
            sonnenData['Uac'],
            sonnenData['Ubat'],
            sonnenData['Timestamp'],
        )
        c.execute(sqlInsert, myrow)

        conn.commit()
        if args.oneshot:
            break

        time.sleep(period-0.05)

    conn.close()


# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()
