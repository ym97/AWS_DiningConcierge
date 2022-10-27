"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message, intent):
    logger.debug('Here in elicitSlot {}'.format(intent_name))
    before = {
        'messages': [message],
        'sessionState':{
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit,
                'intentName': intent_name,
                'slots': slots
            },
            'intent': {
               'name': intent_name,
               'state': 'Failed',
               'confirmationState': 'None',
               'slots': slots,

              }
        }
    }
    return before


def close(session_attributes, fulfillment_state, message, slots):
    
    
    
    cuisine = slots['Cuisine']['value']['interpretedValue']
    dining_time = slots['Diningtime']['value']['interpretedValue']
    number_of_people = slots['Number_of_people']['value']['interpretedValue']
    phone = slots['Phone']['value']['interpretedValue']
    email = slots['Email']['value']['interpretedValue']
    
    info = cuisine + ',' + dining_time + ',' + number_of_people + ',' + phone + ',' + email
    logger.debug('Here in close - {}'.format(info))

    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/788578785318/DiningRequests",
        MessageBody=info
    )
    response = {
        'sessionState':{
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
            },
            'intent': {
               'name': 'DiningSuggestionsIntent',
               'state': 'Fulfilled',
               'confirmationState': 'None',
               'slots': slots
              }
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
            'type': 'Delegate',
            },
            'intent':{
                'state': 'ReadyForFulfillment',
                'name': 'DiningSuggestionsIntent',
                'slots': slots
            }

        }
        
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def inter(item):
    try:
        return item['value']['interpretedValue']
    except KeyError:
        return None
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'SSML', 'content': message_content}
    }



def validate_dining_suggestions(location, cuisine, dining_time, number_of_people, phone_number, email):
    
    if dining_time is not None:
        logger.debug('{}'.format(dining_time))
        dining_time = inter(dining_time)
        if not dining_time:
            return build_validation_result(False, 'Diningtime', 'Sorry, I didnot recognize that. We expect the time to be something like 9 pm, 11:30 am, now, etc. Please share the dinning time again!')
        if len(dining_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Diningtime', 'Sorry, I didnot recognize that. We expect the time to be something like 9 pm, 11:30 am, now, etc. Please share the dinning time again!')

        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Diningtime', 'Sorry, I didnot recognize that. We expect the time to be something like 9 pm, 11:30 am, now, etc. Please share the dinning time again!')

        if hour < 8 or hour > 23:
            # Outside of business hours
            logger.debug('restaurants not open')
            return build_validation_result(False, 'Diningtime', 'Restaurant are open from 8 am to 11 pm, please specify a time between that!')

    
    if cuisine is not None: 
        cuisine_value = inter(cuisine)
        if not cuisine_value:
             return build_validation_result(False, 'Cuisine', 'I didnot recognize that, please share the cuisine again!')
        valid_cuisines = ['italian', 'chinese', 'indian', 'american', 'mexican', 'spanish', 'greek', 'latin', 'Persian', 'korean', 'thai']
        if cuisine_value.lower() not in valid_cuisines:
            valid_cuisines = [i.title() for i in valid_cuisines]
            return build_validation_result(False,
                                            'Cuisine',
                                            'We dont have information about this cuisine, you can pick from the following: ' + (", ").join(valid_cuisines) + 
                                            ". \n Which one would like to have?" 
                                            )

        
    if number_of_people is not None:
        number = inter(number_of_people)
        if not number:
            return build_validation_result(False,
                                        'Number_of_people',
                                        'I didnt understand that, can you try telling me the number of people again?'
                                        )
        if not parse_int(number):
            return build_validation_result(False,
                                        'Number_of_people',
                                        'I didnt understand that, can you try telling me the number of people again?'
                                        )
            
    if phone_number is not None:
        phone_number = inter(phone_number)
        if not phone_number:
            return build_validation_result(False,
                                        'Phone',
                                        'This is not a valid format, we expect the phone number to be a 10 digit number. For example 1234567891, please input your phone number again!'
                                        )
        if not parse_int(phone_number):
            return build_validation_result(False,
                                        'Phone',
                                        'This is not a valid format, we expect the phone number to be a 10 digit number. For example 1234567891, please input your phone number again!'
                                        )
        if(len(phone_number)!=10):
            return build_validation_result(False,
                                        'Phone',
                                        'This is not a valid format, we expect the phone number to be a 10 digit number. For example 1234567891, please input your phone number again!'
                                        )
    if email is not None:
        email = inter(email)
        logger.debug('{}'.format(email))
        if not email:
            return build_validation_result(False,
                                        'Email',
                                        'Sorry I didnot understand that, we expect the email to be in a format like user@domain.com. Please share the email in this format!'
                                        )
        
        
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def dining_suggestions(intent_request):
    """
    Performs dialog management and fulfillment for suggesting restaurant.
    """
    intent = intent_request['interpretations'][0]['intent']
    location = get_slots(intent)["Location"]
    cuisine = get_slots(intent)["Cuisine"]
    dining_time = get_slots(intent)["Diningtime"]
    number_of_people = get_slots(intent)["Number_of_people"]
    phone_number = get_slots(intent)["Phone"]
    email = get_slots(intent)["Email"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent)

        validation_result = validate_dining_suggestions(location, cuisine, dining_time, number_of_people, phone_number, email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionState']['sessionAttributes'],
                              intent['name'],
                              slots,
                              validation_result['violatedSlot'],
                              validation_result['message'], intent_request['interpretations'][0]['intent'])

        output_session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState']['sessionAttributes'] is not None else {}

        return delegate(output_session_attributes, get_slots(intent))

    
    if source == 'FulfillmentCodeHook':
        return close(intent_request['sessionState']['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You will get dinning suggestions on your phone or email soon'}, get_slots(intent))


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    # logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['interpretations'][0]['intent']['name']
    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    
    
    
    
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    logger.debug('{}'.format(event))
    return dispatch(event)
