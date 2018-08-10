from ffmpy import *
import os
import pysrt
from datetime import datetime, timedelta
import shutil
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch,mm
from comparePictures import comparePictures
from PyPDF2 import PdfFileMerger

## This function will produce one final PDF from all PDFs generated, i.e, 1 PDF for 1 lesson.
def finalpdf(pdfs):
    merger = PdfFileMerger()
    for pdf in pdfs:
        merger.append(open(pdf, 'rb'))
        os.remove(pdf)
    with open('Lesson-Final.pdf', 'wb') as fout:
        merger.write(fout)
        #sdoc = 'Lesson-Final.pdf'
        #sdoc.build('Lesson-Final.pdf',onFirstPage=addPageNumber, onLaterPages=addPageNumber)



### This groups text by timestamps of frames
def groupSubtitlesByTime(subfile, timestamps):
    subs = pysrt.open(subfile)
    timestamps.append(float("inf"))
    # always want to get first subtitle for first picture
    compareSeconds = -1
    #  paragraphs holds the sentences for each frame
    paragraphs = []
    for i in range(1,len(timestamps)):
        combining = ''
        #  add subtitles until the frame seconds > end subtitle seconds
        while timestamps[i] > compareSeconds:
            if not subs:
                break
            combining += subs[0].text.replace('\n', ' ') + ' '
            y = datetime.strptime(str(subs[0].end), '%H:%M:%S,%f')
            compareSeconds = timedelta(hours=y.hour, minutes=y.minute, seconds=y.second,
                                   microseconds=y.microsecond).total_seconds()
            # remove sub since this is an ordered list
            del subs[0]
        # if the last frame is captured, but more subtitles exist, append to the last frame.
        if i == len(timestamps)-1 and timestamps[i] <= compareSeconds:
            for j in range(0,len(subs)):
                combining += subs[j].text.replace('\n', ' ') + ' '
        paragraphs.append(combining)
    return paragraphs

## i frames extraction.  Creates images and returns list of timestamps for frames.
def getI_Frames(vidfile):
    if not os.path.exists('temp'):
        os.makedirs('temp')
    path = os.path.abspath('temp/thumbnails-%02d.jpeg')
    imageList = []
    timestamps = []

    ff = FFmpeg(
        global_options={'-loglevel', '48'},
        inputs={vidfile: None},
        outputs={path: ['-vf', "select='eq(pict_type\,PICT_TYPE_I)'", '-vsync', '2', '-s', '1280x960', '-f', 'image2']}
    )
    stdout, stderr = ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ### gets timestamps of frames.
    logfile = stderr.split('\n')
    for i in range(0,len(logfile)):
        flag = False
        if logfile[i].find('pict_type:I') != -1:
            for y in logfile[i].split():
                if y[0] == 't' and y[1] == ':':
                    timestamps.append(float(y.strip('t:')))
                    flag = True
                    break
            ## didn't find time on line, check previous line, sometimes long lines get split in 2.
            if not flag:
                for y in logfile[i-1].split():
                    if y[0] == 't' and y[1] == ':':
                        timestamps.append(float(y.strip('t:')))
                        break
    ## get imagelist of names
    for filename in os.listdir(os.path.abspath('temp')):
        imageList.append(os.path.join('temp',filename))
    return timestamps, imageList

def addPageNumber(canvas, doc):
    """
    Add the page number
    """
    page_num = canvas.getPageNumber()
    text = "Page #%s" % page_num
    canvas.drawRightString(200*mm, 20*mm, text)

