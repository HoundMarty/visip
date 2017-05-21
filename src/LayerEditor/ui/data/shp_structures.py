import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import shapefile
import struct
import os

class ShpLine():
    """
    Line from shape file 
    """   
    def __init__(self, p1, p2, highlighted=False):
        self.p1 = p1
        """First point"""
        self.p2 = p2
        """Second point"""
        self.highlighted = highlighted
        """Object is highlighted"""
 
 
class ShpPoint():
    """
    Point from shape file 
    """
    def __init__(self, p, highlighted=False):
        self.p = p
        """Point"""
        self.highlighted = highlighted
        """Object is highlighted"""    


class ShpData():
    """
    Shape file geometric data. 
    
    (Only geometric that will be displayed)
    """
    def __init__(self):
        self.lines = []
        """List of displayed lines in ShpLine data type"""
        self.points = []
        """List of displayed points in ShpPoint data type"""
        self.object = None
        """Graphic object"""
        self.min = None
        """left top corner in QPoint coordinates"""
        self.max = None
        """right bottom corner in QPoint coordinates"""
        
    def clear(self):
        """Remove all lines, points ant reset border"""
        self.lines = []
        self.points = []
        self.min = None
        self.max = None

class ShpDisp():
    """
    Shape file displayed settings.
    """
    BACKGROUND_COLORS = [
    
            QtGui.QColor("#e2caff"), #blue1
            QtGui.QColor("#bbffc0"), #green1
            QtGui.QColor("#fffaae"), #yelow1
            QtGui.QColor("#ffd3d0"), #red1            
            QtGui.QColor("#c8c8c8"), #gray
            QtGui.QColor("#c1cfff"), #blue2
            QtGui.QColor("#ffcde6"), #pink1
            QtGui.QColor("#c1ffda"), #green2
            QtGui.QColor("#ffd0b8"), #red2
            QtGui.QColor("#ffff7f"), #yelow2
            QtGui.QColor("#ffd2f6"), #pink2
            QtGui.QColor("#cfebff"), #blue3
            QtGui.QColor("#e3ffb5"), #green3
            QtGui.QColor("#ffd7dd"), #red3
            QtGui.QColor("#f3ffb3"), #yelow3
            QtGui.QColor("#8effff") #blue4
        ]
        
    _last_color = -1
    
    
    def __init__(self, file):
        self.file = file
        """paths to shp file"""
        self.color = self.next_color()
        """displaing color fir shapes"""
        self.attrs = []
        """File attributes"""
        self.attr = None
        """Selected attribute"""
        self.av_names = []
        """Values for selected attribute"""
        self.av_show = []
        """Show shape with this attribute"""
        self.av_highlight = []
        """Highlight shape with this attribute"""
        self.shpdata = ShpData()
        """Datat for drawing"""
        self._init_data(True)
        
    @classmethod
    def next_color(self):
        """File name without path"""
        self._last_color += 1
        if self._last_color>=len(self.BACKGROUND_COLORS):
            self._last_color = 0
        return self.BACKGROUND_COLORS[self._last_color]
        
    @property
    def file_name(self):
        """File name without path"""
        return os.path.basename( self.file)
    
    def refresh(self,  attr):
        """Refresh drawing data after settings changes"""
        self._init_data(False, attr)
        self.refreshed = False
        
    def _init_data(self, init_attr, load_attr=None):
        """Init end refresh data"""
        sf = shapefile.Reader(self.file)
        count_shapes = self._read_shp_count(sf)
        
        if init_attr:
            #init attributes
            self.attr = None
            for i in range(1, len(sf.fields)):
                field = sf.fields[i]
                self.attrs.append(field[0])
                if self.attr is None:
                    self.attr = i-1
        
        if load_attr is None or load_attr != self.attr:
            #reload values for attributes
            if load_attr is None:
                load_attr = self.attr
            #reset
            self.av_names = []
            self.av_show = []
            self.av_highlight = []
            # add shapes attributes            
            if self.attr is not None and  \
                (init_attr or load_attr!=self.attr):            
                for i in range(0, count_shapes):            
                    fields = sf.record(i)
                    if fields[load_attr] not in self.av_names:
                        if isinstance(fields[load_attr], str):
                            self.av_names.append(fields[load_attr])
                        else:
                            # TODO: better logic for bad type
                            if "???" not in self.av_names:
                                self.av_names.append("???")
                        self.av_show.append(True)
                        self.av_highlight.append(False)
                self.attr = load_attr     
        # process shapes
        self.shpdata.clear()
        for i in range(0, count_shapes):            
            fields = sf.record(i)
            if isinstance(fields[load_attr], str):
                idx = self.av_names.index(fields[self.attr])
            else:
                # TODO: better logic for bad type
                idx = self.av_names.index("???")
            highlighted = self.av_highlight[idx]
            shape = sf.shape(i)             
            if shape.shapeType==15 or shape.shapeType==5:
                # layer borders
                if self.shpdata.min is None:
                    self.shpdata.min = QtCore.QPointF(shape.bbox[0], shape.bbox[1])
                    self.shpdata.max = QtCore.QPointF(shape.bbox[2], shape.bbox[3])
                else:
                    if self.shpdata.min.x()>shape.bbox[0]:
                        self.shpdata.min.setX(shape.bbox[0])
                    if self.shpdata.min.y()>shape.bbox[1]:
                        self.shpdata.min.setY(shape.bbox[1])
                    if self.shpdata.max.x()<shape.bbox[2]:
                        self.shpdata.max.setX(shape.bbox[2])
                    if self.shpdata.max.y()<shape.bbox[3]:
                        self.shpdata.max.setY(shape.bbox[3])
                if not self.av_show[idx]:
                    continue
                part = 0
                point = None
                firstpoint = None
                # transform to point and lines
                for j in range(0, len(shape.points)):
                    lastPoint = point
                    point = QtCore.QPointF(shape.points[j][0],shape.points[j][1])
