import requests

def getSonnenData():
    r = requests.get('http://SB-41059:8080/api/v1/status')
    return r.json()

def main():
    sonnenData = getSonnenData()
    print(sonnenData)

# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    main()