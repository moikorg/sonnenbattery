import requests
import time
import argparse
from time import gmtime, strftime
import configparser
import paho.mqtt.client as mqtt
import schedule
import sys
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS



# configuration file reading and setting the variables
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


# connection to the MariaDB and write the data
def connectDB_andWrite(configfile, sonnenData):
    import mysql.connector
    
    config = configparser.ConfigParser()
    config.read(configfile)

    conn = mysql.connector.connect(host=configSectionMap(config, "DB")['host'],
                                   user=configSectionMap(config, "Credentials")['username'],
                                   password=configSectionMap(config, "Credentials")['password'],
                                   db=configSectionMap(config, "DB")['db'],
                                   port=configSectionMap(config, "DB")['port'],)
#                                   charset = 'utf8mb4',
#                                   collation = 'utf8mb3_general_ci')

    c = conn.cursor()
    SQL_INSERT = """
        INSERT INTO sonnenbattery
        (consumption, gridConsumption, pacTotal, production, rsoc, usoc,
        uAC, uBat, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    try:
        myrows = (
            sonnenData['Consumption_W'],
            sonnenData['GridFeedIn_W'],
            sonnenData['Pac_total_W'],
            sonnenData['Production_W'],
            sonnenData['RSOC'],
            sonnenData['USOC'],
            sonnenData['Uac'],
            sonnenData['Ubat'],
            sonnenData['Timestamp'],
        )
    except KeyError:
        print("some keys are missing, rollingback")
        #conn.rollback()
    else:
        if sonnenData['Consumption_W'] > 0:
            diff = abs(sonnenData['Production_W']+sonnenData['Pac_total_W']-
                    sonnenData['Consumption_W']-sonnenData['GridFeedIn_W'])
            if diff > 20:
                print("error in read out, diff greater than 20. Diff was: " + str(diff))
            else:
                try:
                    c.execute(SQL_INSERT, myrows)
                except mysql.connector.errors.DatabaseError:
                    print("connection to DB did not work")
                else:
                    conn.commit()
                conn.close()



# parsing the input arguments
def parseTheArgs() -> object:
    parser = argparse.ArgumentParser(description='Request the Sonnen Battery API and write the data to the SQL DB')
    parser.add_argument('-v', dest='verbose', action='store_true',
        help='print debugging information')
    parser.add_argument('-m', dest='mock', action='store_true',
        help='use mocked data instead requesting from the API')
    parser.add_argument('-f', help='path and filename of the config file, default is ./config.rc',
        default='./config.rc')
    parser.add_argument('-d', help='write the data also to MariaDB/MySQL DB', action='store_true', dest='db_write')

    args = parser.parse_args()
    return args


# function that requests the Sonnenbatterie API 
def getSonnenData(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    try:
        r = requests.get(configSectionMap(config, "Sonnen")['url'], timeout=1.0)
        return r.json()
    except requests.exceptions.ConnectionError as err:
        print("Error, connection to sonnen battery could be established")
        print(err)
        return None
    except requests.exceptions.Timeout as err:
        print("Request to battery timed out")
        print(err)
    except KeyError:
        print('You must provide the URL of your sonnen battery in the config file')
        return None
    except requests.exceptions.RequestsJSONDecodeError:
        print("Returned value can't be interpreted as json")
        return None

def str2Epoch(strDate):
    pattern = '%Y-%m-%d %H:%M:%S'
    return int(time.mktime(time.strptime(strDate, pattern)))

def on_connect(client, userdata, flags, rc):
    if rc==0:
        print("connected OK Returned code=",rc)
    else:
        print("Bad connection Returned code=",rc)


def job(args):

    try:
        mqttClient = connectMQTT(args)
    except IOError:
        print("Problem with the MQTT connection, trying in the next iteration")
        return
    if args.mock:
        sonnenData={}
        sonnenData['Consumption_W'] = 6182
        sonnenData['GridFeedIn_W'] = -780
        sonnenData['Pac_total_W'] = 2501
        sonnenData['Production_W'] = 2900
        sonnenData['RSOC'] = 5
        sonnenData['Timestamp'] = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        sonnenData['USOC'] = 0
        sonnenData['Uac'] = 230
        sonnenData['Ubat'] = 48
    else:
        sonnenData = getSonnenData(args.f)
        if sonnenData == None:
            error_str = f"Could not connect to sonnen battery. Retry later"
            print(error_str)
            return
        if args.db_write:
            conn = connectDB_andWrite(args.f, sonnenData)

        try:
            if args.verbose:
                output_str = "{\"time\":\""+sonnenData['Timestamp']+"\","+\
                        "\"consumption\":"+str(sonnenData['Consumption_W'])+","+\
                        "\"gridfeedin\":"+str(sonnenData['GridFeedIn_W'])+","+ \
                        "\"pactotal\":" + str(sonnenData['Pac_total_W'])+"," + \
                        "\"production\":" + str(sonnenData['Production_W'])+"," + \
                        "\"rsoc\":" + str(sonnenData['RSOC'])+"," + \
                        "\"usoc\":" + str(sonnenData['USOC'])+"," + \
                        "\"ubat\":" + str(sonnenData['Ubat'])+"}"
                print(output_str)
            mqtt_json = "{\"ts\":\"" + sonnenData['Timestamp'] + "\"," + \
                            "\"cons\":" + str(sonnenData['Consumption_W']) + "," + \
                            "\"gridFIn\":" + str(sonnenData['GridFeedIn_W']) + "," + \
                            "\"pactot\":" + str(sonnenData['Pac_total_W']) + "," + \
                            "\"prod\":" + str(sonnenData['Production_W']) + "," + \
                            "\"usoc\":" + str(sonnenData['USOC']) + "}"
        except KeyError as err:
            print("KeyError occurred: %s" % err)

    if sonnenData['Consumption_W'] > 0:
        diff = abs(sonnenData['Production_W']+sonnenData['Pac_total_W']-
                sonnenData['Consumption_W']-sonnenData['GridFeedIn_W'])
        if diff > 40:
            print("error in read out, diff greater than 40. Diff was: " + str(diff))
        else:
            mqttClient.publish("sensor/pv/1", mqtt_json)  # publish
    else:
        print("got a 0 consumption, ignore this data set")
    
    mqttClient.disconnect()
    write2InfluxDB(sonnenData, args.f)


def write2InfluxDB(data, configfile):

    config = configparser.ConfigParser()
    config.read(configfile)

    bucket = configSectionMap(config, "InfluxDB")['bucket']

    with InfluxDBClient(url=configSectionMap(config, "InfluxDB")['url'], token=configSectionMap(config, "InfluxDB")['token'],
            org=configSectionMap(config, "InfluxDB")['org']) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        ts = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        p = Point(configSectionMap(config, "InfluxDB")['measurement'])\
            .tag("location", "Marly")\
            .time(ts)\
            .field("consumption", data['Consumption_W'])\
            .field("gridfeedin", data['GridFeedIn_W'])\
            .field("pactotal", data['Pac_total_W'])\
            .field("production", data['Production_W'])\
            .field("rsoc", data['RSOC'])\
            .field("usoc", data['USOC'])\
            .field("ubat", data['Ubat'])
        write_api.write(bucket=configSectionMap(config, "InfluxDB")['bucket'], org=configSectionMap(config, "InfluxDB")['org'], record=p)



def main():
    args = parseTheArgs()
    config = configparser.ConfigParser()
    config.read(args.f)

    try:
        periodicity = int(configSectionMap(config, "Sonnen")['periodicity'])
    except:
        sys.exit("Periodicity value must be int")

    schedule.every(periodicity).seconds.do(job, args=args)
    while True:
        schedule.run_pending()
        time.sleep(1)


def on_disconnect(client, userdata, rc):
#    print("disconnecting reason  " + str(rc))
    pass


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
   #client.subscribe("$SYS/#")


def on_publish(client, userdata, result):
#    print("Data published")
    pass


def connectMQTT(args):
    config = configparser.ConfigParser()
    config.read(args.f)
    broker = configSectionMap(config, "MQTT")['host']

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.username_pw_set(username=configSectionMap(config, "MQTT")['username'],
                           password= configSectionMap(config, "MQTT")['password'])

    try:
        client.connect(broker, 1883, 60)
    except:
        print("ERROR: Can not connect to MQTT broker")
        raise IOError

    #print("ready for publishing")
    return client

# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()
