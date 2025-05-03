<div align="center">
  <h3 align="center">ARMap QGIS Python standalone GUI</h3>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

The project goal is to create an easy to use graphic interface for a autonuoumos robot project at University of Győr. There is an alternative web based GUI option in the project also.

This version is based on QuantumGIS geographic information system QT5 based software, the solution usis its Python capabilitties to implement the necessary features. <br>
The features to implement:
* Map display interface
* Robot diganostic information display using ROS2 from the given topics
* Implementation fo command execution by the robot (sending destination points, emergency stop function)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation

The necessary installed softwares: 
* QGIS installation
* Python3
* ROS2 working install
* Download the folder to your desired destiantion folder.
* Any geotiff image data can be used for visualization

The steps:
1. QGIS install
   ```
   sudo apt-get install qgis
   ```
2. Python3 install
   ```
   sudo apt-get install python3
   ```
3. Install ROS2
   ```
   sudo apt install ros-jazzy-ros-base
   ```
4. Install necessary Python modules using pip
5. Download to the desired destination folder
6. Download the desired GeoTIFF files from 
File can be downloaded from here: [Link](https://drive.google.com/drive/folders/1s2qsFp73ChGFuzdcNKcb3fOp995OTX0y)
7. Start GUI in the destination folder
   ```
   python3 armap_gui.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Start the GUI

The following command will start the application:
   ```
   python3 armap_gui.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>
