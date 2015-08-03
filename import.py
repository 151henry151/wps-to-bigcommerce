#!/usr/bin/python

import requests, json, sys
import getpass
from pprint import pprint
#import urllib3.contrib.pyopenssl
#urllib3.contrib.pyopenssl.inject_into_urllib3()


wps_dealer_id = raw_input('WPS Dealer ID:')
wps_password = getpass.getpass('WPS password:')

# WPS credentials and path
WPS_URL = 'http://api.wpswebservices.com'
DEALER_ID = wps_dealer_id
PASSWORD = wps_password
DEBUG = True
 
# BigCommerce credentials and URLs
BIG_USER = 'henry'
BIG_KEY = '6eb1f953e03fcd0f3cb90d2719c77163a8516432'
BIG_API = 'https://store-gya4ih.mybigcommerce.com/api/v2/'
BIG_HEADERS = {'Content-Type': 'application/json'}
BIG_STORE_URL = BIG_API + '%s'
BIG_STORE_PRODUCT_URL = BIG_API + 'products.json'
IMAGE_LOCATION = 'http://www.wpsstatic.com/WPSIMAGES/'
BRAND_IMAGE = 'http://162.243.58.11/comingsoon.jpg'
 
# Script stuff
OVERWRITE = True

# Dictionary for converting WPS properties to BigCommerce properties
conversion_dict = {
    'description': 'name',
    'list_pric': 'price',
    'estimated_weight': 'weight',
    #'producttype': 'categories',
    'image': 'mainimg',
    'catalog_description': 'description',
    'id': 'sku',
    'brand_id': 'brand_id'
}
 
brand_dictionary = {}
 
# Used when testing script
CATNAME = 'testcat'
CATID = '504'
 
def get_category_id(name):
    get_request = requests.get(BIG_API + 'categories.json', params={'name':name}, headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
    try:
        cat_list = get_request.json()
        if cat_list:
            return cat_list[0]['id']
        else:
            return None
    except:
        return None
 
def create_category(name):
    rp = requests.post(BIG_API + 'categories.json',
                      data=json.dumps({'name':name}), headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
    if rp.status_code == 201:
        return rp.json()['id']
    else:
        return get_category_id(name)
 
def get_part_info(pn):
    # Create the url
    part_url = WPS_URL + '/item/%s' % pn

    # Send request
    part_response = requests.get(part_url, auth=(DEALER_ID, PASSWORD))
    
    # Convert JSON response and return part info
    try:
        response =  part_response.json()
        if DEBUG:
            print "[DEBUG] Response of request %s" % part_url
            print "[DEBUG]", response
        return response
    
    # If malformed response or error, return None
    except:
        if DEBUG:
            print "[DEBUG] [ERROR] Error on %s" % part_response.url
            print "[DEBUG] [ERROR]", part_response.text
        return None
 
def add_image(image_name, product_id):
    image_data = {'image_file': IMAGE_LOCATION + '%s' % (image_name,)}
    image_info = requests.post(BIG_API + 'products/%s/images.json' % (product_id,),
                               data=json.dumps(image_data), headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
 
def create_brand(brand_name):
    if brand_name in brand_dictionary.keys():
        return brand_dictionary[brand_name]
    brand_data = {'name': brand_name, 'image_file': BRAND_IMAGE}
    rp = requests.post(BIG_API + 'brands.json', data=json.dumps(brand_data), headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
    if rp.status_code == 201:
        print '[LOG] Created brand %s' % (brand_name,)
        b_id =  rp.json()['id']
        brand_dictionary[brand_name] = b_id
        return b_id
    else:
        return get_brand_id(brand_name)
 
def get_brand_id(name):
    get_request = requests.get(BIG_API + 'brands.json', params={'name':name}, headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
    try:
        brand_list = get_request.json()
        if brand_list:
            b_id = brand_list[0]['id']
            brand_dictionary[name] = b_id
            return b_id
        else:
            return None
    except:
        return None

def wps_item_to_bc(wps_item):
    # Swap out compatible keys and remove incompatible keys
    bc_item = {}
    print "[LOG] Converting item: %s" % (wps_item['description'],)
    for k in wps_item.keys():
        if k in conversion_dict.keys() and k != conversion_dict[k]:
            bc_item[conversion_dict[k]] = wps_item[k]
    
    # Add some product properties
    bc_item['availability'] = 'available'
    bc_item['is_visible'] = True
    bc_item['type'] = 'physical'
    bc_item['categories'] = [CATID,]
    
    # If weight is None , set it to 0
    if not bc_item['weight']:
        bc_item['weight'] = 0
    
    if DEBUG:
        print "[DEBUG] Part data: ",
        pprint(bc_item)
    
    return bc_item
 

def create_item(pd):
    if pd.get('vendor', None):
        pd['brand_id'] = create_brand(pd['vendor']['name'])
    
    # Remove mainimg property after setting image_filename
    image_filename = pd.get('mainimg', '')
    if image_filename:
        pd.pop('mainimg')

    bigComerce_item = wps_item_to_bc(pd)
    
    # Create BigCommerce product
    rp = requests.post(BIG_STORE_URL % ('products.json',), data=json.dumps(bigComerce_item), headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
    
    # Check for success
    if rp.status_code == 201:
        print "[LOG] Item %s created" % (bigComerce_item['name'],)
        if image_filename:
            product_id = rp.json()['id']
            add_image(image_filename, product_id)
    
    elif rp.status_code == 409 and not OVERWRITE:
        print "[LOG] Cannot continue. Item %s already exists" % (bigComerce_item['name'],)
    
    elif rp.status_code == 409 and OVERWRITE:
        print "[LOG] Item %s already exists. Overwriting..." % (bigComerce_item['name'],)
        existing_product = requests.get(BIG_STORE_PRODUCT_URL, params={'name': bigComerce_item['name']}, headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
        existing_product = existing_product.json()
        product_id = existing_product[0]['id']
        requests.delete(BIG_API + 'products/%s.json' % (product_id,),
                        headers = BIG_HEADERS, auth = (BIG_USER, BIG_KEY))
        print '[LOG] Deleted item %s' % (bigComerce_item['name'],)
        rp = requests.post(BIG_STORE_PRODUCT_URL, data=json.dumps(bigComerce_item), headers = BIG_HEADERS, auth=(BIG_USER, BIG_KEY))
        
        # Get product ID and add image if one exists
        if image_filename:
            product_id = rp.json()['id']
            add_image(image_filename, product_id)
        
        print "[LOG] Item %s created" % (bigComerce_item['name'],)
    elif DEBUG:
        print "[DEBUG]", rp.text
        print '[DEBUG] Could not create item %s' % (bigComerce_item['name'],)
 
if __name__ == '__main__':
    if len(sys.argv) > 2:
        CATNAME = sys.argv[1]
        CATID = create_category(CATNAME)
        
        # Open and read input file
        f = open(sys.argv[2])
        f = f.readlines()
        
        for part_number in f:
            part_number = part_number.rstrip('\n')
            part_info = get_part_info(part_number)
            if part_info:
                if DEBUG:
                    print "[DEBUG] Name: " + part_info['description']
                create_item(part_info)
    else:
        print 'Correct syntax is import.py categoryname FILE.TXT\nFILE.TXT is a plain text file with a part number on each line'
 
