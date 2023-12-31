# Final Project - 3D Object Detection Software from Point Clouds

<p align="center">
  <img src="./images/Poster.png" alt="Poster" width="800"， height="600">
</p>


## Introduction
The project is to build the a software platform for object detection in 3D point cloud data. It leverages OpenMMLab's [MMDetection3D](https://github.com/thePegasusai/mmdetection3d) toolbox to process point cloud data, implement the detection model, train/test the model, etc. With an intuitive GUI, it allows users easier utilize advanced algorithms for 3D Object detection from point cloud data, providing a efficient way for a wide range of applications in fields like robotics, autonomous vehicles, an so on.

### Major Features
- **Graphical User Interface (GUI)**: An intuitive GUI, designed in Python PyQt5, facilitating seamless interaction with the software's functionalities. The GUI includes Login windows, detecting, training and testing tabs.  
- **Sign up/in Module**: Provides registration and login window to ensure authorized access to the software.  
- **Detecting Module**: Provides pretrained models on point cloud datasets. Users can upload the point cloud data and visualize the detection results.  
- **Training Module**: Enables users to train their own detection model with selected datasets.  
- **Testing Module**: Enables users to test trained models on selected datasets, offering insights into model performance and accuracy.  

## Demo
- **Demo Turtorial Videos**:  **[Youtube link](https://www.youtube.com/watch?v=uEN7J7l3VUk)**
- **Demo Detection Videos**:  **[Youtube link](https://www.youtube.com/shorts/jL8j-vp2kRg)**

- **Login Window**
<p align="center">
  <img src="./images/login.png" alt="Login" width="500"， height="300">
</p>

- **Registration Window**
<p align="center">
  <img src="./images/register.png" alt="Registration" width="500"， height="300">
</p>

- **Detection Window**
<p align="center">
  <img src="./images/detection.png" alt="Detection" width="800"， height="600">
</p>

- **Train Window**
<p align="center">
  <img src="./images/train.png" alt="Train" width="800"， height="600">
</p>

- **Test Window**
<p align="center">
  <img src="./images/test.png" alt="Test" width="800"， height="600">
</p>


## Getting Started
### Installation
- **MMDection3D**: Please refer to [MMDetection3D's document](https://github.com/thePegasusai/mmdetection3d/blob/master/docs/en/getting_started.md) for installation.
- PyQt5
- pyqtgraph
- OpenCV

### Data Preparation
**1.  Download the dataset and put it in ```data/```.**  

For example, for KITTI dataset, the folder structure should be like below:  
```
    ROOT  
    ├── data  
    │   ├── kitti  
    │   │   │── ImageSets  
    │   │   │── training  
    │   │   │   ├──calib & velodyne & label_2 & image_2  
    │   │   │── testing  
    │   │   │   ├──calib & velodyne & image_2  
    ├── configs  
    ├── mmdet3d  
    ├── tools  
```
**2.  Prepare for the data.** (The process will be ingrated in the GUI for next version)  

Due to different ways of organizing the raw data in different datasets, we typically need to collect the useful data information with a .pkl file. So after getting all the raw data ready, we need to run the scripts provided in the ```tools/create_data.py``` for different datasets to generate data infos.  

For example, for KITTI dataset we need to run:  
```python
python tools/create_data.py kitti --root-path ./data/kitti --out-dir ./data/kitti --extra-tag kitti  
```

Then, the ```data/kitti``` folder structure should be as follows:    
```
    Root  
    ├── data  
    │   ├── kitti  
    │   │   ├── ImageSets  
    │   │   ├── testing  
    │   │   │   ├──calib & image_2 & velodyne & velodyne_reduced  
    │   │   ├── training  
    │   │   │   ├──calib & image_2 & label_2 & velodyne & velodyne_reduced  
    │   │   ├── kitti_gt_database  
    │   │   ├── kitti_infos_train.pkl  
    │   │   ├── kitti_infos_trainval.pkl  
    │   │   ├── kitti_infos_val.pkl  
    │   │   ├── kitti_infos_test.pkl  
    │   │   ├── kitti_dbinfos_train.pkl  
    ├── configs  
    ├── mmdet3d  
    ├── tools  
```
### Run

After all preparations are completed, run the ```login.py``` to launch the software.  
```   
python login.py  
```

### Pcakage

Using ```Pyinstaller``` to package the codes to an executable file(*.exe) that can be run on Windows system.
```
pyinstaller --add-data "packages/mmcv:mmcv" --add-data "packages/yapf_third_party:yapf_third_party" -w login.py
```

After running successfully, a folder named ```dist/``` will generate in the current folder. There will be a ```login.exe``` file in it.

Place folders of ```ui/, checkpoints/, configs/, data/``` into the same directory as the ```login.exe```, then double-click to open the software.

## Reference
- [MMDetection3D](https://github.com/open-mmlab/mmdetection3d)
```latex
@misc{mmdet3d2020,
    title={{MMDetection3D: OpenMMLab} next-generation platform for general {3D} object detection},
    author={MMDetection3D Contributors},
    howpublished = {\url{https://github.com/open-mmlab/mmdetection3d}},
    year={2020}
}
```
