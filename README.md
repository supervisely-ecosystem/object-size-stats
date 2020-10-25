# TODO
only for bitmap/rectangle/polygon - other objects are ignored



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
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/object-size-stats&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/object-size-stats&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/object-size-stats&counter=runs&label=runs)](https://supervise.ly)

</div>

## Overview 

Data Exploration Tools provide deep understanding of your data and are crucial for building high quality models (better you understand data, more accurate models are).  

This app generates report with detailed statistics for objects **(`Bitmap` / `Rectangle` / `Polygon`, objects of other shapes are ignored)** in images project. It allows to see big picture as well as shed light on hidden patterns and edge cases (see <a href="#how-to-use">How to use</a> section). 


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

Shows progress bar and then the path to the saved report in `Files`. So you can open it later.  App saves resulting report to "Files": `/reports/objects_stats/{USER_LOGIN}/{WORKSPACE_NAME}/{PROJECT_NAME}.lnk`. To open report file from `Files` use "Right mouse click" -> "Open".

### Objects table

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


### Height distribution

Histogram shows distribution for all classes at once. 

<img src="https://i.imgur.com/R5L3N3U.png" width="400"/>

Use double click to see the 

Columns:
* `IMAGE ID` - image id in Supervisely Instance
* `IMAGE` - image name with direct link to annotation tool. You can use table to find some anomalies or edge cases in your data by sorting different columns and then quickly open images with annotations to investigate deeper. 
* `HEIGHT`, `WIDTH` - image resolution in pixels
* `CHANNELS` - number of image channels
* `UNLABELED` - percentage of pixels (image area)

Columns for every class:
* <img src="https://i.imgur.com/tyDf3qi.png" width="100"/> - class area (%)
* <img src="https://i.imgur.com/1EquheL.png" width="100"/> - number of objects of a given class (%)

### Per Class Stats

<img src="https://i.imgur.com/ztE4BCG.png"/>

* `CLASS NAME`
* `IMAGES COUNT` - total number of images that have at least one object of a given class
* `OBJECTS COUNT` - total number of objects of a given class
* `AVG CLASS AREA PER IMAGE (%)` -

```
              the sum of a class area on all images               
 -------------------------------------------------------------- 
 the number of images with at least one object of a given class 
```
 
* `AVG OBJECTS COUNT PER IMAGE (%)` - 
```
              total number of class objects               
 -------------------------------------------------------------- 
 the number of images with at least one object of a given class 
```

### Histogram: AVG AREA / AVG OBJECTS COUNT

<img src="https://i.imgur.com/6LXoXHH.png"/>

Histogram view for two metrics from previous chapter: `AVG CLASS AREA PER IMAGE (%)` and `AVG OBJECTS COUNT PER IMAGE (%)`

### Images Count With / Without Class

<img src="https://i.imgur.com/veerIHk.png"/>

### TOP-10 Image Resolutions

<img src="https://i.imgur.com/UwrkTBf.png"/>
