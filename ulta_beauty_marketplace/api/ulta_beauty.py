from curl_cffi import requests
from parsel import Selector
import header_cookies as hc
import json
import ftfy
import unicodedata
from unidecode import unidecode

def get_needed_data_at_once(json_data):
    t = {
        "Average Ratings": "N/A",
        "Num Ratings": "N/A",
        'images':[],
        'Name' :'N/A',
        'Mrp' : 'N/A',
        'Category' : 'N/A',
        'Brand' : 'N/A',
        'Sale Price' : 'N/A',
        'Price Currency' : 'N/A',
        'Final Price' : 'N/A',
        'Discount' : 'N/A',
        'Description' : 'N/A',
        'Size' : 'N/A',
        'Color' : 'N/A',
    }
    for pdp_sec in json_data['modules']:
        if pdp_sec['type'] == 'ProductInformation':
            try:
                t['Average Ratings'] = pdp_sec['rating'] or "N/A"
                t['Num Ratings'] = pdp_sec['reviewCount'] or "N/A"
            except:
                pass
        elif pdp_sec['type'] == 'MediaGallery':
            t['images'] = [x['imageUrl'] for x in pdp_sec['items']]
        elif pdp_sec['type'] == 'ProductPricing':
            try:
                t['Name'] = pdp_sec['productName']
            except:
                pass
            t['Mrp'] = int(float(pdp_sec.get('listPrice').replace("$", "").replace(",", ""))) if pdp_sec.get(
                'listPrice') else "N/A"
            t['Sale Price'] = int(float(pdp_sec.get('salePrice').replace("$", "").replace(",", ""))) if pdp_sec.get(
                'salePrice') else "N/A"
            t['Category'] = pdp_sec['productCategory']
            t['Brand'] = pdp_sec.get('brandName', "N/A")
            t['Price Currency'] = pdp_sec.get('afterpay', {}).get('currency', "N/A")
        elif pdp_sec['type'] == 'ProductDetail':
            t['Description'] = clean_text(pdp_sec['description'].replace("\n", "").replace("####", "|").strip("|").replace("Features-",
                                                                                                           "Features: ").replace(
                "Benefits-", "Benefits: ").replace("Research Results-", "Research Results: ").replace(
                "Key Ingredients-", "Key Ingredients: ").strip())
        elif pdp_sec['type'] == 'ProductVariant':
            try:
                if pdp_sec['dimensionsLabel'] == 'Size':
                    t['Size'] = pdp_sec['dimensionsValue']
            except:
                pass
        elif pdp_sec['type'] == 'ProductReviews':
            if pdp_sec['variantType'] == "color":
                try:
                    t['Color'] = pdp_sec["variantName"]
                except:
                    pass
    t['Final Price'] = t['Mrp']
    if t['Sale Price'] != 'N/A':
        t['Final Price'] = t['Sale Price']
        t['Discount'] = round(t['Mrp'] - t['Sale Price'], 2)
        t['IsOnSale'] = "Yes"
    else: t['Sale Price'] = t['Mrp']
    return t


def clean_text(text: str) -> str:
    try:
        text = ftfy.fix_text(text)
        text = unicodedata.normalize("NFC", text)
        text = unidecode(str(text))
        return text.strip()
    except Exception as e:
        print(e)
        return text


def get_variation(record, json_data):
    variants = {}
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductVariant':
                try:
                    type_of_variant = pdp_sec['variantType']
                except:
                    type_of_variant = "N/A"
                if pdp_sec['variants']:
                    for variant in pdp_sec['variants']:
                        item = {}
                        item['available'] = True if not variant['outofStockLabel'] else False
                        item['type'] = type_of_variant
                        short_var_desc = variant.get("shadeDescription", "N/A") if variant.get("shadeDescription") else "N/A"
                        if "color" in type_of_variant.lower():
                            item['Color'] = f"{variant['name']} ({short_var_desc})" if short_var_desc != "N/A" else variant['name']
                            item['Size'] = record['Size']
                            item['Other'] = "N/A"
                        elif "size" in type_of_variant.lower():
                            item['Color'] = record['Color']
                            item['Size'] = variant['name']
                            item['Other'] = "N/A"
                        elif "N/A" in type_of_variant:
                            item['Color'] = record['Color']
                            item['Size'] = record['Size']
                            item['Other'] = "N/A"
                        else:
                            item['Color'] = record['Color']
                            item['Size'] = record['Size']
                            try:
                                item['Other'] = clean_text(variant['name'])
                            except:
                                item['Other'] = "N/A"
                        if not item['Size']:
                            item['Size'] = "N/A"
                        if not item['Color']:
                            item['Color'] = "N/A"
                        item['variant_id'] = variant['skuId']
                        variants[variant['skuId']] = item
    except Exception as e:
        print(e)
    return variants

