"""
Name:       Object Bounding Boxes Annotation Tool
Purpose:    Label object bounding boxes for NeuralNetworks project data
Author:     Artem "Manneq" Arkhipov
Mentor:     Dmitri Timofeev
Created:    07/01/2019
Inspired:   BBox-Label-Tool by puzzledqs:
                https://github.com/puzzledqs/BBox-Label-Tool
            BBox-Label-Tool by xiaqufeng:
                https://github.com/xiaqunfeng/BBox-Label-Tool
Note:       Current format of training works with Keras training!
"""
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import os
import glob


class AnnotationTool:
    # global state initializing
    image_dir = ''  # input directory
    image_list = []  # image list directory
    out_dir = ''  # output directory
    current = 0  # current image
    total = 0  # total number of images
    image_name = ''  # path to image
    labels_file_name = ''  # path to label (helps to create and output format)
    tk_image = None  # load image as tk.Image
    current_label_class = ''  # contains current class
    class_candidate_temp = []  # contains all classes
    classes_filename = 'classes.name'  # path to classes file
    color = 'red'  # outline bbox color

    # mouse state initializing
    mouse_state = {}
    mouse_state['click'] = 0  # click variable
    mouse_state['x'] = 0  # x position variable
    mouse_state['y'] = 0  # y position variable

    # Bbox initializing
    bbox_id_list = []  # list of bboxes ids of current image
    bbox_id = None  # id of current bbox
    bbox_list = []  # list of bboxes of current image
    hl = None  # scaling image on height
    vl = None  # scaling image on width

    def __init__(self, master):
        # main frame set up
        self.parent = master
        self.parent.title("Annotation Tool")
        self.frame = tk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=1)
        self.parent.resizable(width=False, height=False)

        # button for input image directory
        self.src_dir_button = tk.Button(self.frame, text="Image input folder",
                                        command=self.select_source_dir)
        self.src_dir_button.grid(row=0, column=0)

        # input image directory entry field
        self.sv_src_path = tk.StringVar()
        self.entry_src = tk.Entry(self.frame, textvariable=self.sv_src_path)
        self.entry_src.grid(row=0, column=1, sticky=tk.W+tk.E)
        self.sv_src_path.set(os.path.join(os.getcwd(), "input"))

        # load button
        self.load_button = tk.Button(self.frame, text="Load",
                                     command=self.load_dir)
        self.load_button.grid(row=0, column=2, rowspan=2, columnspan=2, padx=2,
                              pady=2, ipadx=5, ipady=5)

        # button for saving output directory
        self.destination_button =\
            tk.Button(self.frame, text="Label output folder",
                      command=self.select_destination_dir)
        self.destination_button.grid(row=1, column=0)

        # output directory entry field
        self.sv_destination_path = tk.StringVar()
        self.entry_destination = \
            tk.Entry(self.frame, textvariable=self.sv_destination_path)
        self.entry_destination.grid(row=1, column=1, sticky=tk.W+tk.E)
        self.sv_destination_path.set(os.path.join(os.getcwd(), "output"))

        # main panel for labeling
        self.main_panel = tk.Canvas(self.frame, cursor='tcross')
        # mouse button click
        self.main_panel.bind("<Button-1>", self.mouse_click)
        # mouse movement
        self.main_panel.bind("<Motion>", self.mouse_move)
        # <Espace> button to cancel current bbox
        self.parent.bind("<Escape>", self.cancel_bbox)
        # 's' button to cancel current bbox
        self.parent.bind("s", self.cancel_bbox)
        # 'p' button to go backward
        self.parent.bind("p", self.previous_image)
        # 'n' button to go forward
        self.parent.bind("n", self.next_image)
        self.main_panel.grid(row=2, column=1, rowspan=4, sticky=tk.W+tk.N)

        # choose class panel
        self.class_name = tk.StringVar()
        self.class_candidate = ttk.Combobox(self.frame, state='readonly',
                                            textvariable=self.class_name)
        self.class_candidate.grid(row=2, column=2)

        if os.path.exists(self.classes_filename):
            with open(self.classes_filename) as cf:
                for line in cf.readlines():
                    self.class_candidate_temp.append(line.strip('\n'))

        self.class_candidate['values'] = self.class_candidate_temp
        self.class_candidate.current(0)
        self.current_label_class = self.class_candidate.current()
        self.class_button = tk.Button(self.frame, text="Confirm class",
                                      command=self.set_class())
        self.class_button.grid(row=2, column=3, sticky=tk.W+tk.E)

        # showing bbox info and delete bbox button
        self.bbox_label = tk.Label(self.frame, text="Bounding boxes:")
        self.bbox_label.grid(row=3, column=2, sticky=tk.W+tk.N)
        self.list_box = tk.Listbox(self.frame, width=22, height=12)
        self.list_box.grid(row=4, column=2, sticky=tk.N+tk.S)
        self.delete_button = tk.Button(self.frame, text="Delete",
                                       command=self.delete_bbox)
        self.delete_button.grid(row=4, column=3, sticky=tk.W+tk.E+tk.N)
        self.clear_button = tk.Button(self.frame, text="Clear All",
                                      command=self.clear_bbox)
        self.clear_button.grid(row=4, column=3, sticky=tk.W+tk.E+tk.S)

        # control panel for image navigation
        self.control_panel = tk.Frame(self.frame)
        self.control_panel.grid(row=6, column=1, columnspan=2,
                                sticky=tk.W+tk.E)
        self.previous_button = tk.Button(self.control_panel, text="<< Prev",
                                         width=10,
                                         command=self.previous_image)
        self.previous_button.pack(side=tk.LEFT, padx=5, pady=3)
        self.next_button = tk.Button(self.control_panel, text="Next >>",
                                     width=10, command=self.next_image)
        self.next_button.pack(side=tk.LEFT, padx=5, pady=3)
        self.progress_label = tk.Label(self.control_panel,
                                       text="Progress:     /    ")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        self.temp_label = tk.Label(self.control_panel, text="Go to image")
        self.temp_label.pack(side=tk.LEFT, padx=5)
        self.idx_entry = tk.Entry(self.control_panel, width=5)
        self.idx_entry.pack(side=tk.LEFT)
        self.go_button = tk.Button(self.control_panel, text="Go",
                                   command=self.go_to_image)
        self.go_button.pack(side=tk.LEFT)

        # display mouse position
        self.display_mouse = tk.Label(self.control_panel)
        self.display_mouse.pack(side=tk.RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

    def select_source_dir(self):
        """
        Method to select an input directory
        """
        path = filedialog.askdirectory(title="Select image source folder",
                                       initialdir=self.sv_src_path.get())
        self.sv_src_path.set(path)

        return

    def select_destination_dir(self):
        """
        Method to select an output directory
        """
        path = \
            filedialog.askdirectory(title="Select label output folder",
                                    initialdir=self.sv_destination_path.get())
        self.sv_destination_path.set(path)

        return

    def load_dir(self):
        """
        Method to load input and output directories and image list
        """
        self.parent.focus()
        # get image list
        self.image_dir = self.sv_src_path.get()

        if not os.path.isdir(self.image_dir):
            messagebox.showerror("Error!",
                                 message="The specified folder doesn't exist!")

        extensions = ["*.jpeg", "*.jpg", "*.png", "*.bmp"]

        for e in extensions:
            file_list = glob.glob(os.path.join(self.image_dir, e))
            self.image_list.extend(file_list)

        if len(self.image_list) == 0:
            print('No allowable extensions images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.current = 1
        self.total = len(self.image_list)

        # set up output dir
        self.out_dir = self.sv_destination_path.get()

        if not os.path.exists(self.out_dir):
            os.mkdir(self.out_dir)

        self.load_image()

        print('%d images loaded from %s' % (self.total, self.image_dir))

        return

    def load_image(self):
        """
        Method to load image from the image list
        """
        # load image
        image_path = self.image_list[self.current - 1]
        self.image = Image.open(image_path)
        size = self.image.size
        self.factor = max(size[0] / 1000, size[1] / 1000., 1.)
        self.image = self.image.resize(
            (int(size[0] / self.factor), int(size[1] / self.factor)))
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.main_panel.config(width=max(self.tk_image.width(), 400),
                               height=max(self.tk_image.height(), 400))
        self.main_panel.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        self.progress_label.config(text="%04d/%04d" % (self.current,
                                                       self.total))

        # load labels
        self.clear_bbox()
        full_filename = os.path.basename(image_path)
        self.image_name, _ = os.path.splitext(full_filename)
        label_name = self.image_name + '.txt'
        self.labels_file_name = os.path.join(self.out_dir, label_name)
        bbox_count = 0
        if os.path.exists(self.labels_file_name):
            with open(self.labels_file_name) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_count = int(line.strip())
                        continue
                    # tmp = [int(t.strip()) for t in line.split()]
                    temp = line.split()
                    temp[0] = int(int(temp[0]) / self.factor)
                    temp[1] = int(int(temp[1]) / self.factor)
                    temp[2] = int(int(temp[2]) / self.factor)
                    temp[3] = int(int(temp[3]) / self.factor)
                    self.bbox_list.append(tuple(temp))
                    temp_id = \
                        self.main_panel.create_rectangle(temp[0], temp[1],
                                                         temp[2], temp[3],
                                                         width=2,
                                                         outline=self.color)
                    self.bbox_id_list.append(temp_id)
                    self.list_box.insert(tk.END, '%s : (%d, %d) -> (%d, %d)'
                                         % (temp[4], temp[0], temp[1], temp[2],
                                            temp[3]))
                    self.list_box.itemconfig(len(self.bbox_id_list) - 1,
                                             fg=self.color)

        return

    def save_image(self):
        """
        Method to save current image bboxes to the files:
                1. training.data for YOLOv3 and SSD, witch contains
                multiple classes
                2. training_tiny.data for YOLOv3-tiny, witch contains
                only one class
        Saving  format:
                path/to/image bbox1 bbox2 bbox3 ...
        Bbox format:
                x_min,y_min,x_max,y_max,class_num
        """
        if self.labels_file_name == '':
            return

        with open('output/training.data', 'a') as f:
            self.labels_file_name = self.labels_file_name.split('\\')[
                len(self.labels_file_name.split("\\"))-1]
            self.labels_file_name = \
                self.labels_file_name.split('.')[0] + '.jpg'

            f.write('data/training_data/{} '.format(self.labels_file_name))

            for bbox in self.bbox_list:
                f.write(
                    "{},{},{},{},{} ".format(int(int(bbox[0]) * self.factor),
                                             int(int(bbox[1]) * self.factor),
                                             int(int(bbox[2]) * self.factor),
                                             int(int(bbox[3]) * self.factor),
                                             bbox[4]))

            f.write('\n')

        with open('output/training_tiny.data', 'a') as f:
            f.write('data/training_data/{} '.format(self.labels_file_name))

            for bbox in self.bbox_list:
                f.write(
                    "{},{},{},{},{} ".format(int(int(bbox[0]) * self.factor),
                                             int(int(bbox[1]) * self.factor),
                                             int(int(bbox[2]) * self.factor),
                                             int(int(bbox[3]) * self.factor),
                                             0))

            f.write('\n')

        print('Image No. %d saved' % self.current)

        return

    def mouse_click(self, event):
        """
        Method to read mouse clicks and save minimum and maximum
                bbox coordinates with current class
        """
        if self.mouse_state['click'] == 0:
            self.mouse_state['x'], self.mouse_state['y'] = event.x, event.y
        else:
            x1, x2 = min(self.mouse_state['x'], event.x), \
                     max(self.mouse_state['x'], event.x)
            y1, y2 = min(self.mouse_state['y'], event.y), \
                     max(self.mouse_state['y'], event.y)
            self.bbox_list.append((x1, y1, x2, y2, self.current_label_class))
            self.bbox_id_list.append(self.bbox_id)
            self.bbox_id = None
            self.list_box.insert(tk.END, '%s : (%d, %d) -> (%d, %d)' % (
                self.current_label_class, x1, y1, x2, y2))
            self.list_box.itemconfig(len(self.bbox_id_list) - 1, fg=self.color)

        self.mouse_state['click'] = 1 - self.mouse_state['click']

    def mouse_move(self, event):
        """
        Method to read mouse moves on the displayed image
        """
        self.display_mouse.config(text='x: %d, y: %d' % (event.x, event.y))

        if self.tk_image:
            if self.hl:
                self.main_panel.delete(self.hl)
            self.hl = self.main_panel.create_line(0, event.y,
                                                  self.tk_image.width(),
                                                  event.y, width=2)

            if self.vl:
                self.main_panel.delete(self.vl)
            self.vl = self.main_panel.create_line(event.x, 0, event.x,
                                                  self.tk_image.height(),
                                                  width=2)

        if self.mouse_state['click'] == 1:
            if self.bbox_id:
                self.main_panel.delete(self.bbox_id)

            self.bbox_id = self.main_panel.create_rectangle(
                self.mouse_state['x'], self.mouse_state['y'], event.x, event.y,
                width=2, outline=self.color)

    def cancel_bbox(self):
        """
        Method to cancel the current bbox
        """
        if self.mouse_state['click'] == 1:
            if self.bbox_id:
                self.main_panel.delete(self.bbox_id)
                self.bbox_id = None
                self.mouse_state['click'] = 0

        return

    def delete_bbox(self):
        """Method to delete the current bbox"""
        sel = self.list_box.curselection()

        if len(sel) != 1:
            return

        idx = int(sel[0])
        self.main_panel.delete(self.bbox_id_list[idx])
        self.bbox_id_list.pop(idx)
        self.bbox_list.pop(idx)
        self.list_box.delete(idx)

        return

    def clear_bbox(self):
        """
        Method to clear the current bbox
        """
        for idx in range(len(self.bbox_id_list)):
            self.main_panel.delete(self.bbox_id_list[idx])

        self.list_box.delete(0, len(self.bbox_list))
        self.bbox_id_list = []
        self.bbox_list = []

        return

    def previous_image(self):
        """
        Method to go to the previous image
        """
        self.save_image()

        if self.current > 1:
            self.current -= 1
            self.load_image()

        return

    def next_image(self):
        """
        Method to go to the next image
        """
        self.save_image()

        if self.current < self.total:
            self.current += 1
            self.load_image()

        return

    def go_to_image(self):
        """
        Method to go to a specific image
        """
        idx = int(self.idx_entry.get())

        if 1 <= idx <= self.total:
            self.save_image()
            self.current = idx
            self.load_image()

        return

    def set_class(self):
        """
        Method to change current class to annotate
        """
        self.current_label_class = self.class_candidate.current()

        print('Set label class to : %s' % self.current_label_class)

        return


if __name__ == '__main__':
    root = tk.Tk()
    tool = AnnotationTool(root)
    root.resizable(width=True, height=True)
    root.mainloop()
