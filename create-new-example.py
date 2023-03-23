
from string import Template
import argparse
import os
import json
import shutil
import re


def create_parser():
    parser = argparse.ArgumentParser(description='Add a sample to Readme.md and copy all images')

    parser.add_argument('outputFilePath', type=str,
                        help='full path to final output image, imples location of input.json')

    parser.add_argument('shortName', type=str,
                        help='single word description of this sample')

    

    return parser



def generateAddToReadme(values):
    '''
    Generate the snippet of text to append to Readme.md for the sample being added.
    values: dictionary of strings used in the template
      'humanTitle'       - one word description
      'sampleDirectory'  - directory under ./samples for the sample
      'width'
      'height'           - width and height HTML attributes for the images
      'contentImagePath' -
      'styleImagePath'   -
      'outputImagePath'  - 
    '''
    
    template = Template('''
### $humanTitle [Full output directory]($sampleDirectory)

<img title="$titleContentImage" width="$width" height="$height"
     src="$contentImagePath" >
<img title="$titleStyleImage" width="$width" height="$height"
     src="$styleImagePath" >
<img title="$titleOutputImage" width="$width" height="$height"
     src="$outputImagePath" >
''')


    
    output = template.safe_substitute(values)

    return output


def get_output_directory_from(output_top_dir, short_name):
    if not os.path.isdir(output_top_dir):
        raise Exception(f"output top is not a directory: {output_top_dir}")

    today = date.today()
    yyyy = today.year
    mm = today.month
    dd = today.day
    yyyymmdd = f"{yyyy}-{mm:02}-{dd:02}"

    output_directory  = yyyymmdd + "-" + short_name

    #
    # check exists:
    #
    if os.path.isdir(output_top_dir + "/" + output_directory):
        raise Exception(f"sample output directory {output_directory} already exists in {output_top_dir}")
    
    return output_directory

def get_input_json_from_outputfilepath(pathToOutputFile):
    '''
    From the full path of the input file  e.g. ../a/b/output/output0033/a.png,
    return the
      a) filename of input.json "next to it"   ../a/b/output/output0033/input.json
      b) parsed JSON of that input.json
    '''

    dirname = os.path.dirname(pathToOutputFile)
    if not os.path.isdir(dirname):
        raise Exception(f"Programmer error not a directory: {dirname}")
    inputJsonFullPath = dirname + "/input.json"
    if not os.path.isfile(inputJsonFullPath):
        raise Exception(f"sample image {pathToOutputFile} does not have 'input.json' file next to it")
    

    with open(inputJsonFullPath, 'r') as f:
        inputJson = json.load(f)

    return (inputJson, inputJsonFullPath)


def fixslash(path_with_possible_backslashes):
    '''
    There is a bug in some of the input.json where the paths contain
    the strings like "images\\monet.jpg" instead of "images/monet.jpg"
    Fix that.
    '''
    
    ret = path_with_possible_backslashes.replace("\\", "/")
    #print(f"in={path_with_possible_backslashes}  out={ret}")
    
    return ret

def get_epochs_from_filename(filename):
    '''
    input filename e.g. image_00250.jpg
    return 250
    '''
    epochs = None
    match = re.match(r'^[^0-9]*([0-9]+).*$', filename)
    if match:
        digits = match.group(1)
        epochs = int(match.group(1))
    return epochs
    
