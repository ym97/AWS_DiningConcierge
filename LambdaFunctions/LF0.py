import boto3
import random
# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')
def lambda_handler(event, context):
    msg_from_user = event['messages'][0]['unstructured']['text']
    sessionId = event['messages'][1]['unstructured']['text']
    
    disallowed_character = " ()-"
    # sessionId = "Tue Oct 11 2022 18:47:03 GMT-0400 (Eastern Daylight Time)"
    for character in disallowed_character:
            sessionId = sessionId.replace(character,"")
    sessionId.replace("(", "")
    sessionId.replace(")", "")
    
    
    
    print(sessionId)
    print(event)
    print(context)
    print(f"Message from frontend: {msg_from_user}")
    
    
    # Initiate conversation with Lex
    response = client.recognize_text(
            botId='IE6NFZRZRR', # MODIFY HERE
            botAliasId='OUEVWX7BS4', # MODIFY HERE
            localeId='en_US',
            sessionId=sessionId,
            text=msg_from_user)
    
    msg_from_lex = response.get('messages', [])
    if msg_from_lex:
        
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        msg_lex = ""
        print(msg_from_lex)
        for i in range(len(msg_from_lex)):
            msg_lex = msg_lex + " " + msg_from_lex[i]['content']
        print(response)
        resp = {
            'statusCode': 200,
            'messages': [
                          {
                            'type': 'unstructured',
                            'unstructured': {
                              'text': msg_lex,
                            }
                          }
                        ]
          
        }

        return resp