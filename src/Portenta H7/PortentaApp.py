import sensor, image, time, os
import tf
import pyb
import math
import ulab

############################################################
################### GLOBAL VARIABLES #######################
############################################################

#A global variable that stores an image in the frame buffer.
#We use a global variable as there is no easy way to free memory
#From the frame buffer.
imgCorrected = sensor.alloc_extra_fb(320, 240, sensor.GRAYSCALE)
cellCountX = 15
cellCountY = 7
charWidth = 13
charHeight = 18
characterImages = []
gridModel = None
charModel = None

RED_LED_PIN = 1
BLUE_LED_PIN = 3
GREEN_LED_PIN = 2

character_classes = {
    0: "a",
    1: "b",
    2: "c",
    3: "d",
    4: "e",
    5: "f",
    6: "g",
    7: "h",
    8: "i",
    9: "j",
    10: "k",
    11: "l",
    12: "m",
    13: "n",
    14: "o",
    15: "p",
    16: "q",
    17: "r",
    18: "s",
    19: "t",
    20: "u",
    21: "v",
    22: "w",
    23: "x",
    24: "y",
    25: "z",
    26: "A",
    27: "B",
    28: "C",
    29: "D",
    30: "E",
    31: "F",
    32: "G",
    33: "H",
    34: "I",
    35: "J",
    36: "K",
    37: "L",
    38: "M",
    39: "N",
    40: "O",
    41: "P",
    42: "Q",
    43: "R",
    44: "S",
    45: "T",
    46: "U",
    47: "V",
    48: "W",
    49: "X",
    50: "Y",
    51: "Z",
    52: "1",
    53: "2",
    54: "3",
    55: "4",
    56: "5",
    57: "6",
    58: "7",
    59: "8",
    60: "9",
    61: "0",
    62: "!",
    63: "@",
    64: "#",
    65: "$",
    66: "%",
    67: "^",
    68: "&",
    69: "*",
    70: "(",
    71: ")",
    72: "-",
    73: "_",
    74: "+",
    75: "=",
    76: "{",
    77: "}",
    78: "[",
    79: "]",
    80: "|",
    81: "\\",
    82: ":",
    83: ";",
    84: "\"",
    85: "'",
    86: "<",
    87: ">",
    88: ",",
    89: ".",
    90: "/",
    91: "?",
    92: "~",
    93: "`",
    94: " "
}

############################################################
################### HELPER FUNCTIONS #######################
############################################################

################### SETUP ##################################

def InitCharacterImages():
    global characterImages
    global cellCountY
    global cellCountX
    characterImages = [2 for i in range(cellCountX * cellCountY)]

    for y in range(0, cellCountY):
        for x in range(0, cellCountX):
            characterImages[y * cellCountX + x] = sensor.alloc_extra_fb(charWidth, charHeight,sensor.GRAYSCALE)
            time.sleep(0.01)

############################################################

################### VECTOR MATH ############################

# Subtract v2 from v1
def sub(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1])

# Distance between two vectors
def distance(v1, v2):
    return math.sqrt((v2[0] - v1[0]) * (v2[0] - v1[0]) + (v2[1] - v1[1]) * (v2[1] - v1[1]))

#Normalizes a vector
def vectorNormalize(v):
    length = math.sqrt(v[0] * v[0] + v[1] * v[1])
    return (v[0]/length, v[1]/length)

#Generates a range of positions along a line traversed by an input vector
def vectorRange(xy, v, count, dist):
    vals = []
    intv = int(dist/count + 0.5)

    if intv < 1:
        intv = 1

    for i in range(0, dist, intv):

        if len(vals) == count:
            break

        vals.append((xy[0] + v[0]*i, xy[1] + v[1]*i))

    while not len(vals) == count:
        vals.append(vals[-1])

    return vals

############################################################

################### IMAGE SLICING ##########################

