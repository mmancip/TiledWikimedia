#!/bin/env python3

#req:
# python3-pip install metadata_parser

import sys,os
import argparse
import re
from datetime import datetime
import json

import metadata_parser

import requests
from bs4 import BeautifulSoup

import traceback

def parse_args(argv):
    parser = argparse.ArgumentParser(
        'Build a nodes.json TiledViz tileset file from wikimedia site.')
    parser.add_argument('-n', '--nodes', type=int, default=5,
                        help='Number of nodes (default: 5)')
    parser.add_argument('--name', default='nodes.json',
                        help='File name for nodes.json output')
    args = parser.parse_args(argv[1:])
    return args

if __name__ == '__main__':
    args = parse_args(sys.argv)

    epoch_now = datetime.now().timestamp()
    
    json_tiles=[]
    
    inode=0
    while inode<args.nodes:

        testpage=True
        thistile={}
        
        while testpage:
            page = metadata_parser.MetadataParser(url="https://commons.m.wikimedia.org/wiki/Special:Random#/random",search_head_only=False)
            realURL=page.metadata['_internal']['url_actual']
            print("test page "+realURL)
            req = requests.get( realURL )
            soup = BeautifulSoup(req.text, 'html.parser') #, "lxml")
            desc=soup.select("[class*=commons-file-information-table] > table")
            soupdesc = BeautifulSoup(str(desc[0]), "html.parser")
            metadata=soup.select("[class*=mw-imagepage-section-metadata] > table")
            
            if ( len(metadata) > 0 and re.search("(jpg|JPG|png|PNG)",realURL) ):
                testpage=False

                exif=soup.select("[class*=mw_metadata]")[0]

                try:
                    thistile["title"]=soupdesc.select("[class*=description] > span")[0].next_sibling.replace("(","")[:80]
                    thistile["url"]=soup.select("[class*=fileInfo]")[0].parent.a["href"]

                    tagauthor=""
                    hrefauthor=""
                    try:
                        tag=soupdesc.find(id="fileinfotpl_src").next_sibling.next_sibling
                        hrefauthor=tag.find("a")["href"]
                        tagauthor=tag.find("a").string
                    except:
                        pass
                    
                    tag=soupdesc.find(id="fileinfotpl_aut").next_sibling.next_sibling
                    tagcreator=tag.find("a")
                    author=tagauthor+" "+hrefauthor+" "+tagcreator["title"].replace("User:","")
                    thistile["usersNotes"]=author

                    tag=soupdesc.find(id="fileinfotpl_date").next_sibling.next_sibling
                    tagtime=tag.find("time")
                    thistile["comment"]=tagtime.string

                    thistile["name"]=soupdesc.table.td.span.string

                    print("page OK.")
                except:
                    testpage=True
                    traceback.print_exc(file=sys.stderr)
                    pass

                if (not testpage):
                    try:
                        tags=[]
                    
                        try:
                            utc_time = datetime.strptime(tagtime["datetime"], "%Y-%m-%d %H:%M:%S")
                        except:
                            utc_time = datetime.strptime(tagtime["datetime"], "%Y-%m-%d")
                        epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
                        tag1="{01_time,0,"+str(epoch_time)+","+str(epoch_now)+"}"
                        tags.append(tag1)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        position=soup.select("[class*=mw-kartographer-maplink]")[0]
                        data_lon=position["data-lon"]
                        tag2 ="{02_lon,-180,"+data_lon+",180}"
                        tags.append(tag2)
                        data_lat=position["data-lat"]
                        tag3 ="{03_lat,-90,"+data_lat+",90}"
                        tags.append(tag3)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        fileInfo=soup.select("[class*=fileInfo]")[0].get_text()
                        p=re.compile('\((?P<width>[0-9,]+) × (?P<height>[0-9,]+) pixels, file size: (?P<size>[0-9.]+) (?P<ubyte>[MK]+)B, .*',re.DOTALL)
                        ma=p.search(fileInfo)
                        #ma.groups()
                        
                        #Image width
                        tag4 = "{04_width,1,"+ma.group("width").replace(",",".")+",16000}"
                        tags.append(tag4)
                        #Image height
                        tag5 = "{05_height,1,"+ma.group("height").replace(",",".")+",16000}"
                        tags.append(tag5)
                        
                        #size (convert byte or byte ?)
                        fsize=ma.group("size").replace(",",".")
                        if (ma.group("ubyte") == "M"):
                            fsize=str(float(fsize)*1000)
                        tag6 = "{06_fsize,1,"+fsize+",100000}"
                        tags.append(tag6)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        #Exposure time
                        et=re.sub('.*\(','',metadata[0].select("[class*=exif-exposuretime] > td")[0].get_text()).replace(')','')
                        tag7 = "{07_expos,0,"+et+",1}"
                        tags.append(tag7)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        #focal
                        f=exif.select("[class*=exif-fnumber] > td")[0].get_text().replace('f/','')
                        tag8 = "{08_focal,1,"+f+",32}"
                        tags.append(tag8)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        #shutterspeed
                        spe=exif.select("[class*=exif-shutterspeedvalue] > td")[0].get_text()
                        tag9 = "{09_shutsp,1,"+spe+",20}"
                        tags.append(tag9)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        #ISO
                        iso=metadata[0].select("[class*=exif-isospeedratings] > td")[0].get_text().replace(",","")
                        tag10 = "{10_iso,50,"+iso+",25000}"
                        tags.append(tag10)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                    try:
                        #aperture
                        aper=exif.select("[class*=exif-aperturevalue] > td")[0].get_text()
                        tag11 = "{11_aper,1,"+aper+",32}"
                        tags.append(tag11)
                    except:
                        traceback.print_exc(file=sys.stderr)
                        pass
                        
                    thistile["tags"]=tags
                    
        #text = soup.find('h1', attrs={"id":"itemTitle"}).text

        json_tiles.append(thistile)
        
        inode=inode+1

    json_nodes={}
    json_nodes["nodes"]=json_tiles
    nodes_json_text=json.JSONEncoder().encode(json_nodes)
    
    with open(args.name,'w+') as f:
        f.write(nodes_json_text)
