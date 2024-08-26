import xmltodict
import json
from lxml import etree
from itertools import islice
import tiktoken
import numpy as np
import tenacity

def validate_xml_with_xsd(xml_file, xsd_file):
    """Validate XML file using schema in XSD file"""
    try:
        with open(xml_file, 'r') as fx, open(xsd_file, 'r') as fs:
            xml_data = fx.read()
            xsd_data = fs.read()
            
            # Convert string data to bytes
            xml_data_bytes = xml_data.encode('utf-8')
            xsd_data_bytes = xsd_data.encode('utf-8')
            
            # Parse the XML and XSD data
            xml_doc = etree.fromstring(xml_data_bytes)
            xmlschema_doc = etree.fromstring(xsd_data_bytes)
            xmlschema = etree.XMLSchema(xmlschema_doc)
            
            # Validate the XML against the XSD
            if xmlschema.validate(xml_doc):
                print("XML is valid according to XSD")
            else:
                print(f"XML is not valid according to XSD: {xmlschema.error_log}")
    except etree.XMLSyntaxError as e:
        print(f"XML is not well-formed: {e}")
    except etree.XMLSchemaParseError as e:
        print(f"XSD schema is not well-formed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")



def parse_xml_to_dict(xml_file):
    """Parse XML file to json format"""
    with open(xml_file, 'r') as f:
        xml_content = f.read()
        return xmltodict.parse(xml_content)
    

    
def clean_dict_data(dict_data):
    """Rename fields and clean data"""
    # Renaming fields
    for data in dict_data['grants_data']['grant']:
        if 'deadlines' in data.keys() and data['deadlines']:
            if isinstance(data['deadlines']['deadline'], list):
                for deadline in data['deadlines']['deadline']:
                    deadline['type'] = deadline.pop('@type')
                    deadline['date'] = deadline.pop('#text')
            else:
                data['deadlines']['deadline']['type'] = data['deadlines']['deadline'].pop('@type')
                data['deadlines']['deadline']['date'] = data['deadlines']['deadline'].pop('#text')

        if 'amounts' in data.keys() and data['amounts']:
            if isinstance(data['amounts']['amount'], list):
                for amount in data['amounts']['amount']:
                    amount['confirmed'] = amount.pop('@confirmed')
                    amount['currency'] = amount.pop('@currency')
                    amount['type'] = amount.pop('@type')
                    amount['value'] = amount.pop('#text')
            else:
                data['amounts']['amount']['confirmed'] = data['amounts']['amount'].pop('@confirmed')
                data['amounts']['amount']['currency'] = data['amounts']['amount'].pop('@currency')
                data['amounts']['amount']['type'] = data['amounts']['amount'].pop('@type')
                data['amounts']['amount']['value'] = data['amounts']['amount'].pop('#text')
        
        if 'locations' in data.keys() and data['locations']:
            if isinstance(data['locations']['location'], list):
                for location in data['locations']['location']:
                    location['is_exclude'] = location.pop('@is_exclude')
                    location['is_primary'] = location.pop('@is_primary')
                    location['type'] = location.pop('@type')
                    if '#text' in location:
                        location['text'] = location.pop('#text')
            else:
                 data['locations']['location']['is_exclude'] =  data['locations']['location'].pop('@is_exclude')
                 data['locations']['location']['is_primary'] =  data['locations']['location'].pop('@is_primary')
                 data['locations']['location']['type'] =  data['locations']['location'].pop('@type')
                 if '#text' in data['locations']['location']:
                    data['locations']['location']['text'] =  data['locations']['location'].pop('#text')

        if 'sponsors' in data.keys() and data['sponsors']:
            if isinstance(data['sponsors']['sponsor'], list):
                for sponsor in data['sponsors']['sponsor']:
                    sponsor['id'] = sponsor.pop('@id')
                    sponsor['name'] = sponsor.pop('#text')
            else:
                data['sponsors']['sponsor']['id'] = data['sponsors']['sponsor'].pop('@id')
                data['sponsors']['sponsor']['name'] = data['sponsors']['sponsor'].pop('#text')
        
        # Cleaning data
        if 'is_limited' in data.keys() and data['is_limited'] =='None':
            data['is_limited'] = '' # ElasticSearch does not accept None

        
    return dict_data

