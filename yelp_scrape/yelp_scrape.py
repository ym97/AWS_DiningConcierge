import boto3
import datetime
import json
import requests
from decimal import *
from time import sleep
from urllib.parse import urljoin

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('yelp-restaurants')

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
TOKEN_PATH = '/oauth2/token'
GRANT_TYPE = 'client_credentials'

# Defaults for our simple example.
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'Manhattan'
restaurants = {}


def search(cuisine, offset):
    url_params = {
        'location': DEFAULT_LOCATION,
        'offset': offset,
        'limit': 50,
        'term': cuisine + " restaurants",
        'sort_by': 'rating'
    }
    return request(API_HOST, SEARCH_PATH, url_params=url_params)


def request(host, path, url_params=None):
    url_params = url_params or {}
    url = urljoin(host, path)
    headers = {
        'Authorization': 'Bearer B0b_arYCsu148wsXpuQayibp3KmqKpb1oC0ZKk1xJSUKARt93KEPVIvPTf-ADQphJjonlxnn9XnypMuatmejbneURwgMbd3Q7Kw_bXlMqY16Y35hwNjTE8RmXMo0Y3Yx',
    }

    response = requests.get(url, headers=headers, params=url_params)
    rjson = response.json()
    return rjson


def addItems(data, cuisine):
    global restaurants
    with table.batch_writer() as batch:
        for details in data:
            try:
                if details["alias"] in restaurants:
                    continue;
                details["rating"] = Decimal(str(details["rating"]))
                restaurants[details["alias"]] = 0
                details['cuisine'] = cuisine
                details['insertedAtTimestamp'] = str(datetime.datetime.now())
                details["coordinates"]["latitude"] = Decimal(str(details["coordinates"]["latitude"]))
                details["coordinates"]["longitude"] = Decimal(str(details["coordinates"]["longitude"]))
                details['address'] = details['location']['display_address']
                details.pop("distance", None)
                details.pop("location", None)
                details.pop("transactions", None)
                details.pop("display_phone", None)
                details.pop("categories", None)
                if details["phone"] == "":
                    details.pop("phone", None)
                if details["image_url"] == "":
                    details.pop("image_url", None)

                #print(details)
                batch.put_item(Item=details)
                #print("inserted to db")
                sleep(0.001)
            except Exception as e:
                print(e)
                print(details)

def scrapeYelp():
    cuisines = ['italian', 'chinese', 'indian', 'american', 'mexican', 'spanish', 'greek', 'latin', 'Persian', 'korean', 'thai']
    for cuisine in cuisines:
        print(cuisine + '::START')
        offset = 0
        while offset < 1000:
            js = search(cuisine, offset)
            addItems(js["businesses"], cuisine)
            offset += 50
        print(cuisine + '::END')


def lambda_handler(event, context):
    scrapeYelp()