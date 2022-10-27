import json 
import boto3
import numpy as np
import requests
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError
region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service,session_token=credentials.token)

es_url = 'https://search-restaurants1-ndw3rsiqzzplkw733oib5xkc3i.us-east-1.es.amazonaws.com'
#'https://search-restaurants-tr5okwkb7z2nugjdelsfs5t4aa.us-east-1.es.amazonaws.com'
size = 3
index = 'restaurants'
                
sqs = boto3.client('sqs')
sns = boto3.client('sns')
ses = boto3.client('ses')
dynamodb = boto3.resource('dynamodb', region_name=region)
table = dynamodb.Table('yelp-restaurants')

def send_message (phone, message):
    try:
        response = sns.publish(PhoneNumber='+1'+phone, Message=message)
        message_id = response['MessageId']
        print(response)
        print("Published message to ", phone)
    except ClientError:
        print("Couldn't publish message to ", phone)
        
            
def compose_message( recommendations, cuisine, numberOfPpl, time ):
    message = 'Hello! Our suggestions for restaurants in Manhattan with ' + cuisine.capitalize() + ' cuisine for '+ str(numberOfPpl) + ' at '+ time + 'hours are\n'
    index = 1
    for rec in recommendations:
        message += str(index) + '. ' + rec['name'] + ' at ' + rec['address'] + '| '+str(rec['rating'])+' rated ( ' + str(rec['reviews']) + ' votes)\n'
        index += 1
    return message
        
def compose_mail( recommendations, cuisine, numberOfPpl, time ):
    html = '<p>Hello! Our suggestions for <b>' + cuisine.capitalize() + '</b> restaurants in Manhattan for <i>' +  str(numberOfPpl) + '</i> at <u>'+ time + ' hours</u> are</p>\n'
    index = 1
    for rec in recommendations:
        html += '<p>'+str(index) + '. ' + rec['name'] + ' at ' + rec['address'] + '| '+str(rec['rating'])+' rated ( '+str(rec['reviews'])+' votes)</p>\n'
        if len(rec['image']) :
            html += '<img src=' + rec['image'] + ' alt=' + rec['name'] +' width=\"150\" height=\"150\" >\n'
        index += 1
    return html
        
def send_mail_new( message, html, toAddress):
    send_args = {
            'Source': 'diningconciergeservices@gmail.com',
            'Destination': {'ToAddresses': [toAddress]},
            'Message': {
                'Subject': {'Data': 'Our restaurant suggestsions are here!'},
                'Body': {'Text': {'Data': message}, 'Html': {'Data': html}
                }
            }
    }
    try:
        response = ses.send_email(**send_args)
        message_id = response['MessageId']
        print("Sent mail")
    except ClientError:
        print("Couldn't send mail")
        raise
    else:
        return message_id
             
def send_mail( message, toAddress):
    components = message.split('\n')
    html = '<p>' + components[0] + '</p>\n'
    for i in range(size):
        html += '<p>' + components[i+1] + '</p>\n'

    send_args = {
            'Source': 'diningconciergeservices@gmail.com',
            'Destination': {'ToAddresses': [toAddress]},
            'Message': {
                'Subject': {'Data': 'Our restaurant suggestsions are here!'},
                'Body': {'Text': {'Data': message}, 'Html': {'Data': html}
                }
            }
    }
    try:
        response = ses.send_email(**send_args)
        message_id = response['MessageId']
        print("Sent mail")
    except ClientError:
        print("Couldn't send mail")
        raise
    else:
        return message_id
        
