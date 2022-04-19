# Hello World Example
#
# Welcome to the OpenMV IDE! Click on the green run arrow button below to run the script!

#https://tannerhelland.com/2013/02/11/simple-algorithm-correcting-lens-distortion.html

import sensor, image, time, math, gc

sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.GRAYSCALE) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.
clock = time.clock()                # Create a clock object to track the FPS.

imgClone = sensor.alloc_extra_fb(320, 240, sensor.GRAYSCALE)

def correctLensDistort(img, str, zoom):
    global count

    width = img.width()
    height = img.height()
    halfWidth = width/2
    halfHeight = height/2

    global imgClone

    if str == 0: str = 0.00001

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

            imgClone.set_pixel(x, y, img.get_pixel(int(sourceX), int(sourceY)))
    sensor.flush()

count = 0

while(True):
    clock.tick()                    # Update the FPS clock.
    img = sensor.snapshot()         # Take a picture and return the image.
    correctLensDistort(img, 1.25, 1)

    for x in range(0, 320):
        for y in range(0, 240):
            img.set_pixel(x, y, imgClone.get_pixel(x, y))

    count += 1
    #print(clock.fps())              # Note: OpenMV Cam runs about half as fast when connected
                                    # to the IDE. The FPS should increase once disconnected.