#Calculates the corners of all cells within a grid
def CalculateCellBounds(x1, y1, x2, y2, x3, y3, x4, y4):

    global cellCountX
    global cellCountY

    #Create Vectors
    v3 = vectorNormalize((x3-x1, y3-y1)) # Vector from top left to bottom left
    v4 = vectorNormalize((x4-x2, y4-y2)) # Vector from top right to bottom right

    #Create Position Sets
    v3set = vectorRange((x1, y1), v3, cellCountY + 1, int(y3-y1+(y3-y1)/cellCountY)) #Set of positions from top left to bottom left
    v4set = vectorRange((x2, y2), v4, cellCountY + 1, int(y4-y2+(y4-y2)/cellCountY)) #Set of positions from top right to bottom right

    cells = []
    for y in range(0, cellCountY):
        row = []

        v1 = vectorNormalize(sub(v4set[y], v3set[y]))
        v2 = vectorNormalize(sub(v4set[y+1], v3set[y+1]))

        d1 = distance(v3set[y], v4set[y])
        d2 = distance(v3set[y+1], v4set[y+1])

        v1set = vectorRange(v3set[y], v1, cellCountX + 1, int(d1 + d1/cellCountX))
        v2set = vectorRange(v3set[y + 1], v2, cellCountX + 1, int(d2 + d2/cellCountX))

        for x in range(0, cellCountX):
            row.append([v1set[x],v1set[x+1],v2set[x],v2set[x+1]])

        cells.append(row)

    return cells

#Samples the image within a cell
def SampleCell(rawimage, cimg, cell):
    global charWidth
    global charHeight

    x1, y1 = cell[0][0], cell[0][1] # Top Left Corner
    x2, y2 = cell[1][0], cell[1][1] # Top Right Corner
    x3, y3 = cell[2][0], cell[2][1] # Bottom Left Corner
    x4, y4 = cell[3][0], cell[3][1] # Bottom Right Corner

    #Create Vectors
    v3 = vectorNormalize((x3-x1, y3-y1)) # Vector from top left to bottom left
    v4 = vectorNormalize((x4-x2, y4-y2)) # Vector from top right to bottom right

    #Create Position Sets
    v3set = vectorRange((x1, y1), v3, charHeight + 1, int(y3-y1+(y3-y1)/charHeight)) #Set of positions from top left to bottom left
    v4set = vectorRange((x2, y2), v4, charHeight + 1, int(y4-y2+(y4-y2)/charHeight)) #Set of positions from top right to bottom right

    for y in range(0, min(len(v3set), charHeight)):
        v1 = vectorNormalize(sub(v4set[y], v3set[y]))

        d1 = distance(v3set[y], v4set[y])

        v1set = vectorRange(v3set[y], v1, charWidth + 1, int(d1 + d1/charWidth))

        for x in range(0, min(len(v1set),charWidth)):
            cimg.set_pixel(x, y, rawimage.get_pixel(int(v1set[x][0]),int(v1set[x][1])))

    return cimg

#Cuts a grid image into cell images
def CutCellImages(img, cells):
    global characterImages
    for x in range(0, len(cells)):
        for y in range(0, len(cells[x])):
            corners = cells[x][y]
            SampleCell(img, characterImages[x * cellCountY + y], corners)

    return characterImages


############################################################

#Do the classification and get the object returned by the inference.
def PredictChar(img):
    global charModel
   
    TF_objs = tf.classify('Character_Recognition_Model.tflite', img)

    cl = ulab.numpy.argmax(TF_objs[0].output())
    return character_classes[cl]


############################################################
################### CORE FUNCTIONS #########################
############################################################
def TakePicture():

    global GREEN_LED_PIN
    global RED_LED_PIN
    global BLUE_LED_PIN

    sensor.reset() # Initialize the camera sensor.
    sensor.set_pixformat(sensor.GRAYSCALE) # or sensor.GRAYSCALE
    sensor.set_framesize(sensor.QVGA) # or sensor.QQVGA (or others)
    sensor.skip_frames(time = 2000) # Let new settings take affect.

    pyb.LED(RED_LED_PIN).on()
    sensor.skip_frames(time = 2000) # Give the user time to get ready.

    pyb.LED(RED_LED_PIN).off()
    pyb.LED(BLUE_LED_PIN).on()

    img = sensor.snapshot()

    pyb.LED(BLUE_LED_PIN).off()

    return img