def extract_metadata(url, response):
    item = {}
    raw_data = response.xpath("//script[@id='apollo_state']//text()").get()
    if raw_data:
        raw_data = json.loads(raw_data.split("window.__APOLLO_STATE__ =")[-1].split("window.__AUTH0_CALLBACK__")[0].strip())
        key_to_data = [x for x in list(raw_data['ROOT_QUERY'].keys()) if "Page(" in x][0]
        data = raw_data['ROOT_QUERY'][key_to_data]['content']
        pdp_data_json = None
        for module in data['modules']:
            if module['moduleName'] == "MainWrapper":
                for sub_modules in module['modules']:
                    if sub_modules['type'] == 'ProductHero':
                        pdp_data_json = sub_modules
                        break
        if not pdp_data_json: return None
        whole_data = get_needed_data_at_once(pdp_data_json)
        unique_url = url.split("?")[0]
        sku = url.split("?")[-1].replace("sku=", "").strip()
        pid = unique_url.split("-")[-1].strip()
        variant_data = get_variation({'Color':whole_data['Color'], 'Size':whole_data['Size']}, pdp_data_json)
        others = variant_data.get(sku, {}).get("Other", "N/A")
        item['Name'] = whole_data['Name']
        image_data = whole_data['images']
        if image_data:
            item['Image URL'] = image_data[0]
        else:
            item['Image URL'] = "N/A"
        item['SKU'] = sku
        item['PID'] = pid
        item['IsInStock'] = "True" if variant_data.get(sku, {}).get("available", None) else "False"
        item['Price Currency'] = whole_data['Price Currency']
        item['Sale Price'] = str(whole_data['Sale Price'])
        item['Final Price'] = str(whole_data['Final Price'])
        item['Mrp'] = whole_data['Mrp']
        item['Discount'] = whole_data['Discount']
        item['Manufacturer'] = "N/A"
        item['Brand'] = whole_data['Brand']
        item['Colour'] = variant_data.get(sku, {}).get("Color", None) if variant_data else whole_data['Color']
        item['Num Ratings'] = whole_data['Num Ratings']
        item['Average Ratings'] = whole_data['Average Ratings']
        item['Gender'] = "N/A"
        if image_data:
            item['Alternate Image URLs'] = " | ".join(image_data[1:]) if len(
                image_data) > 2 else "N/A"
        item['Link URL'] = url
        item['Category'] = whole_data['Category'].replace(":", "/")
        item['Description'] = whole_data['Description']
        item['Size'] = variant_data.get(sku, {}).get("Size", None) if variant_data else whole_data['Size']
        item['Varint_Price'] = f"{item['Final Price']}"
        if variant_data:
            try:
                del variant_data[sku]
            except:
                pass
            variant_data = list(variant_data.values())
            for var in variant_data:
                del var['type']
                del var['variant_id']
            item['Variant_data'] = variant_data
        item['policy'] = []
        item['Other'] = others
        return item


def fetch_response(url):
    try:
        response = requests.get(
            url,
            cookies=hc.data_cookies,
            headers=hc.data_headers,
        )
        if response.status_code == 200:
            return Selector(response.text)
        else:
            print("Incorrect pdp response", response.status_code)
            return None
    except Exception as e:
        print("Error while fetching response: ", e)

def main(url):
    response = fetch_response(url)
    if not response:
        return None
    data = extract_metadata(url, response)
    if not data:
        return None
    return data



if __name__ == "__main__":
    print(main("https://www.ulta.com/p/studio-fix-powder-plus-foundation-pimprod2051406?sku=2635749"))