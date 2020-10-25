import os
import supervisely_lib as sly
import random
from collections import defaultdict
import json
import numpy as np
import plotly.graph_objects as go
import time
#np.seterr(divide='ignore')

my_app = sly.AppService()

TEAM_ID = int(os.environ['context.teamId'])
WORKSPACE_ID = int(os.environ['context.workspaceId'])
PROJECT_ID = int(os.environ['modal.state.slyProjectId'])
DATASET_ID = os.environ.get('modal.state.slyDatasetId', None)
if DATASET_ID is not None:
    DATASET_ID = int(DATASET_ID)
USER_LOGIN = os.environ['context.userLogin']

SAMPLE_PERCENT = int(os.environ['modal.state.samplePercent'])
BG_COLOR = [0, 0, 0]
BATCH_SIZE = 50

progress = 0
sum_class_area_per_image = []
sum_class_count_per_image = []
count_images_with_class = []
resolutions_count = defaultdict(int)

overview_columns = ["#", "class name", "images count", "objects count", "avg class area per image (%)", "avg objects count per image"]


def color_text(name, color):
    hexcolor = sly.color.rgb2hex(color)
    #<div style="color:{}">{}</div>
    return '<div><b style="display: inline-block; border-radius: 50%; background: {}; width: 8px; height: 8px"></b> {} </div>'.format(hexcolor, name)


def _col_name(name, color, icon):
    hexcolor = sly.color.rgb2hex(color)
    return '<div><i class="zmdi {}" style="color:{};margin-right:3px"></i> {}</div>'.format(icon, hexcolor, name)


def get_col_name_area(name, color):
    return _col_name(name, color, "zmdi-time-interval")


