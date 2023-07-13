import os
import supervisely as sly
import random
from collections import defaultdict
import json
import plotly.graph_objects as go
from statistics import mean
import pandas as pd
import plotly.express as px
from supervisely.app.v1.app_service import AppService

my_app: AppService = AppService()

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])
DATASET_ID = os.environ.get('modal.state.slyDatasetId', None)
if DATASET_ID is not None:
    DATASET_ID = int(DATASET_ID)
USER_LOGIN = os.environ['context.userLogin']

SAMPLE_PERCENT = int(os.environ['modal.state.samplePercent'])
BATCH_SIZE = 50

progress = 0


class_heights_px = defaultdict(list)
class_widths_px = defaultdict(list)
class_areas_px = defaultdict(list)
class_heights_norm = defaultdict(list)
class_widths_norm = defaultdict(list)
class_areas_norm = defaultdict(list)
class_objects_count = defaultdict(int)


def color_text(name, color):
    hexcolor = sly.color.rgb2hex(color)
    # <div style="color:{}">{}</div>
    return '<div><b style="display: inline-block; border-radius: 50%; background: {}; width: 8px; height: 8px"></b> {} </div>'.format(
        hexcolor, name)


def sample_images(api, datasets):
    all_images = []
    for dataset in datasets:
        images = api.image.get_list(dataset.id)
        all_images.extend(images)

    cnt_images = len(all_images)
    if SAMPLE_PERCENT != 100:
        cnt_images = int(max(1, SAMPLE_PERCENT * len(all_images) / 100))
        random.shuffle(all_images)
        all_images = all_images[:cnt_images]

    ds_images = defaultdict(list)
    for image_info in all_images:
        ds_images[image_info.dataset_id].append(image_info)
    return ds_images, cnt_images


