import json
data = []
with open('/Users/manishayara/Documents/Fall 2022/CCBD/HW1_DiningConcierge/yelp-restaurants-dynamodb.json') as f:
    for line in f:
        data.append(json.loads(line))

updated_dict = []
for dat in data:
    entry = {}
    #print(list(dat["Item"]["insertedAtTimestamp"].values())[0])
    entry["RestaurantID"] = list(dat["Item"]["insertedAtTimestamp"].values())[0]
    entry["Cuisine"] = list(dat["Item"]["cuisine"].values())[0]
    updated_dict.append(entry)

index_dict = {"index": {"_index": "restaurants", "_type": "_doc", "_id": ""}}
count = 1
with open('/Users/manishayara/Documents/Fall 2022/CCBD/HW1_DiningConcierge/open_search/restaurants-es1.json', 'a') as outfile:
    for hostDict in updated_dict:
        index_dict["index"]["_id"] = str(count)#hostDict['RestaurantID']
        json.dump(index_dict, outfile)
        outfile.write('\n')
        json.dump(hostDict, outfile)
        outfile.write('\n')
        count = count +1