def get_col_name_count(name, color):
    return _col_name(name, color, "zmdi-equalizer")


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

    fields = [
        {"field": "data.projectName", "payload": project.name},
        {"field": "data.projectId", "payload": project.id},
        {"field": "data.projectPreviewUrl", "payload": api.image.preview_url(project.reference_image_url, 100, 100)}
    ]
    api.task.set_fields(task_id, fields)

    meta_json = api.project.get_meta(project.id)
    meta = sly.ProjectMeta.from_json(meta_json)
    colors_warning = meta.obj_classes.validate_classes_colors()

    # list classes
    class_names = ["unlabeled"]
    class_colors = [[0, 0, 0]]
    class_indices_colors = [[0, 0, 0]]
    _name_to_index = {}
    table_columns = ["image id", "image", "dataset", "height", "width", "channels", "unlabeled"]
    for idx, obj_class in enumerate(meta.obj_classes):
        class_names.append(obj_class.name)
        class_colors.append(obj_class.color)
        class_index = idx + 1
        class_indices_colors.append([class_index, class_index, class_index])
        _name_to_index[obj_class.name] = class_index
        table_columns.append(get_col_name_area(obj_class.name, obj_class.color))
        table_columns.append(get_col_name_count(obj_class.name, obj_class.color))

    sum_class_area_per_image = [0] * len(class_names)
    sum_class_count_per_image = [0] * len(class_names)
    count_images_with_class = [0] * len(class_names)
    #count_images_with_class[0] = 1  # for unlabeled

    api.task.set_field(task_id, "data.table.columns", table_columns)

    ds_images, sample_count = sample_images(api, datasets)
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

                render_idx_rgb = np.zeros(ann.img_size + (3,), dtype=np.uint8)
                render_idx_rgb[:] = BG_COLOR
                ann.draw_class_idx_rgb(render_idx_rgb, _name_to_index)
                stat_area = sly.Annotation.stat_area(render_idx_rgb, class_names, class_indices_colors)
                stat_count = ann.stat_class_count(class_names)

                if stat_area["unlabeled"] > 0:
                    stat_count["unlabeled"] = 1

                table_row = []
                table_row.append(info.id)
                table_row.append('<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>'
                                 .format(api.image.url(TEAM_ID, WORKSPACE_ID, project.id, dataset.id, info.id), info.name))
                table_row.append(dataset.name)
                table_row.extend([stat_area["height"],
                                  stat_area["width"],
                                  stat_area["channels"],
                                  round(stat_area["unlabeled"], 2)])
                resolutions_count["{}x{}x{}".format(stat_area["height"], stat_area["width"], stat_area["channels"])] += 1
                for idx, class_name in enumerate(class_names):
                    sum_class_area_per_image[idx] += stat_area[class_name]
                    sum_class_count_per_image[idx] += stat_count[class_name]
                    count_images_with_class[idx] += 1 if stat_count[class_name] > 0 else 0
                    if class_name == "unlabeled":
                        continue
                    table_row.append(round(stat_area[class_name], 2))
                    table_row.append(round(stat_count[class_name], 2))

                if len(table_row) != len(table_columns):
                    raise RuntimeError("Values for some columns are missed")
                batch_stats.append(table_row)

            all_stats.extend(batch_stats)
            progress += len(batch_stats)

            fields = [
                {"field": "data.progress", "payload": int(progress * 100 / sample_count)},
                {"field": "data.table.data", "payload": batch_stats, "append": True}
            ]
            api.task.set_fields(task_id, fields)
            task_progress.iters_done_report(len(batch_stats))

    # average nonzero class area per image
    with np.errstate(divide='ignore'):
        avg_nonzero_area = np.divide(sum_class_area_per_image, count_images_with_class)
        avg_nonzero_count = np.divide(sum_class_count_per_image, count_images_with_class)

    avg_nonzero_area = np.where(np.isnan(avg_nonzero_area), None, avg_nonzero_area)
    avg_nonzero_count = np.where(np.isnan(avg_nonzero_count), None, avg_nonzero_count)

    fig = go.Figure(
        data=[
            go.Bar(name='Area %', x=class_names, y=avg_nonzero_area, yaxis='y', offsetgroup=1),
            go.Bar(name='Count', x=class_names, y=avg_nonzero_count, yaxis='y2', offsetgroup=2)
        ],
        layout={
            'yaxis': {'title': 'Area'},
            'yaxis2': {'title': 'Count', 'overlaying': 'y', 'side': 'right'}
        }
    )
    # Change the bar mode
    fig.update_layout(barmode='group')  # , legend_orientation="h")


    # images count with/without classes
    images_with_count = []
    images_without_count = []
    images_with_count_text = []
    images_without_count_text = []
    for idx, class_name in enumerate(class_names):
        #if class_name == "unlabeled":
        #    continue
        with_count = count_images_with_class[idx] #- 1 if class_name == "unlabeled" else count_images_with_class[idx]
        without_count = sample_count - with_count
        images_with_count.append(with_count)
        images_without_count.append(without_count)
        images_with_count_text.append("{} ({:.2f} %)".format(with_count, with_count * 100 / sample_count))
        images_without_count_text.append("{} ({:.2f} %)".format(without_count, without_count * 100 / sample_count))

    if len(class_names) != len(images_with_count) or len(class_names) != len(images_with_count_text) or \
        len(class_names) != len(images_without_count) or len(class_names) != len(images_without_count_text):
        raise RuntimeError("Class names are inconsistent with images counting")

    fig_with_without_count = go.Figure(
        data=[
            go.Bar(name='# of images that have class', x=class_names, y=images_with_count, text=images_with_count_text),
            go.Bar(name='# of images that do not have class', x=class_names, y=images_without_count, text=images_without_count_text)
        ],
    )
    fig_with_without_count.update_layout(barmode='stack')  # , legend_orientation="h")

    # barchart resolution
    resolution_labels = []
    resolution_values = []
    resolution_percent = []
    for label, value in sorted(resolutions_count.items(), key=lambda item: item[1], reverse=True):
        resolution_labels.append(label)
        resolution_values.append(value)
    if len(resolution_labels) > 10:
        resolution_labels = resolution_labels[:10]
        resolution_labels.append("other")
        other_value = sum(resolution_values[10:])
        resolution_values = resolution_values[:10]
        resolution_values.append(other_value)
    resolution_percent = [round(v * 100 / sample_count) for v in resolution_values]

    #df_resolution = pd.DataFrame({'resolution': resolution_labels, 'count': resolution_values, 'percent': resolution_percent})
    pie_resolution = go.Figure(data=[go.Pie(labels=resolution_labels, values=resolution_values)])
    #pie_resolution = px.pie(df_resolution, names='resolution', values='count')

    # @TODO: hotfix - pie chart do not refreshes automatically
    fig.update_layout(autosize=False, height=450)
    fig_with_without_count.update_layout(autosize=False, height=450)
    pie_resolution.update_layout(autosize=False, height=450)

    # overview table
    overviewTable = {
        "columns": overview_columns,
        "data": []
    }
    _overview_data = []
    for idx, (class_name, class_color) in enumerate(zip(class_names, class_colors)):
        row = [idx,
               color_text(class_name, class_color),
               count_images_with_class[idx], # - 1 if class_name == "unlabeled" else count_images_with_class[idx],
               sum_class_count_per_image[idx],
               None if avg_nonzero_area[idx] is None else round(avg_nonzero_area[idx], 2),
               None if avg_nonzero_count[idx] is None else round(avg_nonzero_count[idx], 2)
        ]
        _overview_data.append(row)
    overviewTable["data"] = _overview_data

    # save report to file *.lnk (link to report)
    report_name = "{}.lnk".format(project.name)
    local_path = os.path.join(my_app.data_dir, report_name)
    sly.fs.ensure_base_path(local_path)
    with open(local_path, "w") as text_file:
        print(my_app.app_url, file=text_file)
    remote_path = "/reports/classes_stats/{}/{}/{}".format(USER_LOGIN, workspace.name, report_name)
    remote_path = api.file.get_free_name(TEAM_ID, remote_path)
    report_name = sly.fs.get_file_name_with_ext(remote_path)
    file_info = api.file.upload(TEAM_ID, local_path, remote_path)
    report_url = api.file.get_url(file_info["id"])

    fields = [
        {"field": "data.overviewTable", "payload": overviewTable},
        {"field": "data.avgAreaCount", "payload": json.loads(fig.to_json())},
        {"field": "data.imageWithClassCount", "payload": json.loads(fig_with_without_count.to_json())},
        {"field": "data.resolutionsCount", "payload": json.loads(pie_resolution.to_json())},
        {"field": "data.loading0", "payload": False},
        {"field": "data.loading1", "payload": False},
        {"field": "data.loading2", "payload": False},
        {"field": "data.loading3", "payload": False},
        {"field": "state.showDialog", "payload": True},
        {"field": "data.savePath", "payload": remote_path},
        {"field": "data.reportName", "payload": report_name},
        {"field": "data.reportUrl", "payload": report_url},
    ]
    api.task.set_fields(task_id, fields)
    api.task.set_output_report(task_id, file_info["id"], report_name)
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
        "progress": progress,
        "loading0": True,
        "loading1": True,
        "loading2": True,
        "loading3": True,
        "avgAreaCount": json.loads(go.Figure().to_json()),
        "imageWithClassCount": json.loads(go.Figure().to_json()),
        "resolutionsCount": json.loads(go.Figure().to_json()),
        "projectName": "",
        "projectId": "",
        "projectPreviewUrl": "",
        "overviewTable": {
            "columns": overview_columns,
            "data": []
        },
        "savePath": "...",
        "reportName": "..."
    }

    state = {
        "test": 12,
        "perPage": 10,
        "pageSizes": [10, 15, 30, 50, 100],
        "showDialog": False
    }

    # Run application service
    my_app.run(data=data, state=state, initial_events=[{"command": "calc"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
