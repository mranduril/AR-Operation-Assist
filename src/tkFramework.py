import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd, colorchooser, ttk
from tkinter.messagebox import showinfo
from tkinter.simpledialog import askstring
from PIL import Image, ImageTk
import pandas as pd
import io
import os
import math
import cv2
import numpy as np
import dbConnect

def open_eps(ps, dpi=300.0):
    img = Image.open(io.BytesIO(ps.encode('utf-8')))
    original = [float(d) for d in img.size]
    scale = dpi/72.0            
    if dpi != 0:
        img.load(scale = math.ceil(scale))
    if scale != 1:
        img.thumbnail([round(scale * d) for d in original], Image.LANCZOS)
    return img

# TODO: make creating shape a new page (essentially a new Class)
class windows(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # Adding a title to the window
        self.wm_title("Test Application")
        self.geometry("1920x1080")

        # creating a frame and assigning it to container
        container = tk.Frame(self, height=1920, width=1080)
        # specifying the region where the frame is packed in root
        container.pack(side="top", fill="both", expand=True)

        # configuring the location of the container using grid
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # We will now create a dictionary of frames
        self.frames = {}

        self.idToImage = {}
        self.idToPhotoImage = {}
        self.idToTag = {}
        self.notMovableID = set()
        
        self.tagToPhotoImage = {}
        self.tagToImage = {}
        self.tagToID = {}
        self.tagToFileDir = {}
        
        # self.idToShape
        
        self.canvasSize = (0, 0)
        # we'll create the frames themselves later but let's add the components to the dictionary.
        for F in (DrawPage, CanvasConfigPage, CompletionScreen, NewShapePage):
            frame = F(container, self)

            # the windows class acts as the root window for the frames.
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Using a method to switch frames
        self.show_frame(CanvasConfigPage)
        
    def show_frame(self, cont):
        frame = self.frames[cont]
        if (cont is DrawPage):
            frame.reconfig_size()
        # raises the current frame to the top
        frame.tkraise()
        
class DrawPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        label = tk.Label(self, text="Draw Page")
        label.pack(padx=10, pady=10)
        self.controller = controller
        self.scene = Canvas(self, width=self.controller.canvasSize[0], height=self.controller.canvasSize[1], bg="white", highlightthickness=1, highlightbackground="black")
        self.scene.pack()
        
        self.currImgConfigInfo = tk.Label(self, text="")
        self.currImgConfigInfo.pack()
        
        self.scene.bind("<Button-1>", self.startMovement)
        self.scene.bind("<Button-3>", self.deleteImage)
        self.scene.bind("<ButtonRelease-1>", self.stopMovement)
        self.scene.bind("<Motion>", self.movement)
        self.scene.bind("<MouseWheel>", self.resize)
        
        self.cursorX = 0
        self.cursorY = 0
        
        self.move = False
        
        self.inputtext = Text(self, height=3, width=100)
        self.inputtext.pack()
        inputLabel = Label(self, text="input image tag above")
        inputLabel.pack()
        
        load_file_button = tk.Button(
            self,
            text="Load File",
            command=self.load_file,
        )
        
        prev_button = tk.Button(
            self,
            text="Reconfig canvas size",
            command=self.back_to_CanvasConfig,
        )

        switch_window_button = tk.Button(
            self,
            text="Next Window",
            command=lambda: controller.show_frame(CompletionScreen),
        )
        
        save_scene_button = tk.Button(
            self,
            text="Save Current Canvas scene",
            command=self.save_canvas,
        )
        
        draw_shape_button = tk.Button(
            self,
            text="Create New Shape",
            command=self.switch_NewShapePage,
        )
        
        switch_window_button.pack(side="bottom", fill=tk.X)
        load_file_button.pack()
        draw_shape_button.pack()
        prev_button.pack()
        save_scene_button.pack()
    

    def update_currInfo(self, event, reset=False):
        if reset:
            self.currImgConfigInfo.config(text="")
            return
        target = self.scene.find_closest(self.scene.canvasx(event.x), self.scene.canvasx(event.y), halo=5)
        print(target)
        if target == ():
            return
        self.currImgConfigInfo.config(text=
                              "Current Image/Shape Tag: {} | Current Image/Shape Center Coordinates (x, y): {} | Current Image Size: {}"
                              .format(self.controller.idToTag[target[0]],
                                        self.scene.coords(target[0]),
                                        [(self.scene.bbox(target[0])[2] - self.scene.bbox(target[0])[0]), 
                                        (self.scene.bbox(target[0])[3] - self.scene.bbox(target[0])[1])]))
        
    def load_file(self):
        tag = self.inputtext.get(1.0, "end")
        file_path = fd.askopenfilename()
        if (len(tag) == 1):
            showinfo(message="missing tag")
            return
        if file_path == '':
            showinfo(message="file not selected")
            return
        tag = tag[:-1]
        if tag in self.controller.tagToFileDir or tag in self.controller.tagToID:
            showinfo(message="Tag already exists")
            return
        self.controller.tagToFileDir[tag] = file_path
        showinfo(message="success")
        self.inputtext.delete(1.0, "end")
        self.presentImage(tag)
        
    def reconfig_size(self):
        self.scene.config(width=self.controller.canvasSize[0], height=self.controller.canvasSize[1])
        
    def presentImage(self, tag):
        print(self.controller.tagToFileDir[tag])
        newImage = Image.open(self.controller.tagToFileDir[tag])
        newPhotoImage = ImageTk.PhotoImage(newImage)
        # newPhotoImage = ImageTk.PhotoImage(file=self.controller.tagToFileDir[tag])
        # newImage = newImage.zoom(0.5, 0.5)
        self.controller.tagToPhotoImage[tag] = newPhotoImage
        self.controller.tagToImage[tag] = newImage
        id = self.scene.create_image(250, 250, anchor=CENTER, image=newPhotoImage)
        self.controller.idToPhotoImage[id] = newPhotoImage
        self.controller.idToImage[id] = newImage
        self.controller.idToTag[id] = tag
        self.controller.tagToID[tag] = id
        # self.scene.itemconfig(id, image=newImage)
        print(id)
        
    def startMovement(self, event):
        self.initi_x = self.scene.canvasx(event.x) #Translate mouse x screen coordinate to canvas coordinate
        self.initi_y = self.scene.canvasy(event.y) #Translate mouse y screen coordinate to canvas coordinate
        print('startMovement init', self.initi_x, self.initi_y)
        self.movingimage = self.scene.find_closest(self.initi_x, self.initi_y, halo=5) # get canvas object ID of where mouse pointer is 
        if self.movingimage != () and self.movingimage[0] not in self.controller.notMovableID:
            self.move = True
        print(self.movingimage)
        print(self.scene.find_all()) # get all canvas objects ID
        self.update_currInfo(event) 

    def stopMovement(self, event):
        self.move = False

    def movement(self, event):
        self.cursorX = self.scene.canvasx(event.x)
        self.cursorY = self.scene.canvasy(event.y)
        if self.move:
            # end_x = self.scene.canvasx(event.x) #Translate mouse x screen coordinate to canvas coordinate
            # end_y = self.scene.canvasy(event.y) #Translate mouse y screen coordinate to canvas coordinate
            print('movement end', self.cursorX, self.cursorY)
            deltax = self.cursorX - self.initi_x #Find the difference
            deltay = self.cursorY - self.initi_y
            print('movement delta', deltax, deltay)
            self.initi_x = self.cursorX #Update previous current with new location
            self.initi_y = self.cursorY
            print('movement init', self.initi_x, self.initi_y)
            # print(c.itemcget(self.movingimage, "filepath"))
            self.scene.move(self.movingimage, deltax, deltay) # move object
            self.scene.tag_raise(self.movingimage)
            self.update_currInfo(event)
        
    def resize(self, event):
        #if not self.objOutOfBound():
        if True:
            movingimg = self.scene.find_closest(self.cursorX, self.cursorY, halo=5)
            x = self.scene.canvasx(event.x)
            y = self.scene.canvasy(event.y)
            print(movingimg)
            id = movingimg[0]
            img_w, img_h = self.controller.idToImage[id].size
            if (event.delta == -120):
                newImage = self.controller.idToImage[id].resize((img_w * 9 // 10 - 5, img_h * 9 // 10 - 5))
                # self.scene.scale(movingimg, x, y, 0.9, 0.9)
            elif (event.delta == 120):
                newImage = self.controller.idToImage[id].resize((img_w * 11 // 10 + 5, img_h * 11 // 10 + 5))
                # self.scene.scale(movingimg, x, y, 1.1, 1.1)
            newPhotoImage = ImageTk.PhotoImage(newImage)
            self.scene.itemconfig(id, image=newPhotoImage)
            self.controller.idToImage[id] = newImage
            self.controller.idToPhotoImage[id] = newPhotoImage
            self.update_currInfo(event)

    def deleteImage(self, event):
        movingimg = self.scene.find_closest(self.cursorX, self.cursorY, halo=5)
        id = movingimg[0]
        self.scene.delete(id)
        del self.controller.idToImage[id]
        del self.controller.idToPhotoImage[id]
        tag = self.controller.idToTag[id]
        del self.controller.idToTag[id]

        del self.controller.tagToPhotoImage[tag]
        del self.controller.tagToImage[tag]
        del self.controller.tagToID[tag]
        del self.controller.tagToFileDir[tag]
        self.update_currInfo(event, reset=True)
    
    def objOutOfBound(self):
        if (self.scene.bbox(self.movingimage)[0] < 0
            or self.scene.bbox(self.movingimage)[1] < 0
            or self.scene.bbox(self.movingimage)[2] > self.controller.canvasSize[0]
            or self.scene.bbox(self.movingimage)[3] > self.controller.canvasSize[1]):
            return True
        return False
        
    def back_to_CanvasConfig(self):
        self.controller.idToImage = {}
        self.controller.idToPhotoImage = {}
        self.controller.idToTag = {}
        self.controller.tagToPhotoImage = {}
        self.controller.tagToImage = {}
        self.controller.tagToID = {}
        self.controller.tagToFileDir = {}
        self.controller.canvasSize = (0, 0)
        self.scene.delete("all")
        self.controller.show_frame(CanvasConfigPage)
    
    def switch_NewShapePage(self):
        self.controller.show_frame(NewShapePage)
    
    def save_canvas(self):
        if len(self.scene.find_all()) == 0:
            showinfo(message="Empty scene")
            return
        name = askstring('csvName', 'Name of output csv file')
        if name == "":
            showinfo(message="Invalid output file name")
            return
        result = {'Scene Width': self.controller.canvasSize[0],
                  'Scene Height': self.controller.canvasSize[1],
                  'Tag': [],
                  'x coord': [],
                  'y coord': [],
                  'width': [],
                  'height': [],
                  'File Location': []}
        for id in self.scene.find_all():
            tag = self.controller.idToTag[id]
            result['Tag'].append(tag)
            result['x coord'].append(self.scene.coords(id)[0])
            result['y coord'].append(self.scene.coords(id)[1])
            result['width'].append(self.scene.bbox(id)[2] - self.scene.bbox(id)[0])
            result['height'].append(self.scene.bbox(id)[3] - self.scene.bbox(id)[1])
            result['File Location'].append(self.controller.tagToFileDir[tag])
        df = pd.DataFrame(data=result)
        df.to_csv('../output/sheets/{}.csv'.format(name), index=False)
        showinfo(message="Successfully saved")

    def __str__(self):
        return "DrawPage"
        
class CanvasConfigPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="This is the Canvas Size Config Page")
        label.pack(padx=10, pady=10)
        
        self.inputWidth = Text(self, height=1, width=5)
        self.inputWidth.pack()
        
        labelWidth = Label(self, text="Type Canvas Width above")
        labelWidth.pack()
        
        self.inputHeight = Text(self, height=1, width=5)
        self.inputHeight.pack()
        
        labelHeight = Label(self, text="Type Canvas Height above")
        labelHeight.pack()
        
        confirm_button = tk.Button(
            self,
            text="Confirm Canvas Config",
            command=self.saveCanvasConfig
        )
        confirm_button.pack()
        
        switch_button = tk.Button(
            self,
            text="Start Drawing",
            command=self.switchToDrawPage
        )
        switch_button.pack()
        
        # switch_window_button = tk.Button(
        #     self,
        #     text="Go to the Draw Screen",
        #     command=lambda: controller.show_frame(DrawPage),
        # )
        # switch_window_button.pack(side="bottom", fill=tk.X)
        
    def switchToDrawPage(self):
        if (type(self.controller.canvasSize[0]) != int
                or type(self.controller.canvasSize[1]) != int 
                or self.controller.canvasSize[0] == 0 
                or self.controller.canvasSize[1] == 0):
            showinfo(message="Invalid Canvas Size")
            return
        self.controller.show_frame(DrawPage)
        
    def saveCanvasConfig(self):
        canvasWidth = self.inputWidth.get(1.0, "end")[:-1]
        canvasHeight = self.inputHeight.get(1.0, "end")[:-1]
        if (not canvasHeight.isdigit() or not canvasWidth.isdigit()):
            showinfo(message="Invalid Input")
            return
        canvasWidth = int(canvasWidth)
        canvasHeight = int(canvasHeight)
        if (canvasHeight == 0 or canvasWidth == 0):
            showinfo(message="Invalid Canvas Size")
            return
        self.controller.canvasSize = (canvasWidth, canvasHeight)
        showinfo(message="canvas width: {} | canvas height: {}".format(self.controller.canvasSize[0], self.controller.canvasSize[1]))
    
    def __str__(self):
        return "CanvasConfigPage"

class CompletionScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Completion Screen, we did it!")
        label.pack(padx=10, pady=10)
        switch_window_button = ttk.Button(
            self, text="Return to menu", command=lambda: controller.show_frame(CanvasConfigPage)
        )
        switch_window_button.pack(side="bottom", fill=tk.X)
        
    def __str__(self):
        return "CompletionScreen"    

class NewShapePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Create New Item Page")
        label.pack(padx=10, pady=10)
        self.controller = controller
        self.scene = Canvas(self, width=self.controller.canvasSize[0], height=self.controller.canvasSize[1], bg="white", highlightthickness=1, highlightbackground="black")
        self.scene.pack()
        
        self.itemWidth = 0.0
        self.itemHeight = 0.0
        
        scene_config_button = tk.Button(
            self,
            text="Config Item Size",
            command=self.config_item_size,
        )
        
        create_item_button = tk.Button(
            self,
            text="Create New Item",
            command=self.create_new_shape,
        )
        
        save_item_button = tk.Button(
            self,
            text="Save Shape",
            command=self.save_shape,
        )
        scene_config_button.pack()
        create_item_button.pack()
        save_item_button.pack()
    
    def config_item_size(self):
        popup = Toplevel(self)
        popup.geometry("750x250")
        popup.title("Shape Config")
        popup.inputWidth = Text(popup, height=1, width=5)
        popup.inputWidth.pack()
        
        labelWidth = Label(popup, text="Type Item Width above")
        labelWidth.pack()
        
        popup.inputHeight = Text(popup, height=1, width=5)
        popup.inputHeight.pack()
        
        labelHeight = Label(popup, text="Type Item Height above")
        labelHeight.pack()
        
        confirm_button = tk.Button(
            popup,
            text="Confirm Item Size",
            command=lambda: self.set_item_size(popup)
        )
        confirm_button.pack()
        
    def set_item_size(self, configWindow):
        itemWidth = configWindow.inputWidth.get(1.0, "end")[:-1]
        itemHeight = configWindow.inputHeight.get(1.0, "end")[:-1]
        try:
            itemWidth = float(itemWidth)
            itemHeight = float(itemHeight)
        except ValueError:
            showinfo(message="Invalid Input")
            return

        if (itemHeight == 0.0 or itemWidth == 0.0):
            showinfo(message="Invalid Canvas Size")
            return
        self.itemWidth = itemWidth
        self.itemHeight = itemHeight
        self.scene.config(height=int(self.itemHeight), width=int(self.itemWidth))
        showinfo(message="Success")
        
    def create_new_shape(self):
        popup = Toplevel(self)
        popup.geometry("750x250")
        popup.title("Shape Config")
        
        popup.color = ((0, 0, 0), '#000000') # initialized to be black
        
        colorFrame = tk.Frame(popup)
        colorFrame.pack()
        
        color_label = tk.Label(popup, bg=popup.color[-1],height=1, width=2)
        popup.color_label = color_label
        
        color_picker = tk.Button(
            popup,
            text="Pick color",
            command=lambda: self.choose_color(popup)
        )
        
        curr_color = tk.Label(popup, text="Current Color:")
 
        color_picker.pack(in_=colorFrame, side=tk.LEFT, pady=20)
        curr_color.pack(in_=colorFrame, side=tk.LEFT, padx=5)
        color_label.pack(in_=colorFrame, side=tk.LEFT, padx=1)

        shapeLabel = tk.Label(popup, text="Input Coordinates of Points to create new shape\nForm: x1, y1, x2, y2, ...")
        #shapes = Entry(popup, width=50)
        shapes = Text(popup, height=3, width=50)
        shapeLabel.pack()
        shapes.focus_set()
        popup.shapes = shapes
        shapes.pack()
        
        tagFrame = tk.Frame(popup)
        tagFrame.pack()
        
        tagLabel = tk.Label(popup, text="Tag of the new shape")
        tagEntry = Entry(popup)
        tagLabel.pack(in_=tagFrame, side=tk.LEFT)
        tagEntry.pack(in_=tagFrame, side=tk.LEFT, padx=1)
        
        popup.tagEntry = tagEntry
        
        popup.isSmooth = tk.IntVar()
        smooth = tk.Checkbutton(popup, text="Draw Curve", variable=popup.isSmooth, onvalue=1, offvalue=0)
        smooth.pack()
        
        confirm_button = tk.Button(
            popup,
            text="Generate Shape",
            command=lambda: self.generate_shape(popup)
        )
        confirm_button.pack()
    
    def generate_shape(self, configWindow):
        points = configWindow.shapes.get(1.0, "end")
        try:
            points = points[:-1].split(",")
            points = list(map(float, points))
        except ValueError:
            showinfo(message="Invalid Input")
            configWindow.shapes.delete(1.0, "end")
            return
            
        if len(points) < 4 or len(points) % 2 == 1:
            showinfo(message="Not Enough Input")
            configWindow.shapes.delete(1.0, "end")
            return
        
        print(points)
        print(configWindow.isSmooth.get())
        id = self.scene.create_line(points, fill=configWindow.color[-1], smooth=configWindow.isSmooth.get())
        tag = configWindow.tagEntry.get()
        print(tag)
        configWindow.destroy()
        
    def save_shape(self):
        if len(self.scene.find_all()) == 0:
            showinfo(message="Empty scene")
            return
        name = askstring('csvName', 'Name of output csv file')
        if name == "":
            showinfo(message="Invalid output file name")
            return
        ps = self.scene.postscript(colormode="color", pagewidth=self.itemWidth-1, pageheight=self.itemHeight-1)
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        
        img = img.convert("RGBA")
        datas = img.getdata()
        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)

        img.putdata(newData)
        # im = open_eps(ps, dpi=119.5)
        image_fileName = "/output/images/{}.png".format(name)
        # im.save(".." + image_fileName, dpi=(119.5, 119.5))
        img.save(".." + image_fileName)
        showinfo(message="Success")
    
    def choose_color(self, parent):
        parent.color = colorchooser.askcolor(parent=parent, title="Choose color")
        parent.color_label.config(bg=parent.color[-1])
            
        
if __name__ == "__main__":
    testObj = windows()
    testObj.mainloop()