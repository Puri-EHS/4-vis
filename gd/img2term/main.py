from GD import GD
import numpy
from PIL import Image
from img2term.utils import fcode_opt
from typing import List, Tuple, Literal
from draw_utils import Position
from logger import Logger

PIXEL = "▀" # top half is bg, bottom half is fg

def draw(
    img_path: str, 
    topleft_pos: Position.Relative = Position.Relative(left=0, top=0),
    maxsize: Tuple[int, int] = (None, None), 
    overflow_behavior: Literal['crop', 'scale'] = 'crop') -> None:
    """
    Prints an image to the current terminal window.

    `img_path` path to image file, relative to the current working directory.
    
    `topleft_pos` (custom for vis gd project): A Position.Relative object that specifies the top-left corner of the image.
    
    `maxsize` tuple of (width, height) of the maximum size of the image to be printed. Dimensions
    that are smaller than this won't be affected. maxsize of None means no limit. default is (None, None).
    
    `overflow_behavior` string that determines how the image will be handled if it is larger than
    `maxsize`. If 'crop', the image will be cropped to fit the dimensions. If 'scale', the image
    will be scaled down to fit the dimensions. default is 'crop'.
    """
    im = Image.open(img_path)
    width, height = im.size
    
    # do any resizing if necessary
    if overflow_behavior == 'scale':
        im = im.resize((
            min(maxsize[0], width) if maxsize[0] is not None else width,
            min(maxsize[1], height) if maxsize[1] is not None else height
        ))    
    elif overflow_behavior == 'crop':
        im = im.crop((
            0, 0, 
            min(maxsize[0], width) if maxsize[0] is not None else width,
            min(maxsize[1], height) if maxsize[1] is not None else height
        ))
    else:
        raise ValueError("[img2term] invalid arg in draw(): overflow_behavior must be 'crop' or 'scale'")

    pixels = numpy.array(im, dtype=numpy.uint8)
    
    final_chars: List[List[str]] = []
    for i in range(0, len(pixels)-1, 2): # TODO - last row of odd height images is not being processed
        row = pixels[i]
        row2 = pixels[i + 1]
        
        final_row: List[str] = []
        
        for j in range(len(row)):
            top_pixel = row[j]
            bottom_pixel = row2[j]
            final_row.append("\x1b[0m" + fcode_opt(fg=top_pixel[0:3], bg=bottom_pixel[0:3]) + PIXEL)
            
        final_chars.append(final_row)
    
    final_chars = numpy.array(final_chars)
    
    # draw image at specified pos
    abs_pos = topleft_pos.get_absolute(GD.term.width, GD.term.height)
    Logger.log(f"Drawing image at {abs_pos.left}, {abs_pos.top}")
    for row in range(len(final_chars)):
        # dont draw if out of bounds
        if not 0 <= abs_pos.top+row < GD.term.height: continue
        if not abs_pos.left < GD.term.width or abs_pos.left+len(final_chars[row]) < 0: continue
        print(GD.term.move_xy(abs_pos.left, abs_pos.top+row) + ''.join(final_chars[row]) + '\x1b[0m')

def draw_from_pixel_array(
    _pixels: numpy.ndarray | List[List[List[int]]],
    topleft_pos: Position.Relative = Position.Relative(left=0, top=0)) -> None:
    """
    Draws an image from a numpy array of pixels.
    
    `pixels` a numpy array of pixels, where each pixel is an array of 3 ints representing RGB values.
    
    `topleft_pos` (custom for vis gd project): A Position.Relative object that specifies the top-left corner of the image.
    """
    
    # if pixels is a list of lists, convert it to a numpy array
    if type(_pixels) == list:
        pixels = numpy.array(_pixels)
    
    final_chars: List[List[str]] = []
    for i in range(0, len(pixels)-1, 2): # TODO - last row of odd height images is not being processed
        row = pixels[i]
        row2 = pixels[i + 1]
        
        final_row: List[str] = []
        
        for j in range(len(row)):
            top_pixel = row[j]
            bottom_pixel = row2[j]
            final_row.append("\x1b[0m" + fcode_opt(fg=top_pixel[0:3], bg=bottom_pixel[0:3]) + PIXEL)
            
        final_chars.append(final_row)
    
    final_chars = numpy.array(final_chars)
    
    # draw image at specified pos
    abs_pos = topleft_pos.get_absolute(GD.term.width, GD.term.height)
    Logger.log(f"Drawing image at {abs_pos.left}, {abs_pos.top}")
    for row in range(len(final_chars)):
        # dont draw if out of bounds
        if not 0 <= abs_pos.top+row < GD.term.height: continue
        if not abs_pos.left < GD.term.width or abs_pos.left+len(final_chars[row]) < 0: continue
        print(GD.term.move_xy(abs_pos.left, abs_pos.top+row) + ''.join(final_chars[row]) + '\x1b[0m')

# demo i guess
# draw("demo.png", topleft_pos=(0, 0), maxsize=(200, 100), overflow_behavior="crop")