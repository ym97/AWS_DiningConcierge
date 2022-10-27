# CODE TAKEN FROM
# https://rspiro9.github.io/nyc_restaurant_yelp_and_inspection_analysis
import json

import requests
import pandas as pd

# Define function to gather keys:
def get_keys(path):
    with open(path) as f:
        return json.load(f)
				
# Pull in keys and specifically draw out the api key. I have removed the specific path to the keys 
# for security purposes:
api_key = 'B0b_arYCsu148wsXpuQayibp3KmqKpb1oC0ZKk1xJSUKARt93KEPVIvPTf-ADQphJjonlxnn9XnypMuatmejbneURwgMbd3Q7Kw_bXlMqY16Y35hwNjTE8RmXMo0Y3Yx'

# URL to pull data from:
url = 'https://api.yelp.com/v3/businesses/search'

# Identify headers:
headers = {'Authorization': 'Bearer {}'.format(api_key)}



 # List of Manhattan neighborhoods:
neighborhoods = ['Midtown West', 'Greenwich Village', 'East Harlem', 'Upper East Side', 'Midtown East',
                 'Gramercy', 'Little Italy', 'Chinatown', 'SoHo', 'Harlem',
                 'Upper West Side', 'Tribeca', 'Garment District', 'Stuyvesant Town', 'Financial District',
                 'Chelsea', 'Morningside Heights', 'Times Square', 'Murray Hill', 'East Village',
                 'Lower East Side', 'Hell\s Kitchen', 'Central Park']
#neighborhoods = ['Morningside Heights']

# Create temporary dataframe to hold data:
nyc = [[] for i in range(len(neighborhoods))] 


mainlimit = 20
search_limit = 50

# Function to draw in data for each neighborhood:
for x in range(len(neighborhoods)):
    print('---------------------------------------------')
    print('Gathering Data for {}'.format(neighborhoods[x]))
    print('---------------------------------------------')


    for y in range(mainlimit):
        location = neighborhoods[x]+', Manhattan, NY'
        term = "Restaurants"        
        offset = search_limit * y
        categories = "(restaurants, All)"
        sort_by = 'distance'

        url_params = {
                        'location': location.replace(' ', '+'),
                        'term' : term,
                        'limit': search_limit,
                        'offset': offset,
                        #'categories': categories,
                        #'sorty_by': sort_by
                    }
        
        response = requests.get(url, headers=headers, params=url_params)
        print('***** {} Restaurants #{} - #{} ....{}'.format(neighborhoods[x], 
                                                             offset+1, offset+search_limit,
                                                             response))
        nyc[x].append(response)

print(response)
print(type(response.text))
print(response.json().keys())
print(response.text[:mainlimit*search_limit])


## Check for any empty business lists:

# for x in range(len(neighborhoods)):
#     for y in range(mainlimit):
#         num = len(nyc[x][y].json()['businesses'])
#         if num != search_limit:
#             print(neighborhoods[x], y, num)

## Save the compiled data into dataframe and remove any empty data:
df = pd.DataFrame()
for x in range(len(neighborhoods)):
    for y in range(mainlimit):
        try:
            df_temp = pd.DataFrame.from_dict(nyc[x][y].json()['businesses'])
            df_temp.loc[:,'neighborhood'] = neighborhoods[x]
            df = df.append(df_temp)
        except:
            print('Not there for '+str(y)+' in '+neighborhoods[x])

file_name = 'my2727_yelp.csv'
df.to_csv(file_name, encoding='utf-8', index=False)