def process_input_json(values, inputJson, inputJsonFullPath):
    '''
    The values we compute are:
    source_top_directory (path)   "{inputJsonFullPath}/../.."  [TODO: hardcoded]
    content_shortname   just the filename "louvre.jpg"
    style_shortname     just the filename "monet.jpg"
    
    orig_content_image_path   "{source_top_directory}/images/louvre.jpg"
    orig_style_image_path     "{source_top_directory}/images/monet.jpg"
    orig_output_image_path    "{source_top_directory}/
        "content_image_filename":
    '''

    print(f"intputJsonFullPath is {inputJsonFullPath}")
    
    keys =[ 'output_dir_top', 'content_image_filename', 'style_image_filename' ]
    for key in keys:
        if not key in inputJson:
            raise Exception(f"input.json did not contain key {key}")

    # drop 'input.json':
    inputJsonDirectory = os.path.dirname(inputJsonFullPath)
    # go "up" two directories:
    source_top_directory = os.path.dirname(os.path.dirname(inputJsonDirectory))
    print(f"source_top_directory is {source_top_directory}")
    
    if not os.path.isdir(source_top_directory):
        raise Exception(f"programmer error, not a directory: {source_top_directory}")

    values['content_image_path'] = fixslash( inputJson['content_image_filename'] )
    values['orig_content_image_path'] = f"{source_top_directory}/{values['content_image_path']}"

    values['style_image_path'] = fixslash( inputJson['style_image_filename'] )
    values['orig_style_image_path'] = f"{source_top_directory}/{values['style_image_path']}"


    values['orig_input_json_path'] = inputJsonFullPath
    
    #
    # safety checks:
    #
    thefile = values['orig_content_image_path']
    if not os.path.isfile(thefile):
        raise Exception(f"Programmer error, content not a file: {thefile}")

    thefile = values['orig_style_image_path']
    if not os.path.isfile(thefile):
        raise Exception(f"Programmer error, style not a file: {thefile}")

    thefile = values['orig_input_json_path']
    if not os.path.isfile(thefile):
        raise Exception(f"Programmer error, input.json not a file: {thefile}")    


    values['contentImagePath'] = "images/" + os.path.basename(values['content_image_path'])
    values['styleImagePath'] = "images/" + os.path.basename(values['style_image_path'])
    values['outputImageName'] = os.path.basename( values['orig_outputfile_path'] )
    values['outputImagePath'] = values['sampleDirectory'] + "/" + values['outputImageName']

    # parse epochs
    epochs = get_epochs_from_filename(values['outputImageName'])
    if epochs:
        values['outputImageEpoch'] = epochs

    if values['outputImageEpoch']:
        values['titleOutputImage'] = f"{values['outputImageEpoch']} epochs"
    else:
        values['titleOutputImage'] = ''



def do_work(values):
    '''
    1) make output directory
    2) copy images into output directory
    3) copy input.json into output directory
    '''
    our_output_directory = values['sampleDirectory']
    os.mkdir( our_output_directory )

        
    #2) images
    target = "images/" + os.path.basename( values['orig_content_image_path'] )
    if not os.path.isfile(target):
        shutil.copy( values['orig_content_image_path'], "images")

    target = "images/" + os.path.basename( values['orig_style_image_path'] )
    if not os.path.isfile(target):
        shutil.copy( values['orig_style_image_path'], "images")

    source = values['orig_outputfile_path']
    target = values['outputImagePath']
    print(f"copy from {source} to {target}")
    if not os.path.isfile(target):     # this will always be true
        shutil.copyfile(source, target)
    
    #3) input.json
    shutil.copy( values['orig_input_json_path'], our_output_directory)

    # TODO
    output = generateAddToReadme(values)
    print(output)
    if True:
        with open('Readme.md', 'a') as f:
            f.write(output)

    

    
    

if __name__ == '__main__':
    
    from datetime import date
    import sys
    #
    # Arguments:
    #   path-to-output-file
    #      this is the "image_02500.jpg" in the output00NN directory
    #        the output00NN directory contains "input.json"
    #   short-name
    #      one word description of the sample, e.g. "picaso" or "diagonal"
    #
    parser = create_parser()
    args = parser.parse_args()
    
    argPathToOutputFile = args.outputFilePath
    argShortName = args.shortName

    
    outputTopDirectory = "samples"
    justOutputDirectory = get_output_directory_from(outputTopDirectory,
                                                    argShortName)

    (inputJson, inputJsonFullPath) = get_input_json_from_outputfilepath(argPathToOutputFile)

    values = {}
    values['titleContentImage'] = "content image"
    values['titleStyleImage'] = "style image"
    values['sampleDirectory'] = outputTopDirectory + "/" + justOutputDirectory    
    values['orig_outputfile_path'] = argPathToOutputFile
    process_input_json(values, inputJson, inputJsonFullPath)
    

    values['height'] = "200px"
    values['width'] = "200px"
    values['humanTitle'] = argShortName.capitalize()

    #values['contentImagePath'] = "images/louvre_small.jpg"
    #values['styleImagePath'] = "images/grid400x400-offset-40x40.png"




    do_work(values)

    # CDP10047  batteries plus
    