#                    self.shpdata.points.append(
#                            ShpPoint(point, highlighted)
#                        )
                    if shape.parts[part]==j:
                        if firstpoint is not None:
                            self.shpdata.lines.append(
                                    ShpLine(point, firstpoint, highlighted)
                                )
                        firstpoint=point
                        if len(shape.parts)>(part+1):
                            part +=1
                    else:
                        self.shpdata.lines.append(
                                ShpLine(lastPoint, point, highlighted)
                            )
                if firstpoint is not None:
                    self.shpdata.lines.append(
                            ShpLine(point, firstpoint, highlighted)
                        )
            else:
                raise Exception("Shape file type {0} is not implemented".format(str(shape.shapeType)))
        return True
    
    def _read_shp_count(self, sf):
        """
        read safetly shapes count
        
        if count of record in the dbf file is not match
        count of shapes in shp file, smaller number is
        returned
        """
        try:
            i=len(sf.shapes())
            return i
        except struct.error:
            i = 0
            while True:            
                try:
                    sf.record(i)
                    sf.shape(i)
                    i += 1
                except IndexError:
                    return i
        return 0
        
    def set_color(self, color):
        """change displayed color"""
        self.color = color
        self.refreshed = False
        
    def set_attr(self, attr):
        """change dislayed attribute"""
        self.refresh(attr)
        self.refreshed = False        
       
    def set_show(self, i, value):
        """change dislayed attribute value"""
        self.av_show[i] = value
        self.refresh(self.attr)
        self.refreshed = False
        
    def set_highlight(self, i, value):
        """change highlighted attribute value"""
        self.av_highlight[i] = value
        self.refresh(self.attr)
        self.refreshed = False
        

class ShpFiles():
    """
    Shape files, that is displazed in background.
    """
    def __init__(self):
        self.datas = []
        """Data for shp files"""
        self.boundrect = None
        """shape file bounding rect in QRectF variable or None"""
    
    def _shp_rect(self):
        """compute shape file bounding rect"""
        rec = None
        for shp in self.datas:
            if rec is None:
                rec = QtCore.QRectF(shp.shpdata.min, shp.shpdata.max)
            else:
                rec = rec.united(QtCore.QRectF(shp.shpdata.min, shp.shpdata.max))                
        return rec
    
    def is_empty(self):
        """Is set some shapefile"""
        return len(self.datas)==0
        
    def is_file_open(self, file):
        """Is shapefile already opened"""
        for data in self.datas:
            if data.file == file:
                return True
        return False
        
    def add_file(self, file):
        """Add new shapefile"""
        disp = ShpDisp(file)         
        self.datas.append(disp) 
        self.boundrect = self._shp_rect()

    def del_file(self, idx):
        """Delete existing shapefile according to file index"""
        self.boundrect = self._shp_rect()
        
    def set_attr(self, idx):
        """Other attribute for idx file is selected and new data should be reloaded"""
        self.boundrect = self._shp_rect()
