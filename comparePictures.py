from PIL import Image as PILimage
from PIL import ImageChops as PILimageChops
from PIL import ImageFilter as PILimageFilter
from PIL import ImageStat as PILimageStat
import cv2
from skimage.measure import compare_ssim
import imutils
import numpy as np
from pytesseract import image_to_string
import sys
from time import sleep

class comparePictures:
    def __init__(self,imageList):
        self.imageList = imageList
        ### this is used to keep track of pictures to keep
        self.imageIndex = []
        ### to compare how similar images are
        self.threshold = 0.85
        self.maxContours = 1

    ### use this as the compare call in main
    def comparePictures(self):
        modimList=[]
        ### always add the first image
        modimList.append(self.imageList[0])
        ### reduce number of times calling countLines by saving the image before
        countLinesBefore = self.countLines(cv2.imread(self.imageList[0]))
        lastSlideFlag = False
        sizeImageList = len(self.imageList) - 1
        ### prevent divide by 0
        if sizeImageList <= 2:
            percentDone = 1
        else:
            percentDone = sizeImageList - 1
        if sizeImageList <= 0:
            sys.stdout.write('\r')
            sys.stdout.write("100.00%")
            sys.stdout.flush()
        for i in range(sizeImageList):
            pic1 = cv2.imread(self.imageList[i])
            pic2 = cv2.imread(self.imageList[i + 1])
            im1, im2 = self.findContoursAndRemove(pic1, pic2)
            contourSim = self.tverskyRatio(im1, im2)
            countLines2 = self.countLines(pic2)
            if contourSim < self.threshold or countLinesBefore != countLines2:
                modimList.append(self.imageList[i+1])
                if i == len(self.imageList) - 2:
                    lastSlideFlag = True
            countLinesBefore = countLines2
            sys.stdout.write('\r')
            if percentDone <= 1:
                sys.stdout.write("100.00%")
            else:
                sys.stdout.write("%.2f%%" % ((100./percentDone) * i))
            sys.stdout.flush()
        if not lastSlideFlag:
            modimList.append(self.imageList[-1])
        print ''
        return modimList


    ### provide 2 CV images.  finds largest conttour which should be the professor's hand and turns it white
    def findContoursAndRemove(self, im1, im2):
        gray1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
        (score, diff) = compare_ssim(gray1, gray2, full=True)
        diff = (diff * 255).astype("uint8")
        thresh = cv2.threshold(diff, 0, 255,
                               cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]
        ### find number of contours to overwrite, if 0 just return because nothing to delete.
        if len(cnts) == 0:
            return im1, im2
        ### if not a lot of contours, only delete the largest
        elif len(cnts) < 10:
            self.maxContours = 1
        ### get  largest contours
        cntsMax = sorted(cnts, key=cv2.contourArea, reverse=True)[:self.maxContours]
        ### print height, width, channels
        ### loop over the contours
        ### find biggest contour which should be hand
        height, width, channels = im1.shape
        for c in range(len(cntsMax)):
            ### if contour is > 85% of the picture, dont delete it.
            if cv2.contourArea(cntsMax[c]) > height*width*0.80:
                continue
            minRect = cv2.minAreaRect(cntsMax[c])
            box = cv2.boxPoints(minRect)
            box = np.int0(box)
            ### DELETE BOX
            # cv2.drawContours(im1, [box], 0, (255, 255, 255), -1)
            # cv2.drawContours(im2, [box], 0, (255, 255, 255), -1)
            ### RED BOX
            #cv2.drawContours(im1, [box], 0, (0, 0, 255), 2)
            #cv2.drawContours(im2, [box], 0, (0, 0, 255), 2)
            #cv2.imshow('first',im1)
            #cv2.imshow('second', im2)
            #cv2.waitKey(0)

        ### convert to binary black and white for better comparisons
        im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        im1 = cv2.threshold(im1, 127, 255, cv2.THRESH_BINARY)[1]
        im2 = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
        im2 = cv2.threshold(im2, 127, 255, cv2.THRESH_BINARY)[1]
        return im1, im2

    ### provide 1 CV image and it will count the # of lines of text
    def countLines(self,im1):
        # convert to black and white and count lines.  Need to save pic in different temp folder.
        im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
        im1 = cv2.threshold(im1, 127, 255, cv2.THRESH_BINARY)[1]
        PILpic1 = PILimage.fromarray(im1)
        imageString = image_to_string(PILpic1)
        z = imageString.split('\n')
        lines = filter(None, (line.rstrip() for line in z))
        return len(lines)

    ### provide images in form of cv2
    def tverskyRatio(self, im1, im2):
        #cv2.imwrite('pic1.jpeg', im1)
        #cv2.imwrite('pic2.jpeg',im2)
        #PILpic1 = PILimage.open('pic1.jpeg')
        #PILpic2 = PILimage.open('pic2.jpeg')
        PILpic1 = PILimage.fromarray(im1)
        PILpic2 = PILimage.fromarray(im2)
        intersection = PILimageChops.lighter(PILpic1, PILpic2)
        union = PILimageChops.darker(PILpic1, PILpic2)
        # intersection.show()
        # union.show()
        # invert to make shapes white and do RMS on it
        intersection = PILimageChops.invert(intersection)
        union = PILimageChops.invert(union)

        # maxfilter creates a better match, evens out lines
        intersection = intersection.filter(PILimageFilter.MaxFilter(3))
        union = union.filter(PILimageFilter.MaxFilter(3))
        # intersection.show()
        # union.show()
        intersectionStats = PILimageStat.Stat(intersection)
        unionStats = PILimageStat.Stat(union)
        intersectionCount = intersectionStats._getrms()
        unionCount = unionStats._getrms()

        # print intersectionCount
        # print unionCount
        if unionCount[0] == 0:
            ratio = 0
        else:
            ratio = float(intersectionCount[0] / unionCount[0])
        return ratio