#Performs lens distortion correction on the img
#Returns the corrected image
def CorrectLensDistortion(img):
    global imgCorrected

    width = img.width()
    height = img.height()
    halfWidth = width/2
    halfHeight = height/2

    str = 1.125
    zoom = 1

    correctionRadius = math.sqrt(width * width + height * height) / str

    for x in range(0, width):
        for y in range(0, height):
            newX = x - halfWidth
            newY = y - halfHeight

            distance = math.sqrt(newX * newX + newY * newY)
            r = distance / correctionRadius

            theta = 1
            if r == 0:
                theta = 1
            else:
                theta = math.atan(r) / r

            sourceX = halfWidth + theta * newX * zoom
            sourceY = halfHeight + theta * newY * zoom

            imgCorrected.set_pixel(x, y, img.get_pixel(int(sourceX), int(sourceY)))
    return imgCorrected

#Pass the image into the grid prediction model
#Return the results of the grid prediction model
def PredictGrid(img):
    global gridModel

    TF_objs = tf.classify('Grid_Recognition_Model.tflite', img)

    return round(TF_objs[0].output()[0]),round(TF_objs[0].output()[1]),round(TF_objs[0].output()[2]),round(TF_objs[0].output()[3]),round(TF_objs[0].output()[4]),round(TF_objs[0].output()[5]),round(TF_objs[0].output()[6]),round(TF_objs[0].output()[7]),round(TF_objs[0].output()[8])

#Slice the image up into many sub images using the image slicing techniques
#Created for the training data preprocessor
#Return an array of images in order from top left to bottom right
def SliceImage(img, x1, y1, x2, y2, x3, y3, x4, y4):
    global GREEN_LED_PIN
    global RED_LED_PIN
    global BLUE_LED_PIN

    pyb.LED(RED_LED_PIN).on()
    pyb.LED(GREEN_LED_PIN).on()
    cells = CalculateCellBounds(x1, y1, x2, y2, x3, y3, x4, y4)
    pyb.LED(RED_LED_PIN).off()
    pyb.LED(GREEN_LED_PIN).off()

    time.sleep(0.2)

    pyb.LED(RED_LED_PIN).on()
    pyb.LED(GREEN_LED_PIN).on()

    chars = CutCellImages(img, cells)

    pyb.LED(RED_LED_PIN).off()
    pyb.LED(GREEN_LED_PIN).off()

    return chars

#Iterate through each character image, running them through the character
#recognition model. Appends each returned character to a string
#returns the string
def DetectChars(chars):
    finalStr = ""

    for c in chars:
        pyb.LED(GREEN_LED_PIN).on()
        ch = PredictChar(c)
        pyb.LED(GREEN_LED_PIN).off()
        time.sleep(0.05)
        finalStr += ch

    return finalStr

#Send the parsed text to the client on the computer.
#Printing the text sends it over the serial port
def SendTextToClient(text):
    print(text)

#Blink the led red if an error occurs
def BlinkError():
    global GREEN_LED_PIN
    global RED_LED_PIN
    global BLUE_LED_PIN

    pyb.LED(GREEN_LED_PIN).off()
    pyb.LED(RED_LED_PIN).off()
    pyb.LED(BLUE_LED_PIN).off()

    pyb.LED(RED_LED_PIN).on()
    time.sleep(0.2)
    pyb.LED(RED_LED_PIN).off()
    time.sleep(0.2)
    pyb.LED(RED_LED_PIN).on()
    time.sleep(0.2)
    pyb.LED(RED_LED_PIN).off()
    time.sleep(0.2)
    pyb.LED(RED_LED_PIN).on()
    time.sleep(0.2)
    pyb.LED(RED_LED_PIN).off()

############################################################
################### MAIN FUNCTIONS #########################
############################################################
def Setup():
    global charModel
    global gridModel
    InitCharacterImages()
    ##charModel = tf.load('/Character_Recognition_Model.tflite', load_to_fb=True)
    ##gridModel = tf.load('/Grid_Recognition_Model.tflite', load_to_fb=True)

def Loop():
    while True:
        img = TakePicture()
        img = CorrectLensDistortion(img)
        valid, x1, y1, x2, y2, x3, y3, x4, y4 = PredictGrid(img)

        #If our image is not valid (No corners found), goto next iteration
        if (valid != 1):
            BlinkError()
            continue

        try:
            chars = SliceImage(img, x1, y1, x2, y2, x3, y3, x4, y4)
            text = DetectChars(chars)
            SendTextToClient(text)
        except:
            BlinkError()

############################################################
################### EXECUTE ################################
############################################################

Setup()
Loop()
