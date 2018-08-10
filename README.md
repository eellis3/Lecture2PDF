## ABSTRACT
Video summarization is an active field of study with uses in reducing video file sizes. This was applied to lecture videos
to enhance studying on a mobile device without needing to stream video. Different frame extraction techniques need to be
used on different types of video (e.g. news, sports, action movies, surveillance, or lectures). This paper explores largest
contour removal and analyzing text on a lecture video. A program was developed and deployed to be able to run on any
lecture video.

Read more on Project_Paper.pdf

To run program:  "python main.py", but meet all the requirements below.  

System Requirements Windows:  
pip install ffmpy  
pip install Pillow  
pip install reportlab  
pip install PyPDF2  

Countour  
http://www.lfd.uci.edu/~gohlke/pythonlibs/  
pip install "numpy-1.11.3+mkl-cp27-cp27m-win32.whl"  
pip install scipy-0.19.1-cp27-cp27m-win32.whl  
pip install  scikit_image-0.13.0-cp27-cp27m-win32.whl  

OCR  
https://github.com/tesseract-ocr/tesseract/wiki  
pip install pytesseract  

Folder Name and File Name Requirements:  
create 2 folders called "videos" and "subtitles" in the same directory as the program
each video and subtitle file needs to be in the format "NUMBER - LECTURE_NAME".  It compares the NUMBER and strips off any leading zeros to find a match.  The LECTURE_NAME does not have to be the exact same.  Most all lectures we have viewed are in this format.  

Main site  
https://omscs-pdf.github.io/OMSCS-PDF/Courses.html

Google Drive for Program and PDFs  
https://drive.google.com/drive/folders/0BwkwXPT21YHwaTAwYmEyTjBKOU0
