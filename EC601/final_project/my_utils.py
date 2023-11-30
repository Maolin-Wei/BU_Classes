import mmcv
import open3d as o3d
import numpy as np
import cv2
from mmengine import load
from pyqtgraph.opengl import GLLinePlotItem
from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph.opengl as gl
import numpy as np
import sys
import os
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from threading import Event
from tqdm import tqdm
import logging


class VideoOutputThread(QThread):
    update_signal = pyqtSignal(str)
    updateImageSignal = pyqtSignal(object, object)
    updatePointCloudSignal = pyqtSignal(np.ndarray, object, object)
    grabFrameSignal = pyqtSignal()

    def __init__(self, visualizer, point_cloud_folder, image_folder, calib_folder, model, ori_point_cloud_widget,
                 ori_image_widget, res_point_cloud_widget, res_image_widget, parent=None):
        super(VideoOutputThread, self).__init__(parent)
        self.output_folder = None
        self.visualizer = visualizer
        self.point_cloud_folder = point_cloud_folder
        self.image_folder = image_folder
        self.calib_folder = calib_folder
        self.model = model
        self.ori_point_cloud_widget = ori_point_cloud_widget
        self.ori_image_widget = ori_image_widget
        self.res_point_cloud_widget = res_point_cloud_widget
        self.res_image_widget = res_image_widget
        self.frameSavedEvent = Event()

    def update_variables(self, visualizer, point_cloud_folder, image_folder, calib_folder, model, output_folder):
        self.visualizer = visualizer
        self.point_cloud_folder = point_cloud_folder
        self.image_folder = image_folder
        self.calib_folder = calib_folder
        self.model = model
        self.output_folder = output_folder

    def run(self):
        # Get point cloud file folder
        pcd_files = [f for f in os.listdir(self.point_cloud_folder) if f.endswith('.bin')]
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        video_output_path = os.path.join(self.output_folder, 'output_video.avi')
        video_writer = cv2.VideoWriter(video_output_path, fourcc, 24.0, (780, 960))
        tqdm_out = TqdmToQt(self)
        self.update_signal.emit("Start to output a video.")

        for pcd_file in tqdm(pcd_files, file=tqdm_out):
            pcd_path = os.path.join(self.point_cloud_folder, pcd_file)
            img_file = pcd_file.replace('.bin', '.png')
            img_path = os.path.join(self.image_folder, img_file)
            calib_file = os.path.join(self.calib_folder, pcd_file.replace('.bin', '.txt'))
            point_cloud, bboxes_3d, processed_img = self.parent().processPointCloudAndImage(pcd_path, img_path,
                                                                                            calib_file)

            self.updatePointCloudSignal.emit(point_cloud, self.ori_point_cloud_widget, None)
            self.updatePointCloudSignal.emit(point_cloud, self.res_point_cloud_widget, bboxes_3d)
            self.grabFrameSignal.emit()
            self.frameSavedEvent.wait()  # Wait for the event to be set
            self.frameSavedEvent.clear()  # Clear the event for next use
            temp_img_path = 'temp_frame.png'
            frame_point_cloud = mmcv.imread(temp_img_path)
            os.remove(temp_img_path)

            # Convert from BGR to RGB
            frame_point_cloud = mmcv.imconvert(frame_point_cloud, 'bgr', 'rgb')
            frame_point_cloud = resize_image(frame_point_cloud)
            # Write frame to video
            img = mmcv.imread(img_path)
            img = mmcv.imconvert(img, 'bgr', 'rgb')
            self.updateImageSignal.emit(convert_img2pixmap(resize_image(img.copy())), self.ori_image_widget)
            self.updateImageSignal.emit(convert_img2pixmap(resize_image(processed_img)), self.res_image_widget)
            processed_img = mmcv.imconvert(processed_img, 'rgb', 'bgr')
            # Stack both frames vertically
            combined_frame = np.vstack((frame_point_cloud, processed_img))
            video_writer.write(combined_frame)

        self.update_signal.emit('Successfully create the video.')
        video_writer.release()


class TqdmToQt(object):
    def __init__(self, video_output_object):
        self.video_output_object = video_output_object

    def write(self, s):
        # Redirect tqdm's output to the Qt object
        self.video_output_object.update_signal.emit(s)

    def flush(self):
        # This method is required for compatibility with file-like interface.
        pass


def read_bin_file(bin_path):
    point_cloud = np.fromfile(bin_path, dtype=np.float32).reshape(-1, 4)
    return point_cloud


def rotz(t):
    c = np.cos(t)
    s = np.sin(t)
    return np.array([[c, -s, 0],
                     [s, c, 0],
                     [0, 0, 1]])


def convert_lidar_box_to_open3d_box(box):
    center = box[0:3]
    size = box[3:6]
    rotation = box[6]

    rotation_matrix = rotz(rotation)

    obb = o3d.geometry.OrientedBoundingBox(center, rotation_matrix, size)
    return obb


def _extend_matrix(mat):
    mat = np.concatenate([mat, np.array([[0., 0., 0., 1.]])], axis=0)
    return mat


