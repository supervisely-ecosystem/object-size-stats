<div align="center" markdown> 

<img src="https://i.imgur.com/NJzq6OM.png"/>

# Object Size Stats
  
<p align="center">

  <a href="#overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#Details">Details</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack) 
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/object-size-stats)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/object-size-stats)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/object-size-stats)](https://supervise.ly)

</div>

## Overview 

Data Exploration Tools provide deep understanding of your data and are crucial for building high quality models (better you understand data, more accurate models are).  

This app generates report with detailed statistics for objects **(`Bitmap` / `Rectangle` / `Polygon`, objects of other shapes are ignored)** in images project. It allows to see big picture as well as shed light on hidden patterns and edge cases (see <a href="#how-to-use">How to use</a> section). 

<img src="https://media.giphy.com/media/7H3Xx4sMmmnjHT6aLv/giphy.gif" width="600"/>


## How To Run

### Step 1: Run from context menu of project / dataset

Go to "Context Menu" (images project or dataset) -> "Report" -> "Object Size Stats"

<img src="https://i.imgur.com/pY9NTHW.png" width="600"/>

### Step 2: Configure running settings

If number of objects in project is huge, define random sample (%). Subset stats is meant to be an unbiased representation of entire data and will be calculated much faster. Choose the percentage of images that should be randomly sampled. By default all images will be used. And then press "Run" button. In advanced settings you can change agent that will host the app and change version (latest available version is used by default).

<img src="https://i.imgur.com/4wZvTLQ.png" width="400"/>


### Step 3:  Open app

Once app is started, new task appear in workspace tasks. Monitor progress from both "Tasks" list and from application page. To open report in a new tab click "Open" button. 

<img src="https://i.imgur.com/VBRYrHP.png"/>

### Step 4: App shuts down automatically

Even if app is finished, you can always use it as a history: open it from tasks list in `Read Only` mode to check Input project, statistics and Output report path. 


## Details

### Input card
<img src="https://i.imgur.com/deOfZvP.png" width="400"/>

Shows input project (clickable), sample percent that user defined at start and the number of images that used in report calculation.

### Output card
<img src="https://i.imgur.com/R5L3N3U.png" width="400"/>

Shows progress bar and then the path to the saved report in `Files`. So you can open it later.  App saves resulting report to "Files": `/reports/objects_stats/{USER_LOGIN}/{WORKSPACE_NAME}/{PROJECT_NAME}.lnk`. 

To open report file from `Files` use "Right mouse click" -> "Open".

### Objects table

Size properties for every object

<img src="https://i.imgur.com/KMMWBr7.png"/>

Columns:
* `OBJECT_ID` - object id
* `CLASS` - object class name
* `IMAGE` - name of the image (clickable URL) on which this object is
* `DATASET` - dataset name
* `IMAGE SIZE (HW)` - image resolution in pixels (height * width)
* `HEIGHT (PX)` - object height in pixels
* `HEIGHT (%)` - object height (percentage of image height)
* `WIDTH (PX)` - object width in pixels
* `WIDTH (%)` - object width (percentage of image width)
* `AREA (PX)` - object area in pixels
* `AREA (%)` - object area (percentage of image area)

### Classes overview

Properties of object (in data sample) for every class. If sample == 100% then all objects are processed. Use horizontal scroll to see all columns.

<img src="https://i.imgur.com/oYeg6LU.png"/>

---<img src="https://media.giphy.com/media/RzVJXnijKWwYzONe57/giphy.gif"/>


Columns:
* `CLASS NAME` - class name
* `OBJECTS COUNT` - number of objects of the class
* `MIN H (PX)` - minimum object height (in pixels)
* `MIN H (%)` - minimum object height (in percent of image height)
* `MAX H (PX)` - maximum object height (in pixels)
* `MAX H (%)` - maximum object height (in percent of image height)
* `AVG H (PX)` - average object height (in pixels)
* `AVG H (%)` - average object height (in percent of image height)
* `MIN W (PX)` - minimum object width (in pixels)
* `MIN W (%)` - minimum object width (in percent of image width)
* `MAX W (PX)` - maximum object width (in pixels)
* `MAX W (%)` - maximum object width (in percent of image width)
* `AVG W (PX)` - average object width (in pixels)
* `AVG W (%)` - average object width (in percent of image width)
* `MIN AREA (%)` - minimum object area (in percent of image area)
* `MAX AREA (%)` - maximum object area (in percent of image area)
* `AVG AREA (%)` - average object area (in percent of image area)

### Distributions [height (px) / width (px) / area (%)]

Histograms shows distributions for all classes at once. Also you can double-click to class to hide other classes except this one. Or you can select several classes to compare their distributions. 

Height (in px) distribution for all classes:
<img src="https://i.imgur.com/AFX5KVX.png"/>

Height (in px) distribution for single class:
<img src="https://i.imgur.com/zhAG0t6.png"/>

Width (in px) distribution for all classes:
<img src="https://i.imgur.com/MzTNrZu.png"/>

Width (in px) distribution for single class:
<img src="https://i.imgur.com/XV2RhLU.png"/>


Area (in %) distribution for all classes:
<img src="https://i.imgur.com/MzTNrZu.png"/>

Area (in %) distribution for single class:
<img src="https://i.imgur.com/z1qJQlo.png"/>
