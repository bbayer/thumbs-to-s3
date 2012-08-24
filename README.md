# Thumbs to S3 #

Thumbs to S3 is a simple command-line tool for creating thumbnails on Amazon S3

## Usage ##

```bash
Usage: thumbs_to_s3.py [options] file_or_url

Options:
  -h, --help            show this help message and exit
  -k KEY, --key=KEY     AWS Key
  -s SECRET, --secret=SECRET
                        AWS Secret
  -b BUCKET, --bucket=BUCKET
                        S3 bucket name
  -u, --upload-original
                        Upload original file to S3
  -t THUMBNAILS, --thumb-size=THUMBNAILS
                        Size of thumbnail. It should be form of WxH
                        (Note that resize always preserves aspect ratio.)
  -o OUTPUT, --output=OUTPUT
                        Output format : json,post,text
  -c CALLBACK_URL, --callback-url=CALLBACK_URL
                        Callback url for post output format

```

## Installation ##

You need to install dependencies before using Thumbs to S3

```bash
$ easy_install boto
$ easy_install pil
``` 

## Examples ##

Thumbs to S3 both supports local and remote files. Both examples will create two thumbnails with sizes of 75x50 and 320x240.

Don't forget to put your valid AWS key, secret and bucket name.

```bash
$ python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  -t 75x50 -t 320x240 http://www.worldsfamousphotos.com/wp-content/uploads/2008/01/lunch.jpg
```

```bash
$ python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  -t 75x50 -t 320x240 lunch.jpg
```

By default tool won't upload original file. To do so you need to add ```--upload-original``` parameter.

```bash
$ python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  --upload-original -t 75x50 -t 320x240 lunch.jpg
``` 

If you don't specify any output format, Thumbs to S3 will output text information about created files. This will include filename, S3 public url , width and height

```bash
$ python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  --upload-original -t 75x50 -t 320x240 lunch.jpg

lunch.jpg	https://s3.amazonaws.com/mybucket/lunch.jpg	480	390
thumb-lunchjpg-75-50.jpg	https://s3.amazonaws.com/mybucket/thumb-lunchjpg-75-50.jpg	62	50
thumb-lunchjpg-320-240.jpg	https://s3.amazonaws.com/mybucket/thumb-lunchjpg-320-240.jpg	295	240

``` 

You may also want to output more structured format. This might be useful if you plan to invoke Thumbs to S3 within another application. You can see the JSON output below.

```bash
$ python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  -o json --upload-original -t 75x50 -t 320x240 lunch.jpg

[{"url": "https://s3.amazonaws.com/mybucket/lunch.jpg", "width": 480, "filename": "lunch.jpg", "height": 390}, {"url": "https://s3.amazonaws.com/mybucket/thumb-lunchjpg-75-50.jpg", "width": 62, "filename": "thumb-lunchjpg-75-50.jpg", "height": 50}, {"url": "https://s3.amazonaws.com/mybucket/thumb-lunchjpg-320-240.jpg", "width": 295, "filename": "thumb-lunchjpg-320-240.jpg", "height": 240}]
```

Here is an PHP example that shows the concept.

```php
<?php
exec('python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  -o json --upload-original -t 75x50 -t 320x240 lunch.jpg', $output);
$output = implode(" ",$output);
print_r(json_decode($output));
?>
```

This code will output;

```php

Array
(
    [0] => stdClass Object
        (
            [url] => https://s3.amazonaws.com/mybucket/lunch.jpg
            [width] => 480
            [filename] => lunch.jpg
            [height] => 390
        )

    [1] => stdClass Object
        (
            [url] => https://s3.amazonaws.com/mybucket/thumb-lunchjpg-75-50.jpg
            [width] => 62
            [filename] => thumb-lunchjpg-75-50.jpg
            [height] => 50
        )

    [2] => stdClass Object
        (
            [url] => https://s3.amazonaws.com/mybucket/thumb-lunchjpg-320-240.jpg
            [width] => 295
            [filename] => thumb-lunchjpg-320-240.jpg
            [height] => 240
        )

)
```

You can also post JSON output to an URL. This could be useful for creating notifications about thumbnail generation.

```sh
python thumbs_to_s3.py -k <AWS_KEY> -s <AWS_SECRET> -b mybucket  -o post -c http://www.mysite.com/callback.php -t 75x50 -t 320x240 http://www.worldsfamousphotos.com/wp-content/uploads/2008/01/lunch.jpg
```

On your server side you can access posted data like below.

```php
<?php
print_r(json_decode($_POST['data']));
?>
```