def read_calib(calib_path):
    calib_info = {}
    extend_matrix = True
    with open(calib_path, 'r') as f:
        lines = f.readlines()
    P0 = np.array([float(info) for info in lines[0].split(' ')[1:13]]).reshape([3, 4])
    P1 = np.array([float(info) for info in lines[1].split(' ')[1:13]]).reshape([3, 4])
    P2 = np.array([float(info) for info in lines[2].split(' ')[1:13]]).reshape([3, 4])
    P3 = np.array([float(info) for info in lines[3].split(' ')[1:13]]).reshape([3, 4])
    if extend_matrix:
        P0 = _extend_matrix(P0)
        P1 = _extend_matrix(P1)
        P2 = _extend_matrix(P2)
        P3 = _extend_matrix(P3)
    R0_rect = np.array([
        float(info) for info in lines[4].split(' ')[1:10]
    ]).reshape([3, 3])
    if extend_matrix:
        rect_4x4 = np.zeros([4, 4], dtype=R0_rect.dtype)
        rect_4x4[3, 3] = 1.
        rect_4x4[:3, :3] = R0_rect
    else:
        rect_4x4 = R0_rect

    Tr_velo_to_cam = np.array([
        float(info) for info in lines[5].split(' ')[1:13]
    ]).reshape([3, 4])
    Tr_imu_to_velo = np.array([
        float(info) for info in lines[6].split(' ')[1:13]
    ]).reshape([3, 4])
    if extend_matrix:
        Tr_velo_to_cam = _extend_matrix(Tr_velo_to_cam)
        Tr_imu_to_velo = _extend_matrix(Tr_imu_to_velo)
    calib_info['P0'] = P0
    calib_info['P1'] = P1
    calib_info['P2'] = P2
    calib_info['P3'] = P3
    calib_info['R0_rect'] = rect_4x4
    calib_info['Tr_velo_to_cam'] = Tr_velo_to_cam
    calib_info['Tr_imu_to_velo'] = Tr_imu_to_velo
    return calib_info


def get_lidar2img(calib_path):
    calibration_data = read_calib(calib_path)
    rect = calibration_data['R0_rect'].astype(np.float32)
    Trv2c = calibration_data['Tr_velo_to_cam'].astype(np.float32)

    lidar2cam = rect @ Trv2c
    lidar2img_res = (calibration_data['P2'] @ lidar2cam).tolist()
    return lidar2img_res


def resize_image(img, width=780, height=480):
    # Calculate the aspect ratio of the target size to the original size
    scale_ratio = min(width / img.shape[1], height / img.shape[0])
    new_size = (int(img.shape[1] * scale_ratio), int(img.shape[0] * scale_ratio))
    # Resize image
    img_resized = cv2.resize(img, new_size)
    # Create a black background image
    resized_img = np.full((height, width, 3), 255, dtype=np.uint8)  # 设置为白色背景
    # Calculate the center position
    start_x = (width - new_size[0]) // 2
    start_y = (height - new_size[1]) // 2
    # Place the resized image on a black background image
    resized_img[start_y:start_y + new_size[1], start_x:start_x + new_size[0]] = img_resized
    return resized_img


def create_bbox_lines(box):
    """
    Creates a lines from the given 3D bounding box parameters.
    """
    center = np.array(box[:3])
    extents = np.array(box[3:6])
    rotation_angle = box[6]

    # Create a bounding box of 8 vertices
    x, y, z = extents / 2
    vertices = np.array([
        [x, y, z], [-x, y, z], [-x, -y, z], [x, -y, z],
        [x, y, -z], [-x, y, -z], [-x, -y, -z], [x, -y, -z]
    ])

    # Rotate vertices
    rotation_matrix = np.array([
        [np.cos(rotation_angle), -np.sin(rotation_angle), 0],
        [np.sin(rotation_angle), np.cos(rotation_angle), 0],
        [0, 0, 1]
    ])
    vertices = np.dot(vertices, rotation_matrix.T) + center

    # Define the sides of the bounding box
    lines = np.array([
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ])

    # Create lines
    line_vertices = []
    for line in lines:
        line_vertices.extend([vertices[line[0]], vertices[line[1]]])

    return np.array(line_vertices)


def add_bbox_lines_to_widget(widget, line_vertices):
    """
    Add bounding box line to OpenGL view item
    """
    lines_item = GLLinePlotItem(pos=line_vertices, color=(1, 0, 0, 1), width=1.0, mode='lines')
    widget.addItem(lines_item)


def display_image(pixmap, label):
    if not pixmap.isNull():
        label.setPixmap(pixmap)


def convert_img2pixmap(img):
    q_image = QtGui.QImage(img.data, img.shape[1], img.shape[0], img.shape[1] * 3, QtGui.QImage.Format_RGB888)
    pixmap = QtGui.QPixmap.fromImage(q_image)
    return pixmap


def display_point_cloud(point_cloud_data, widget, bboxes_3d=None):
    points = point_cloud_data[:, :3]
    # clear previous display
    widget.clear()
    # create scatter
    scatter = gl.GLScatterPlotItem(pos=points, color=(1, 1, 1, 1), size=1)
    # set background black
    widget.setBackgroundColor('black')

    widget.addItem(scatter)

    if bboxes_3d is not None:
        for box in bboxes_3d:
            line_vertices = create_bbox_lines(box)
            add_bbox_lines_to_widget(widget, line_vertices)
