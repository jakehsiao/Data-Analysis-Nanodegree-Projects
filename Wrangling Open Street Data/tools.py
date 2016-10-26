# -*- coding: utf-8 -*- 
'''indentation:........'''

#入库调试完成啦~没问题哦~接下来就是 嗯 名字改一下的问题咯

import xml.etree.cElementTree as ET
import pprint
from collections import defaultdict
import re
import csv
import codecs
import time

'''constants are written here'''
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street",
            "St.": "Street",
           'Av':"Avenue",
            "Ave":"Avenue",
            'Ave.':'Avenue',
           'Aven':'Avenue',
            'Rd':'Road',
            'Rd.':'Road',
           'Cir':'Circle'
            }

PATH_HEADER="F:\Hsiao's studying\Computing\Udacity P3\\"
#OSM_PATH = "F:\Hsiao's studying\Computing\Udacity P3\sample.osm"
OSM_PATH = "F:\Hsiao's studying\Computing\Udacity P3\los-angeles_california.osm"

NODES_PATH = PATH_HEADER+"nodes.csv"
NODE_TAGS_PATH = PATH_HEADER+"nodes_tags.csv"
WAYS_PATH = PATH_HEADER+"ways.csv"
WAY_NODES_PATH =PATH_HEADER+ "ways_nodes.csv"
WAY_TAGS_PATH = PATH_HEADER+"ways_tags.csv"
# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']



def count_tags(filename):
        # return a dict with tags, how many times represented
    tags={}
    with open(filename,'r') as f:
        tree=ET.parse(f)
        root=tree.getroot()
        ita=root.iter() # iterator can be directly used in for loop
        for this in ita:
            if this.tag in tags:
                tags[this.tag]+=1
            else:
                tags[this.tag]=1
        return tags



def key_type(element, keys):
    '''subfunction of the below one'''
    cases=[[lower,'lower'],[lower_colon,'lower_colon'],[problemchars,'problemchars']]
    if element.tag == "tag":
        # YOUR CODE HERE
        # I should use another re which means everything to better finish this code but my skill is not enough
        kval=element.attrib['k']
        got=False
        for case in cases:
            if case[0].search(kval)!=None:
                keys[case[1]].append(kval)
                got=True
                break
        if not got:
            keys['other'].append(kval)
    return keys

def find_problem_key(filename):
    '''
        show the num problem keys
        should be changed with lists
    '''

    keys = {"lower": [], "lower_colon": [], "problemchars": [], "other": []}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
        # how awesome this code it is, iteractive dictionary!
    return keys

def get_unique_users(filename): # can be replaced by SQL query
    print 'start operating'
    users = []
    for _,element in ET.iterparse(filename):
        if element.tag in ['node','way','relation']:
            id=element.attrib['uid']
            users.append(id)
    return set(users)




def audit_street_type(street_types, street_name):
    '''subfunc of below'''
    m = street_type_re.search(street_name)
    if m: #this hand is awesome, not none haha
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    '''subfunc of below'''
    return (elem.attrib['k'] == "addr:street")


def type_count(osmfile):
    '''return how many street types have been presented'''
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types


def update_name(name, mapping):
    '''change the name from abbr to fullname, this code is better than the before version'''
    # YOUR CODE HERE
    name=name.split()
    # first, dict is itered in key
    # then, ' '.join(iter) is a good way
    if name[-1] in mapping:
        name[-1]=mapping[name[-1]]
    return ' '.join(name)


def update_postcode(postcode):
    postcode=str(postcode)
    if len(postcode)==5:
        return postcode
    if len(postcode)!=5 and postcode[0].isdigit():
        return postcode[:5]
    elif not postcode[0].isdigit():
        for i in range(len(postcode)):
            if postcode[i].isdigit():
                return postcode[i:i+5]




def tag_attrib(this,id):
    '''subfunc of below'''
    tagAttrib={'id':id,'value':'NotFound','type':'NotFound','key':'NotFound'}
    try:
        tagAttrib['value']=this['v']
        kContent=this['k'].split(':')
        if len(kContent)==1:
            kContent=['regular']+kContent # so fuckin ugly
        tagAttrib['type']=kContent[0]
        tagAttrib['key']=':'.join(kContent[1:])

        '''for different situations, wranglin process would do other auditions'''
        if this['k']=="addr:street":
            tagAttrib['value']=update_name(tagAttrib['value'],mapping)
        elif this['k']=="addr:postcode":
            tagAttrib['value']=update_postcode(tagAttrib['value'])
    
    except Exception as e:
        print 'tag insertion error:',e
        print this
        time.sleep(1)
    return tagAttrib

def dictMatching(attribs,fromDict):
    '''subfunction for below'''
    toDict={}
    for i in attribs:
        try:
            toDict[i]=fromDict[i]
        except Exception as e:
            print 'dict matching error:',e,'not found'
            print fromDict
            toDict[i]='NotFound'
            time.sleep(1)
    return toDict



def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=problemchars, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict
        subfunc of below
    """

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    nid=0
    ndPos=0
    
    # YOUR CODE HERE
    if element.tag == 'node':
        nid=element.attrib['id']
        # for i in node_attr_fields:
        #     try:
        #         node_attribs[i]=element.attrib[i]
        #     except Exception as e:
        #         print e
        #         print 'notFound'
        node_attribs=dictMatching(node_attr_fields,element.attrib)
        tagnum=len(element.findall('tag'))
        have_tag=(tagnum>0)
        if have_tag:
            for i in element.findall('tag'):
                this=i.attrib
                tags.append(tag_attrib(this,nid))
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        wid=element.attrib['id']
        way_attribs=dictMatching(way_attr_fields,element.attrib)
        children=element.findall('nd')+element.findall('tag')
        tagnum=len(children)
        have_tag=(tagnum>0)
        if have_tag:
            for i in children:
                this=i.attrib
                tagAttrib={}
                tagAttrib['id']=wid
                if i.tag=='nd':
                    tagAttrib['position']=ndPos
                    ndPos+=1 #update the index
                    tagAttrib['node_id']=this['ref']
                    way_nodes.append(tagAttrib)
                
                elif i.tag=='tag':
                    tags.append(tag_attrib(this,wid))
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# def validate_element(element, validator, schema=SCHEMA):
#     """Raise ValidationError if element does not match schema"""
#     if validator.validate(element, schema) is not True:
#         field, errors = next(validator.errors.iteritems())
#         message_string = "\nElement of type '{0}' has the following errors:\n{1}"
#         error_strings = (
#             "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
#             for k, v in errors.iteritems()
#         )
#         raise cerberus.ValidationError(
#             message_string.format(field, "\n".join(error_strings))
#         )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate=False):
    """Iteratively process each XML element and write to csv(s)"""
    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        # validator = cerberus.Validator()
        COUNT=0

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                # if validate is True:
                #     validate_element(el, validator)
                COUNT+=1
                if COUNT%200000==0:
                    print COUNT,'on processing'
                    time.sleep(0.3)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__=='__main__':
    # probKey=find_problem_key(OSM_PATH)
    # for i in probKey:
    #     print i,':',len(probKey[i])
    '''吼吼吼 发现了很多lower呢 回头一定要汇报一下了啦'''
    # tc=type_count(OSM_PATH)
    # for i in tc:
    #     print i,':',tc[i]
    #     time.sleep(0.3)
    '''吼吼吼 发现简写了哦 回头可要认真的改一下呢'''
    print 'start writing'
   # process_map(OSM_PATH)
    print 'finish writing'
    # 注意这里改动过 改过的都打##了 回头删除以下




