#This code download clips of images from planet website
#Step1:setup api_key which allows u to access to the images and have permisson to download it
#Step2:set filters, in this code there are three filters (and_filter): data filter, cloud filter and geometry filter
#Step3:set request with filters, then use request get result, which are many qualified items
#Step4:set clip information
#Step5:use result(a lot of qualified items)and clip information to download clips
from planet import api
from planet.api import filters
from datetime import datetime
import geojsonio
import json
import requests
import time
import os
from tqdm import tqdm
import zipfile# some operation are slightly different in mac os and windows
#Step1:
# client information
client = api.ClientV1(api_key="eb14409cd5544310ae7cdde4e8fe9e0f")
# Set API key (this should to be an environment variable)
api_key = 'eb14409cd5544310ae7cdde4e8fe9e0f'
PLANET_API_KEY = os.getenv('PL_API_KEY')

#Step2:
#set filters
#1:data filter (lte-> larger than or equel to)
#set start date and end date
start_date = datetime(year=2016, month=6, day=1)
end_date = datetime(year=2016, month=7, day=1)
date_filter = filters.date_range('acquired', gte=start_date, lte = end_date )

#2 cloud filter
cloud_filter = filters.range_filter('cloud_cover', lte=1.0)

#3 geometry filter
geometry_filter={
  "type": "GeometryFilter",
  "field_name": "geometry",
  "config": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          -118.13630282878874,
          34.13666853390047
        ],
        [
          -118.13481152057646,
          34.13666853390047
        ],
        [
          -118.13481152057646,
          34.13785404192857
        ],
        [
          -118.13630282878874,
          34.13785404192857
        ],
        [
          -118.13630282878874,
          34.13666853390047
        ]
      ]
    ]
  }
}

# choose and_filter (also there can be not_filter, or_filter)
and_filter = filters.and_filter(date_filter, cloud_filter,geometry_filter)


#Step3:
#set requests
#item_types = ["REOrthoTile", "PSOrthoTile"]
#item_types = ["PSOrthoTile"]
item_types = ["PSScene4Band"]##################################
req = filters.build_search_request(and_filter, item_types)

print ('====result=======')
#get results
res = client.quick_search(req)


#Step4:
# Area Of Interest (clip geometry) in GeoJSON format
aoi_json = '''{
        "type": "Polygon",
        "coordinates": [
          [
            [
              -118.13630282878874,
              34.13666853390047
            ],
            [
              -118.13481152057646,
              34.13666853390047
            ],
            [
              -118.13481152057646,
              34.13785404192857
            ],
            [
              -118.13630282878874,
              34.13785404192857
            ],
            [
              -118.13630282878874,
              34.13666853390047
            ]
          ]
        ]
      }'''




#Step5:
filepath='D:/Planet/Imagery/test125/' ############ slightly different from mac os->need solve

for item in res.items_iter(200):
    if item['_permissions']!=[]: #with permission so we will be able to download
        assets = client.get_assets(item).get()
        try:
            print '======assets======'
            print assets
            #??? if it has a location url, it can be clipped?
            #location_url = assets["analytic_sr"]['location']#################################????
            #print location_url

            # Sent Scene ID
            scene_id = item['id']
            print scene_id

            # Set Item Type
            item_type = item['properties']['item_type']#????
            print item_type

            # Set Asset Type
            asset_type = 'analytic_sr'#visual, analytic_sr ########################
            print asset_type

            # Construct clip API payload
            clip_payload = {
                'aoi': json.loads(aoi_json),
                'targets': [
                    {
                        'item_id': scene_id,
                        'item_type': item_type,
                        'asset_type': asset_type
                    }
                ]
            }

            # Request clip of scene (This will take some time to complete)
            request = requests.post('https://api.planet.com/compute/ops/clips/v1', auth=(api_key, ''),
                                    json=clip_payload)
            clip_url = request.json()['_links']['_self']

            # Poll API to monitor clip status. Once finished, download and upzip the scene
            clip_succeeded = False
            while not clip_succeeded:

                # Poll API
                check_state_request = requests.get(clip_url, auth=(api_key, ''))

                # If clipping process succeeded , we are done
                if check_state_request.json()['state'] == 'succeeded':
                    clip_download_url = check_state_request.json()['_links']['results'][0]
                    clip_succeeded = True
                    print("Clip of scene succeeded and is ready to download")

                    # Still activating. Wait 1 second and check again.
                else:
                    print("...Still waiting for clipping to complete...")
                    time.sleep(1)#########################################

            # Download clip
            response = requests.get(clip_download_url, stream=True)
            with open(filepath + scene_id + '.zip', "wb") as handle:
                for data in tqdm(response.iter_content()):
                    handle.write(data)

            # Unzip file
            ziped_item = zipfile.ZipFile(filepath + scene_id + '.zip')
            ziped_item.extractall(filepath + scene_id)

            # Delete zip file
            #because you're not closing the file before removing it. On Linux you can remove a file even if it's in use but on windows you can't so, try to close&remove instead of just removing the file
            os.remove(filepath + scene_id + '.zip')
            # print('Downloaded clips located in: /Users/renyubin/Desktop/output/')
        except:
            continue