@my_app.callback("calc")
@sly.timeit
def calc(api: sly.Api, task_id, context, state, app_logger):
    global progress, sum_class_area_per_image, sum_class_count_per_image, count_images_with_class

    workspace = api.workspace.get_info_by_id(WORKSPACE_ID)
    project = None
    datasets = None
    if DATASET_ID is not None:
        dataset = api.dataset.get_info_by_id(DATASET_ID)
        datasets = [dataset]

    project = api.project.get_info_by_id(PROJECT_ID)
    if datasets is None:
        datasets = api.dataset.get_list(PROJECT_ID)

    ds_images, sample_count = sample_images(api, datasets)

    fields = [
        {"field": "data.projectName", "payload": project.name},
        {"field": "data.projectId", "payload": project.id},
        {"field": "data.projectPreviewUrl", "payload": api.image.preview_url(project.reference_image_url, 100, 100)},
        {"field": "data.samplePercent", "payload": SAMPLE_PERCENT},
        {"field": "data.sampleCount", "payload": sample_count},
    ]
    api.task.set_fields(task_id, fields)

    meta_json = api.project.get_meta(project.id)
    meta = sly.ProjectMeta.from_json(meta_json)

    # list classes
    class_names = []
    class_colors = []
    for idx, obj_class in enumerate(meta.obj_classes):
        if obj_class.geometry_type not in [sly.Bitmap, sly.Rectangle, sly.Polygon]:
            continue
        class_names.append(obj_class.name)
        class_colors.append(obj_class.color)

    if len(class_names) == 0 or len(class_colors) == 0:
        sly.logger.warn("""
There are no classes with bitmap, rectangle or polygon geometry in the project.
Classes with other geometry types can not be used for building histograms.""")

    table_columns = ["object_id", "class", "image", "dataset", "image size (hw)",
                     "h (px)", "h (%)", "w (px)", "w (%)", "area (px)", "area (%)"]
    api.task.set_field(task_id, "data.table.columns", table_columns)

    all_stats = []
    task_progress = sly.Progress("Stats", sample_count, app_logger)
    for dataset_id, images in ds_images.items():
        dataset = api.dataset.get_info_by_id(dataset_id)
        for batch in sly.batched(images, batch_size=BATCH_SIZE):
            batch_stats = []

            image_ids = [image_info.id for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset_id, image_ids)
            ann_jsons = [ann_info.annotation for ann_info in ann_infos]

            for info, ann_json in zip(batch, ann_jsons):
                ann = sly.Annotation.from_json(ann_json, meta)

                image_height = ann.img_size[0]
                image_width = ann.img_size[1]
                image_area = image_height * image_width
                for label in ann.labels:
                    if type(label.geometry) not in [sly.Bitmap, sly.Rectangle, sly.Polygon]:
                        continue

                    table_row = []
                    table_row.append(label.geometry.sly_id)
                    table_row.append(label.obj_class.name)
                    table_row.append(
                        '<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>'
                            .format(api.image.url(TEAM_ID, WORKSPACE_ID, project.id, dataset.id, info.id), info.name)
                    )
                    table_row.append(dataset.name)
                    table_row.append("{}x{}".format(image_height, image_width))

                    rect_geometry = label.geometry.to_bbox()
                    height_px = rect_geometry.height
                    height_norm = round(height_px * 100.0 / image_height, 2)
                    table_row.extend([height_px, height_norm])

                    width_px = rect_geometry.width
                    width_norm = round(width_px * 100.0 / image_width, 2)
                    table_row.extend([width_px, width_norm])

                    area_px = label.geometry.area
                    area_norm = round(area_px * 100.0 / image_area, 2)
                    table_row.extend([area_px, area_norm])

                    class_heights_px[label.obj_class.name].append(height_px)
                    class_heights_norm[label.obj_class.name].append(height_norm)
                    class_widths_px[label.obj_class.name].append(width_px)
                    class_widths_norm[label.obj_class.name].append(width_norm)
                    class_areas_px[label.obj_class.name].append(area_px)
                    class_areas_norm[label.obj_class.name].append(area_norm)
                    class_objects_count[label.obj_class.name] += 1

                    batch_stats.append(table_row)
                progress += 1

            all_stats.extend(batch_stats)
            fields = [
                {"field": "data.progress", "payload": int(progress * 100 / sample_count)},
                {"field": "data.table.data", "payload": batch_stats, "append": True}
            ]
            api.task.set_fields(task_id, fields)
            task_progress.iters_done_report(len(batch))

    # overview table
    overview_columns = ["#", "class name", "objects count",
                        "min h (px)", "min h (%)", "max h (px)", "max h (%)", "avg h (px)", "avg h (%)",
                        "min w (px)", "min w (%)", "max w (px)", "max w (%)", "avg w (px)", "avg w (%)",
                        "min area (%)", "max area (%)", "avg area (%)",
                        ]
    overviewTable = {
        "columns": overview_columns,
        "data": []
    }
    _overview_data = []
    for idx, (class_name, class_color) in enumerate(zip(class_names, class_colors)):
        row = [idx, color_text(class_name, class_color), class_objects_count[class_name]]
        if class_objects_count[class_name] > 0:
            row.extend([
                min(class_heights_px[class_name]), min(class_heights_norm[class_name]),
                max(class_heights_px[class_name]), max(class_heights_norm[class_name]),
                round(mean(class_heights_px[class_name]), 2), round(mean(class_heights_norm[class_name]), 2),
                min(class_widths_px[class_name]), min(class_widths_norm[class_name]),
                max(class_widths_px[class_name]), max(class_widths_norm[class_name]),
                round(mean(class_widths_px[class_name]), 2), round(mean(class_widths_norm[class_name]), 2),
                round(min(class_areas_norm[class_name]), 2), round(max(class_areas_norm[class_name]), 2),
                round(mean(class_areas_norm[class_name]), 2)
            ])
        else:
            row.extend([None] * 12)
        _overview_data.append(row)
    overviewTable["data"] = _overview_data

    # @TODO: how to use class colors
    def _create_hist(class2values, name):
        table = []
        for (class_name, class_color) in zip(class_names, class_colors):
            for v in class2values[class_name]:
                table.append([class_name, v])
        df = pd.DataFrame(table, columns=["class", name])
        if df.empty:
            return None
        hist = px.histogram(df, x=name, color="class")
        return hist

    #histograms
    hist_height = _create_hist(class_heights_px, "height")
    hist_width = _create_hist(class_widths_px, "width")
    hist_area = _create_hist(class_areas_norm, "area (%)")

    # # save report to file *.lnk (link to report)
    report_name = "{}.lnk".format(project.name)
    local_path = os.path.join(my_app.data_dir, report_name)
    sly.fs.ensure_base_path(local_path)
    with open(local_path, "w") as text_file:
        print(my_app.app_url, file=text_file)
    remote_path = "/reports/objects_stats/{}/{}/{}".format(USER_LOGIN, workspace.name, report_name)
    remote_path = api.file.get_free_name(TEAM_ID, remote_path)
    report_name = sly.fs.get_file_name_with_ext(remote_path)
    file_info = api.file.upload(TEAM_ID, local_path, remote_path)
    report_url = api.file.get_url(file_info.id)

    if hist_height is not None:
        hist_height = json.loads(hist_height.to_json())
    if hist_width is not None:
        hist_width = json.loads(hist_width.to_json())
    if hist_area is not None:
        hist_area = json.loads(hist_area.to_json())

    fields = [
        {"field": "data.overviewTable", "payload": overviewTable},
        {"field": "data.histHeight", "payload": hist_height},
        {"field": "data.histWidth", "payload": hist_width},
        {"field": "data.histArea", "payload": hist_area},
        {"field": "data.loading0", "payload": False},
        {"field": "data.loading1", "payload": False},
        {"field": "data.loading2", "payload": False},
        {"field": "data.loading3", "payload": False},
        {"field": "data.savePath", "payload": remote_path},
        {"field": "data.reportName", "payload": report_name},
        {"field": "data.reportUrl", "payload": report_url},
    ]
    api.task.set_fields(task_id, fields)
    api.task.set_output_report(task_id, file_info.id, report_name)
    my_app.stop()


def main():
    sly.logger.info("Script arguments", extra={"projectId": PROJECT_ID, "datasetId": DATASET_ID,
                                               "samplePercent": SAMPLE_PERCENT})

    api = sly.Api.from_env()

    data = {
        "table": {
            "columns": [],
            "data": []
        },
        "overviewTable": {
            "columns": [],
            "data": []
        },
        "progress": progress,
        "loading0": True,
        "loading1": True,
        "loading2": True,
        "loading3": True,
        "histHeight": json.loads(go.Figure().to_json()),
        "histWidth": json.loads(go.Figure().to_json()),
        "histArea": json.loads(go.Figure().to_json()),
        "projectName": "",
        "projectId": "",
        "projectPreviewUrl": "",
        "savePath": "...",
        "reportName": "...",
        "samplePercent": "",
        "sampleCount": ""
    }

    state = {
        "test": 12,
        "perPage": 10,
        "pageSizes": [10, 15, 30, 50, 100],
        "showDialog": False
    }

    # Run application service
    my_app.run(data=data, state=state, initial_events=[{"command": "calc"}])

#@TODO: add columns descriptions directly to the report
if __name__ == "__main__":
    sly.main_wrapper("main", main)
