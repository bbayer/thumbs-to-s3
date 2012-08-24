#!/usr/bin/env python
""" Thumbs to S3
Thumbnail generator for Amazon S3
Author: bbayer 
https://github.com/bbayer
"""

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from optparse import OptionParser
from os.path import isfile,basename
from urlparse import urlparse

import re
import urllib
import urllib2
import tempfile
import sys
import unicodedata
import json
import Image

def slugify(value):
  """ Normalizes string, converts to lowercase, removes non-alpha characters,
  and converts spaces to hyphens.
  """
  value = unicode(value)
  value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
  value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
  return re.sub('[-\s]+', '-', value)
  
def create_s3_conn(key, secret, bucket):
  """ Creates a S3 connection and returns connection and bucket object together """
  conn = S3Connection(key, secret)
  bucket = conn.get_bucket(bucket)
  return conn, bucket

def upload_file( filepath, bucket):
  """ Uploads file with filepath to a bucket. Bucket shall be boto.s3.bucket object
  Uploaded file has key name as its filename and it will be publicly accessible
  """
  try:
    k = Key(bucket)
    k.key = basename(filepath)
    k.set_contents_from_filename(filepath)
    k.set_acl('public-read')
  except Exception,e:
    print e
    return None
  return k

def print_upload_data(opts, data):
  if opts.output == "text":
    for d in data:
      print "%s\t%s\t%d\t%d" %( d['filename'], d['url'], d['width'], d['height'] )
  elif opts.output == "json":
    print json.dumps(data)
  elif opts.output == "post":
    try:
      headers = {'Content-Type':'application/x-www-form-urlencoded'}
      params = urllib.urlencode({'data':json.dumps(data)})
      req = urllib2.Request(opts.callback_url,params,headers)
      response = urllib2.urlopen(req)
      print response.read()
    except Exception,e:
      sys.stderr.write("An error occured while posting to url: %s : %s" % (opts.callback_url,e) )
      sys.exit(3)
    
  
def create_thumbnail( infile, outfile, size ):
  """ Creates a thumbnail from infile and save it to outfile with specified size.
  Size must be a tuple with (width,height)
  It will terminate execution if something went wrong. Yes I am too lazy to implement full error flow control.
  """
  try:
    im = Image.open(infile)
    im.thumbnail(size,Image.ANTIALIAS)
    im.save(outfile,"JPEG")
    return im.size
  except IOError,e:
    sys.stderr.write("An error occured while creating thumbnail:%s",e)
    sys.exit(3)
  
def options():
  """ Parses command line arguments """
  usage = "usage: %prog [options] file_or_url"
  parser = OptionParser(usage=usage)
  parser.add_option("-k", "--key",
                    dest="key", help="AWS Key")
  parser.add_option("-s", "--secret",
                    dest="secret", help="AWS Secret")
  parser.add_option("-b", "--bucket",
                    dest="bucket", help="S3 bucket name")
  parser.add_option("-u", "--upload-original",
                    dest="upload_original", action="store_true", default=False, help="Upload original file to S3")
  parser.add_option("-t", "--thumb-size",
                    dest="thumbnails", action="append", type="string", help="Size of thumbnail. It should be form of WxH\
                    (Note that resize always preserves aspect ratio.)")
  parser.add_option("-o", "--output",
                    dest="output", default="text", help="Output format : json,post,text", type="choice", choices=["json","post","text"])
  parser.add_option("-c", "--callback-url",
                    dest="callback_url", help="Callback url for post output format" )
  (options,args) = parser.parse_args()
  
  if len(args) != 1:
    parser.error("No file or url specified.")
    
  if not options.key:
    parser.error("No AWS key specified")
    
  if not options.secret:
    parser.error("No AWS secret specified")
    
  if not options.bucket:
    parser.error("No bucket specified");
  
  if options.output == "post" and not options.callback_url:
    parser.error("Callback url shall be specified for post output type");
    
  if options.thumbnails != None:
    for t in  options.thumbnails:
      if re.search(r'^\d+x\d+$',t) == None:
        parser.error("Thumbnail size specification should be in WxH format. :%s" % t)
  return (options,args[0])

def get_filename_from_url(url):
  """ Creates a filename from specified url """
  
  parsed_url = urlparse(urllib2.unquote(url))
  retval = basename(parsed_url.path)
  return retval
  
def main():
  """ Program entry point. Here is what is going on
  1. Check CL arguments.
  2. Find whether supplied file is url or local file.
  3. Download file if it is remote.
  4. Create a S3 connection.
  5. Create thumbnails and upload them.
  6. Print information about files in specified format.
  """
  (opts,path) = options()
  real_path = None
  uploaded_files = []
  #Determine argument is file or url
  if isfile(path):
    real_path = path
  else:
    #If url specified download to local
    try:
      f = urllib2.urlopen(path)
    except:
      sys.stderr.write("An error occured while downloading image file: %s\n" % path)
      sys.exit(2)
    tmpfile = open(get_filename_from_url(path),"w+b");
    real_path = tmpfile.name
    tmpfile.write(f.read())
    tmpfile.close()
  
  urlbase = "https://s3.amazonaws.com/%s/" % opts.bucket
  #Check whether file is correct
  if real_path == None:
    sys.stderr.write("Specified file couldn't be found: %s\n" %path);
    sys.exit(3);

  #Create a connection object to S3. If an error occured terminate.
  try:
    conn, bucket = create_s3_conn(opts.key,opts.secret,opts.bucket)  
  except:
    sys.stderr.write("An error occured while uploading files to S3. Check your key/secret and bucket name")
    sys.exit(3);
  
  #Upload original if it is specified from command line
  if opts.upload_original:
    im = Image.open(real_path)
    data = { 'width':im.size[0], 
             'height':im.size[1],
             'filename':basename(real_path),
             'url':urlbase+basename(real_path) }
    if( upload_file( real_path, bucket ) != None):
      uploaded_files.append(data)
    
  #If there is parameters specified, create thumbnails accordingly
  if opts.thumbnails != None:
    for t in opts.thumbnails:
      #Parse size parameters WxH => (w,h)
      size = tuple([ int(x) for x in t.split("x")])
      tmpfile = "thumb-%s-%d-%d.jpg" % ( slugify(basename(real_path)), size[0], size[1] )
      actual_size = create_thumbnail(real_path, tmpfile, size)
      data = { 'width': actual_size[0],
               'height': actual_size[1],
               'filename': tmpfile,
               'url':urlbase+tmpfile }
      if( upload_file( tmpfile, bucket ) != None):
        uploaded_files.append(data)
  
  #Finally print or send information of successfully uploaded files
  print_upload_data( opts, uploaded_files )

if __name__ == '__main__':
  main()