def processSQS():
    queues = sqs.list_queues(QueueNamePrefix='DiningRequests')
    request_queue_url = queues['QueueUrls'][0]
    #print(request_queue_url)

    while True:
        response = sqs.receive_message(
            QueueUrl=request_queue_url,
            AttributeNames=[
                'All'
            ],
            MaxNumberOfMessages=10,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=30,
            WaitTimeSeconds=0
        )
        print(response)
        if 'Messages' in response:
            print("Have response")
            for message in response['Messages']:
                parts = str(message['Body']).split(',')
                #print(parts)
                cuisine, time, numberOfPpl, phone, email = parts
                
                #Temp check
                #email = 'manisha.yara@gmail.com'
                #cuisine, time, numberOfPpl, phone, email = ['indian', '8:00', '2', '6093562154', 'manisha.yara@gmail.com']
                search_url = es_url + '/' + index + '/_search'
                query = {
                    "size": size,
                    "query": {
                        "match": {
                                "Cuisine" : cuisine
                        }
                    }
                }
                headers = { "Content-Type": "application/json" }
                
                es_response_ = requests.get(search_url, auth=awsauth, headers=headers, data=json.dumps(query))
                #print(es_response_)
                #print(es_response_.text)
                
                es_response = json.loads(es_response_.text).get("hits").get("hits")
                #print(es_response)
                
                #We have es_responses of size=size
                #Fetch the restaurantIDs and query the dynamo DB for the additional details.
                recommendations = []
                for res in es_response:
                    restaurantID = res['_source']['RestaurantID']
                    #dynamoRes = table.query(KeyConditionExpression=Key('insertedAtTimestamp').eq(restaurantID))
                    dynamoRes = table.get_item(Key={'insertedAtTimestamp': restaurantID})
                    #print(dynamoRes)
                    restaurantName = dynamoRes['Item']['name']
                    restaurantAddress = " ".join(dynamoRes['Item']['address'])
                    restaurantReviews = dynamoRes['Item']['review_count']
                    restaurantRating = dynamoRes['Item']['rating']
                    restaurantPic = ""
                    if 'image_url' in dynamoRes['Item']:
                        restaurantPic = dynamoRes['Item']['image_url']
                    recommendations.append({'name': restaurantName, 'address': restaurantAddress, 'reviews': restaurantReviews, 'rating': restaurantRating, 'image': restaurantPic})
                
                #Sort recommendatiosn by rating
                recommendations=sorted( recommendations, key=lambda x: x['rating'], reverse=True)
                #We are done processing this request. So we delete from sqs
                sqs.delete_message(QueueUrl=request_queue_url, ReceiptHandle=message['ReceiptHandle'])
                message = compose_message(recommendations, cuisine, numberOfPpl, time)
                #print(message)
                #We are not sending SMS now. We will be usign mail.
                #send_message(phone, message)
                
                
                #temp
                #sqs.delete_message(QueueUrl=request_queue_url, ReceiptHandle=message['ReceiptHandle'])
                #message = 'Hello! Our suggestions for restaurants in Manhattan with indian cuisine, for 4 at 8:00 are\n'+'1. Indian Curry Heights at 125 Ralph Ave Brooklyn, NY 11221\n'+'2. VeganHood at 2100 Frederick Douglass Blvd New York, NY 10026\n'+'3. Tandoori Place at 2146 Starling Ave Bronx, NY 10462\n'
                
                #send_mail(message, email)
                #Using new formatted mail service/
                html = compose_mail(recommendations, cuisine, numberOfPpl, time)
                send_mail_new(message, html, email)
                
                #temp
                #break
        else:
            print('No new requests to handle now!')
            break

       
def tester():
    cuisine, time, numberOfPpl, phone, email =  ['Thai', '8:00', '2', '6093562154', 'manisha.yara@gmail.com']
    search_url = es_url + '/' + index + '/_search'
    query = {
        "size": size,
        "query": {
            "match": {
                    "Cuisine" : cuisine
            }
        }
    }
    headers = { "Content-Type": "application/json" }
    es_response_ = requests.get(search_url, auth=awsauth, headers=headers, data=json.dumps(query))
    print(es_response_)
    print(es_response_.text)
    
    es_response = json.loads(es_response_.text).get("hits").get("hits")
    recommendations = []
    for res in es_response:
        restaurantID = res['_source']['RestaurantID']
        dynamoRes = table.get_item(Key={'insertedAtTimestamp': restaurantID})
        print(dynamoRes)
        restaurantName = dynamoRes['Item']['name']
        restaurantAddress = " ".join(dynamoRes['Item']['address'])
        restaurantReviews = dynamoRes['Item']['review_count']
        restaurantRating = dynamoRes['Item']['rating']
        restaurantPic = ""
        if 'image_url' in dynamoRes['Item']:
            restaurantPic = dynamoRes['Item']['image_url']
        recommendations.append({'name': restaurantName, 'address': restaurantAddress, 'reviews': restaurantReviews, 'rating': restaurantRating, 'image': restaurantPic})
    #Sort recommendatiosn by rating
    recommendations=sorted( recommendations, key=lambda x: x['rating'], reverse=True)
    message = compose_message(recommendations, cuisine, numberOfPpl, time)
    html = compose_mail(recommendations, cuisine, numberOfPpl, time)
    print(message)
    #send_mail(message, email)
    send_mail_new(message, html, email)

def lambda_handler(event, context):
    # TODO implement
    processSQS()
    #tester()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
