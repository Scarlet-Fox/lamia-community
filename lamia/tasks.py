from wand.image import Image
from lamia import app
import os
celery = app.celery

@celery.task()
def verify_attachment(filepath, size):
    filepath = os.path.join(os.getcwd(), "woe/static/uploads", filepath)
    sizepath = os.path.join(os.getcwd(), "woe/static/uploads", 
        ".".join(filepath.split(".")[:-1])+".custom_size."+size+"."+filepath.split(".")[-1])
    
    if not os.path.exists(sizepath):
        image = Image(filename=filepath)
        xsize = image.width
        ysize = image.height
        resize_measure = min(float(size)/float(xsize),float(size)/float(ysize))
        image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))
        image.save(filename=sizepath)
        
    return True