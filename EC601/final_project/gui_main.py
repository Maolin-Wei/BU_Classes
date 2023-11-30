import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QListWidgetItem
from PyQt5.uic import loadUi
from PyQt5 import QtGui, QtCore, QtWidgets
from my_utils import *
import pyqtgraph.opengl as gl
import numpy as np
import os
from mmdet3d.apis import init_model, inference_detector
from mmdet3d.visualization import Det3DLocalVisualizer
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
import torch
from test_tab import test_main
from train_tab import train_main
import threading
import sys


class StreamToLogger:
    def __init__(self, log_message_function, browser_widget):
        self.log_message_function = log_message_function
        self.browser_widget = browser_widget

    def write(self, message):
        if message != '\n':
            self.log_message_function(message, self.browser_widget)

    def flush(self):
        pass


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # Load the UI design
        loadUi("./ui/main.ui", self)
        self.gui_log_handler = None

        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.modelsConfig = {
            'KITTI': {
                'PointPillars': ('configs/pointpillars/pointpillars_hv_secfpn_8xb6-160e_kitti-3d-3class.py',
                                 'checkpoints/hv_pointpillars_secfpn_6x8_160e_kitti-3d-3class_20220301_150306-37dc2420.pth'),
                'Point_RCNN': ('configs/point_rcnn/point-rcnn_8xb2_kitti-3d-3class.py',
                               'checkpoints/point_rcnn_2x8_kitti-3d-3classes_20211208_151344.pth'),
                'SECOND': ('configs/second/second_hv_secfpn_8xb6-80e_kitti-3d-3class.py',
                           'checkpoints/hv_second_secfpn_fp16_6x8_80e_kitti-3d-3class_20200925_110059-05f67bdf.pth')
            },
            'nuScenes': {
                'PointPillars': ('configs/pointpillars/pointpillars_hv_fpn_sbn-all_8xb2-amp-2x_nus-3d.py',
                                 'checkpoints/hv_pointpillars_fpn_sbn-all_fp16_2x8_2x_nus-3d_20201021_120719-269f9dd6.pth')
            },
            'Waymo': {
                'PointPillars': ('configs/pointpillars/pointpillars_hv_secfpn_sbn-all_16xb2-2x_waymoD5-3d-3class.py',
                                 'checkpoints/hv_pointpillars_secfpn_sbn_2x16_2x_waymoD5-3d-3class_20200831_204144-d1a706b1.pth'),
            },
        }

        self.model = init_model(self.modelsConfig['KITTI']['PointPillars'][0], self.modelsConfig['KITTI']['PointPillars'][1], device=self.device)

        self.visualizer = Det3DLocalVisualizer()
        self.point_cloud_file = ''
        self.image_file = ''
        self.calib_file = ''
        self.point_cloud_folder = ''
        self.image_folder = ''
        self.calib_folder = ''

        self.pushButton.clicked.connect(lambda: self.select_folder('point_cloud'))
        self.pushButton_4.clicked.connect(lambda: self.select_folder('image'))
        self.pushButton_2.clicked.connect(lambda: self.select_folder('calib'))
        self.pushButton_3.clicked.connect(self.process_point_cloud)
        self.pushButton_5.clicked.connect(self.process_image)
        self.outputVideo.clicked.connect(self.output_video)
        self.datasetSelect.currentIndexChanged.connect(self.update_demo_dataset)
        self.modelSelect.currentIndexChanged.connect(self.update_demo_model)

        self.oriPointCloud = gl.GLViewWidget(self.oriPointCloudContainer)
        self.oriPointCloud.setObjectName("oriPointCloud")
        self.oriPointCloud.setCameraPosition(pos=QtGui.QVector3D(0, 0, 0), distance=20, azimuth=180, elevation=20)
        self.oriPointCloud.setBackgroundColor('white')
        layout = QtWidgets.QVBoxLayout(self.oriPointCloudContainer)
        layout.addWidget(self.oriPointCloud)

        self.resPointCloud = gl.GLViewWidget(self.resPointCloudContainer)
        self.resPointCloud.setObjectName("resPointCloud")
        self.resPointCloud.setCameraPosition(pos=QtGui.QVector3D(0, 0, 0), distance=20, azimuth=180, elevation=20)
        self.resPointCloud.setBackgroundColor('white')
        layout = QtWidgets.QVBoxLayout(self.resPointCloudContainer)
        layout.addWidget(self.resPointCloud)

        self.pointCloudListWidget.currentItemChanged.connect(self.on_point_cloud_selected)

        self.video_thread = VideoOutputThread(self.visualizer, self.point_cloud_folder, self.image_folder,
                                              self.calib_folder, self.model, self.oriPointCloud, self.oriImage,
                                              self.resPointCloud, self.resImage, parent=self)
        self.video_thread.update_signal.connect(self.log_message)
        self.video_thread.updateImageSignal.connect(self.update_image)
        self.video_thread.updatePointCloudSignal.connect(self.update_point_cloud)
        self.video_thread.grabFrameSignal.connect(self.grab_frame)

        # Initialize model
        # self.update_demo_model()

        # Hide button
        self.pushButton_8.setVisible(False)
        self.pushButton_10.setVisible(False)

        # Test tab
        self.testButton.clicked.connect(self.test)
        self.testDatasetSelect.currentIndexChanged.connect(self.update_test_dataset)
        self.testModelSelect.currentIndexChanged.connect(self.update_test_model)

        # Train tab
        self.trainButton.clicked.connect(self.train)
        self.trainDatasetSelect.currentIndexChanged.connect(self.update_train_dataset)
        self.trainModelSelect.currentIndexChanged.connect(self.update_train_model)

    def test(self):
        # re-direct print to testLogTextBrowser
        sys.stdout = StreamToLogger(self.log_message, self.testLogTextBrowser)
        thread = threading.Thread(target=self.run_test)
        thread.start()

    def train(self):
        # re-direct print to trainLogTextBrowser
        sys.stdout = StreamToLogger(self.log_message, self.trainLogTextBrowser)
        thread = threading.Thread(target=self.run_train)
        thread.start()

    def run_test(self):
        dataset_name = self.testDatasetSelect.currentText()
        model_name = self.testModelSelect.currentText()

        config_file, checkpoint_file = self.modelsConfig.get(dataset_name, {}).get(model_name, (None, None))
        if config_file and checkpoint_file:
            self.log_message(f"Test {model_name} model on {dataset_name} dataset", self.testLogTextBrowser)
            test_main(config_file, checkpoint_file)
        else:
            self.log_message(f"Configuration for {model_name} model on {dataset_name} dataset not found.",
                             self.testLogTextBrowser)

    def run_train(self):
        dataset_name = self.trainDatasetSelect.currentText()
        model_name = self.trainModelSelect.currentText()

        config_file, _ = self.modelsConfig.get(dataset_name, {}).get(model_name, (None, None))
        if config_file:
            self.log_message(f"Train {model_name} model on {dataset_name} dataset", self.trainLogTextBrowser)
            train_main(config_file)
        else:
            self.log_message(f"Configuration for {model_name} model on {dataset_name} dataset not found.",
                             self.trainLogTextBrowser)

    def update_train_dataset(self):
        dataset_name = self.trainDatasetSelect.currentText()
        self.log_message(f"Switch to {dataset_name} dataset", self.trainLogTextBrowser)

    def update_train_model(self):
        model_name = self.trainModelSelect.currentText()
        self.log_message(f"Switch to {model_name} model", self.trainLogTextBrowser)

    def update_test_dataset(self):
        dataset_name = self.testDatasetSelect.currentText()
        self.log_message(f"Switch to {dataset_name} dataset", self.testLogTextBrowser)

    def update_test_model(self):
        model_name = self.testModelSelect.currentText()
        self.log_message(f"Switch to {model_name} model", self.testLogTextBrowser)

    def update_demo_dataset(self):
        dataset_name = self.datasetSelect.currentText()
        self.log_message(f"Switch to {dataset_name} dataset")
        self.update_demo_model()

    def update_demo_model(self):
        dataset_name = self.datasetSelect.currentText()
        model_name = self.modelSelect.currentText()

        config_file, checkpoint_file = self.modelsConfig.get(dataset_name, {}).get(model_name, (None, None))
        if config_file and checkpoint_file:
            self.log_message(f"Load {model_name} model on {dataset_name} dataset")
            self.model = init_model(config_file, checkpoint_file, device=self.device)
        else:
            self.log_message(f"Configuration for {model_name} model on {dataset_name} dataset not found.")

    def log_message(self, message, text_browser=None):
        if text_browser is None:
            text_browser = self.logTextBrowser
        text_browser.append(message)
        QApplication.processEvents()

    def grab_frame(self):
        self.resPointCloud.grabFramebuffer().save('temp_frame.png', 'PNG')
        self.video_thread.frameSavedEvent.set()

    def update_point_cloud(self, point_cloud, widget, bboxes_3d=None):
        try:
            display_point_cloud(point_cloud, widget, bboxes_3d)
        except Exception as e:
            print(f"Error in updatePointCloud: {e}")
            self.log_message(f"Error in updatePointCloud: {e}")

    def update_image(self, pixmap, widget):
        display_image(pixmap, widget)

    def select_folder(self, folderType):
        """
        Select data folder
        folderType: 'point_cloud' | 'image' | 'calib'
        """
        folder_path = QFileDialog.getExistingDirectory(self, f"Select {folderType.capitalize()} Folder")
        if not folder_path:
            self.log_message(f"No {folderType} folder selected")
            return

        self.log_message(f"Selected {folderType.capitalize()} Folder: {folder_path}")
        if folderType == 'point_cloud':
            self.point_cloud_folder = folder_path
            self.update_point_cloud_list_widget(folder_path)
        elif folderType == 'image':
            self.image_folder = folder_path
        elif folderType == 'calib':
            self.calib_folder = folder_path

    def update_point_cloud_list_widget(self, folder_path):
        self.pointCloudListWidget.clear()
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.bin'):
                item = QListWidgetItem(file_name)
                item.setData(QtCore.Qt.UserRole, os.path.join(folder_path, file_name))
                self.pointCloudListWidget.addItem(item)

    def on_point_cloud_selected(self, current):
        if not current:
            return
        self.point_cloud_file = current.data(QtCore.Qt.UserRole)
        point_cloud = read_bin_file(self.point_cloud_file)
        point_cloud_file_name = os.path.splitext(os.path.basename(self.point_cloud_file))[0]
        display_point_cloud(point_cloud, self.oriPointCloud)
        if self.image_folder != '':
            for file_name in os.listdir(self.image_folder):
                if file_name.startswith(point_cloud_file_name) and file_name.lower().endswith(('.jpg', '.png')):
                    self.image_file = os.path.join(self.image_folder, file_name)
                    self.log_message(f"Matching Image File: {self.image_file}")
                    img = mmcv.imread(self.image_file)
                    img = mmcv.imconvert(img, 'bgr', 'rgb')
                    img = resize_image(img)
                    display_image(convert_img2pixmap(img), self.oriImage)
                    break
            for file_name in os.listdir(self.calib_folder):
                if file_name.startswith(point_cloud_file_name) and file_name.lower().endswith('.txt'):
                    self.calib_file = os.path.join(self.calib_folder, file_name)
                    self.log_message(f"Matching Calib File: {self.calib_file}")
                    break
        else:
            self.log_message('Image folder is not selected')

    def process_point_cloud_and_image(self, point_cloud_path, image_path, calib_path):
        try:
            point_cloud = read_bin_file(point_cloud_path)
            result = inference_detector(self.model, point_cloud_path)
            bboxes_3d = result[0].pred_instances_3d.bboxes_3d

            lidar2img_res = np.array(get_lidar2img(calib_path), dtype=np.float32)
            input_meta = {'lidar2img': lidar2img_res}

            img = mmcv.imread(image_path)
            img = mmcv.imconvert(img, 'bgr', 'rgb')

            self.visualizer.set_image(img)
            self.visualizer.draw_proj_bboxes_3d(bboxes_3d, input_meta)
            processed_img = self.visualizer.get_image()
            processed_img = resize_image(processed_img)

            return point_cloud, bboxes_3d, processed_img

        except Exception as e:
            self.log_message(f"Error processing point cloud and image: {e}")
            return None, None, None

    def process_point_cloud(self):
        current_item = self.pointCloudListWidget.currentItem()
        if current_item:
            point_cloud_file = current_item.data(QtCore.Qt.UserRole)
            point_cloud, bboxes_3d, _ = self.process_point_cloud_and_image(
                point_cloud_file, self.image_file, self.calib_file)
            display_point_cloud(point_cloud, self.resPointCloud, bboxes_3d)
        else:
            self.log_message("No point cloud file selected")

    def process_image(self):
        _, _, processed_img = self.process_point_cloud_and_image(
            self.point_cloud_file, self.image_file, self.calib_file)
        display_image(convert_img2pixmap(processed_img), self.resImage)

    def output_video(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            self.log_message(f"Selected Output Folder: {folder_path}")
            self.video_thread.update_variables(self.visualizer, self.point_cloud_folder, self.image_folder,
                                               self.calib_folder, self.model, folder_path)
            if not self.video_thread.isRunning():
                self.video_thread.start()
        else:
            self.log_message("No Output folder selected")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()

    mainWindow.show()
    sys.exit(app.exec_())