def print2PDF(filename,imageList,srtList):
    #c = canvas.Canvas(filename.replace(".mp4", "") +".pdf", pagesize=letter)
    doc = SimpleDocTemplate(filename.replace(".mp4", "") +".pdf",pagesize=letter,
                        rightMargin=72,leftMargin=72,
                        topMargin=72,bottomMargin=18)
    Story=[]
    styles=getSampleStyleSheet()
    Story.append(Paragraph(filename.replace(".mp4", ""), styles['Heading1']))
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    for i in range(len(imageList)):
        Story.append(Image(imageList[i], 3*inch, 2*inch))
        Story.append(Spacer(2, 12))
        ptext = '<font size=12>%s</font>' % srtList[i].strip()
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(2, 12))
        #Story.append(PageBreak())

    #doc.build(Story,onFirstPage=addPageNumber, onLaterPages=addPageNumber)
    doc.build(Story)

def deleteTempFiles():
    for filename in os.listdir(os.path.abspath('temp')):
        os.unlink(os.path.join('temp',filename))
    shutil.rmtree('temp')

def get_Newtimestamps(timestamps, imageList, newList):
    '''
    ###Get us the timestamps of thew modified Image list (selected frames)
    '''
    Newtimestamps = []
    for i in range(len(newList)):
        Newtimestamps.append(timestamps[imageList.index(newList[i])])
    return Newtimestamps

class fileError(RuntimeError):
    def __init__(self, arg):
        self.arg = arg

### this sorts by leading number.  all files should be format "04 - Exercise Constructing Semantic Nets I"
def sortFileNames(folder):
    filenameList = []
    returnList = []
    for filename in os.listdir(os.path.abspath(folder)):
        splitFilename = filename.split('-')
        filenameList.append((int(splitFilename[0].strip().lstrip('0')), filename))
    sortedList = sorted(filenameList, key=lambda number: number[0])
    for x in sortedList:
        returnList.append(x[1])
    return returnList

def run_folders():
    pdflist = []
    videoFolder = 'videos'
    subtitleFolder = 'subtitles'
    try:
        ### check for errors in files
        if not os.path.isdir('./' + videoFolder):
            raise fileError("'videos' folder does not exist in current directory")
        if not os.path.isdir('./' + subtitleFolder):
            raise fileError("'subtitles' folder does not exist in current directory")
        if len(os.listdir(os.path.abspath(videoFolder))) != len(os.listdir(os.path.abspath(subtitleFolder))):
            raise fileError("Number of videos do not match number of subtitles in your folder")

        ### run the pdf maker on each video in folder
        videoFileNameSorted = sortFileNames(videoFolder)
        subFileNameSorted = sortFileNames(subtitleFolder)
        for vidFileName in videoFileNameSorted:
            ### check to make sure files are .mp4 and .srt
            if not vidFileName.lower().endswith('.mp4'):
                raise fileError("Video file is not .mp4")
            print 'Generating PDF for Video: %s  ' % vidFileName
            ### find matching subtitle file
            savedSubFile = subFileNameSorted.pop(0)
            if not savedSubFile.lower().endswith('.srt'):
                raise fileError("Subtitle File is not .srt")
            if savedSubFile == '':
                print "no matching subtitle.  Skipping this video"
                continue

            print 'Using Subtitle: %s  ' % savedSubFile
            print ''

            ### run PDF maker on video and subtitle files
            videoPath = os.path.join(videoFolder,vidFileName)
            subtitlePath = os.path.join(subtitleFolder,savedSubFile)
            print 'Analyzing Video'
            timestamps, imageList = getI_Frames(videoPath)
            comparePics = comparePictures(imageList)
            reducedImageList = comparePics.comparePictures()
            reducedTimestamps = get_Newtimestamps(timestamps, imageList, reducedImageList)
            paragraphs = groupSubtitlesByTime(subtitlePath, reducedTimestamps)
            vidFileName = vidFileName.decode('utf-8', 'ignore')
            print2PDF(vidFileName, reducedImageList, paragraphs)
            pdflist.append(vidFileName.replace(".mp4", "") +".pdf")
            deleteTempFiles()
            print 'Completed'
            print ''

    except fileError, e:
        print e.arg
    else:
        finalpdf(pdflist)

run_folders()


