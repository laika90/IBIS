import asyncio
import time

import cv2
import geopy.distance
import numpy as np
import tflite_runtime.interpreter as tflite
import torch
import torchvision


class LibcsDetection:
    def __init__(self):
        print("LibcsDetection initialized")
        self.frame = 0
        self.lat = 0
        self.lng = 0
        self.pitch = 0
        self.roll = 0
        self.yaw = 0
        self.z = 0
        self.ALPHA = np.deg2rad(24.4)  # Horizontal field of view
        self.BETA = np.deg2rad(31.1)  # Vertical field of view
        self.LAT_1deg = 110940.5844  # at lat 35 deg
        self.LNG_1deg = 91287.7885  # at lat 35 deg

    def update(self, frame, lat, lng, pitch, roll, yaw, z):
        self.frame = frame
        self.lat = lat
        self.lng = lng
        self.pitch = np.deg2rad(pitch)
        self.roll = np.deg2rad(roll)
        self.yaw = np.deg2rad(yaw)
        self.z = z

    def box_iou(self, box1, box2):
        # https://github.com/pytorch/vision/blob/master/torchvision/ops/boxes.py
        """
        Return intersection-over-union (Jaccard index) of boxes.
        Both sets of boxes are expected to be in (x1, y1, x2, y2) format.
        Arguments:
            box1 (Tensor[N, 4])
            box2 (Tensor[M, 4])
        Returns:
            iou (Tensor[N, M]): the NxM matrix containing the pairwise
                IoU values for every element in boxes1 and boxes2
        """

        def box_area(box):
            # box = 4xn
            return (box[2] - box[0]) * (box[3] - box[1])

        area1 = box_area(box1.T)
        area2 = box_area(box2.T)

        # inter(N,M) = (rb(N,M,2) - lt(N,M,2)).clamp(0).prod(2)
        inter = (
            (
                torch.min(box1[:, None, 2:], box2[:, 2:])
                - torch.max(box1[:, None, :2], box2[:, :2])
            )
            .clamp(0)
            .prod(2)
        )
        return inter / (
            area1[:, None] + area2 - inter
        )  # iou = inter / (area1 + area2 - inter)

    def xywh2xyxy(self, x):
        # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
        y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
        y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
        y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
        y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
        return y

    def non_max_suppression(
        self,
        prediction,
        conf_thres=0.25,
        iou_thres=0.45,
        classes=None,
        agnostic=False,
        multi_label=False,
        labels=(),
        max_det=300,
    ):
        """Runs Non-Maximum Suppression (NMS) on inference results

        Returns:
            list of detections, on (n,6) tensor per image [xyxy, conf, cls]
        """

        nc = prediction.shape[2] - 5  # number of classes
        xc = prediction[..., 4] > conf_thres  # candidates

        # Checks
        assert (
            0 <= conf_thres <= 1
        ), f"Invalid Confidence threshold {conf_thres}, valid values are between 0.0 and 1.0"
        assert (
            0 <= iou_thres <= 1
        ), f"Invalid IoU {iou_thres}, valid values are between 0.0 and 1.0"

        # Settings
        min_wh, max_wh = 2, 4096  # (pixels) minimum and maximum box width and height
        max_nms = 30000  # maximum number of boxes into torchvision.ops.nms()
        time_limit = 10.0  # seconds to quit after
        redundant = True  # require redundant detections
        multi_label &= nc > 1  # multiple labels per box (adds 0.5ms/img)
        merge = False  # use merge-NMS

        t = time.time()
        output = [torch.zeros((0, 6), device=prediction.device)] * prediction.shape[0]
        for xi, x in enumerate(prediction):  # image index, image inference
            # Apply constraints
            # x[((x[..., 2:4] < min_wh) | (x[..., 2:4] > max_wh)).any(1), 4] = 0  # width-height
            x = x[xc[xi]]  # confidence

            # Cat apriori labels if autolabelling
            if labels and len(labels[xi]):
                l = labels[xi]
                v = torch.zeros((len(l), nc + 5), device=x.device)
                v[:, :4] = l[:, 1:5]  # box
                v[:, 4] = 1.0  # conf
                v[range(len(l)), l[:, 0].long() + 5] = 1.0  # cls
                x = torch.cat((x, v), 0)

            # If none remain process next image
            if not x.shape[0]:
                continue

            # Compute conf
            x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

            # Box (center x, center y, width, height) to (x1, y1, x2, y2)
            box = self.xywh2xyxy(x[:, :4])

            # Detections matrix nx6 (xyxy, conf, cls)
            if multi_label:
                i, j = (x[:, 5:] > conf_thres).nonzero(as_tuple=False).T
                x = torch.cat((box[i], x[i, j + 5, None], j[:, None].float()), 1)
            else:  # best class only
                conf, j = x[:, 5:].max(1, keepdim=True)
                x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > conf_thres]

            # Filter by class
            if classes is not None:
                x = x[(x[:, 5:6] == torch.tensor(classes, device=x.device)).any(1)]

            # Apply finite constraint
            # if not torch.isfinite(x).all():
            #     x = x[torch.isfinite(x).all(1)]

            # Check shape
            n = x.shape[0]  # number of boxes
            if not n:  # no boxes
                continue
            elif n > max_nms:  # excess boxes
                x = x[x[:, 4].argsort(descending=True)[:max_nms]]  # sort by confidence

            # Batched NMS
            c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
            boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
            i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
            if i.shape[0] > max_det:  # limit detections
                i = i[:max_det]
            if merge and (1 < n < 3e3):  # Merge NMS (boxes merged using weighted mean)
                # update boxes as boxes(i,4) = weights(i,n) * boxes(n,4)
                iou = self.box_iou(boxes[i], boxes) > iou_thres  # iou matrix
                weights = iou * scores[None]  # box weights
                x[i, :4] = torch.mm(weights, x[:, :4]).float() / weights.sum(
                    1, keepdim=True
                )  # merged boxes
                if redundant:
                    i = i[iou.sum(1) > 1]  # require redundancy

            output[xi] = x[i]
            if (time.time() - t) > time_limit:
                print(f"WARNING: NMS time limit {time_limit}s exceeded")
                break  # time limit exceeded

        return output

    def parse_pred(self, pred):
        if len(pred[0]) > 0:
            if len(pred[0][0]) == 6:
                s = 1 - (pred[0][0][0] + pred[0][0][2]) / 320  # -1~1
                t = 1 - (pred[0][0][1] + pred[0][0][3]) / 320  # -1~1
                omega = np.matrix(
                    [
                        [np.cos(self.yaw), np.sin(self.yaw)],
                        [-np.sin(self.yaw), np.cos(self.yaw)],
                    ]
                )
                origin = np.matrix(
                    [
                        [np.tan(self.roll + np.arctan(s * np.tan(self.BETA)))],
                        [np.tan(self.pitch + np.arctan(t * np.tan(self.ALPHA)))],
                    ]
                )
                xy = omega * origin * self.z
                # return float(-xy[1]), float(xy[0]), float(pred[0][0][4])
                return float(xy[1] * 1.2), float(-xy[0] * 1.2), float(pred[0][0][4])
        else:
            return None, None, None

    def coordinate_transform(self, x: float, y: float, rot_deg: float) -> tuple:
        """coordinate transform

        Args:
            x (float): x in original coordinate
            y (float): y in original coordinate
            deg (float): rotation

        Returns:
            tuple: transformed x' and y'
        """
        transformed_x = (
            np.cos(rot_deg / 180 * np.pi) * x + np.sin(rot_deg / 180 * np.pi) * y
        )
        transformed_y = (
            -np.sin(rot_deg / 180 * np.pi) * x + np.cos(rot_deg / 180 * np.pi) * y
        )
        return transformed_x, transformed_y

    def letterbox(
        self,
        im,
        new_shape=(640, 640),
        color=(114, 114, 114),
        auto=True,
        scaleFill=False,
        scaleup=True,
        stride=32,
    ):
        # Resize and pad image while meeting stride-multiple constraints
        shape = im.shape[:2]  # current shape [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not scaleup:  # only scale down, do not scale up (for better val mAP)
            r = min(r, 1.0)

        # Compute padding
        ratio = r, r  # width, height ratios
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
        if auto:  # minimum rectangle
            dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
        elif scaleFill:  # stretch
            dw, dh = 0.0, 0.0
            new_unpad = (new_shape[1], new_shape[0])
            ratio = (
                new_shape[1] / shape[1],
                new_shape[0] / shape[0],
            )  # width, height ratios

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(
            im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )  # add border
        return im, ratio, (dw, dh)

    def gps_dest_ne(self, lat, lng, north, east):
        return lat + north / self.LAT_1deg, lng + east / self.LNG_1deg

    async def cycle_detect(self, pixhawk, record):
        if self.model_ver == 2:
            w = "./models/sheet_ver2.tflite"
        elif self.model_ver == 3:
            w = "./models/cone.tflite"
        else:
            w = "./models/sheet.tflite"
        stride = 64
        interpreter = tflite.Interpreter(model_path=w)  # load TFLite model
        print("model", w, "initialized.")
        interpreter.allocate_tensors()  # allocate
        input_details = interpreter.get_input_details()  # inputs
        output_details = interpreter.get_output_details()  # outputs
        int8 = input_details[0]["dtype"] == np.uint8  # is TFLite quantized uint8 model
        imgsz = [320, 320]
        device = "cpu"
        conf_thres = 0.45  # confidence threshold
        iou_thres = 0.45  # NMS IOU threshold
        # target_list = []
        count = 0
        count_sum = 0
        while True:
            if pixhawk.is_detect and record.is_taking:
                self.update(
                    record.frame,
                    pixhawk.latitude_deg,
                    pixhawk.longitude_deg,
                    pixhawk.pitch_deg,
                    pixhawk.roll_deg,
                    pixhawk.yaw_deg,
                    pixhawk.lidar,
                )
                if pixhawk.lidar > 8:
                    print("lidar value broken. continue...")
                    await asyncio.sleep(1)
                    continue
                t0 = time.time()
                img = self.letterbox(self.frame, imgsz, stride=stride, auto=False)[0]
                # Convert
                img = img.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
                img = np.ascontiguousarray(img)
                img = torch.from_numpy(img).to(device)
                img = img.float()  # uint8 to fp16/32
                img = img / 255.0  # 0 - 255 to 0.0 - 1.0
                if len(img.shape) == 3:
                    img = img[None]  # expand for batch dim
                # Inference
                imn = img.permute(0, 2, 3, 1).cpu().numpy()  # image in numpy
                if int8:
                    scale, zero_point = input_details[0]["quantization"]
                    imn = (imn / scale + zero_point).astype(np.uint8)  # de-scale
                interpreter.set_tensor(input_details[0]["index"], imn)
                interpreter.invoke()
                pred = interpreter.get_tensor(output_details[0]["index"])
                if int8:
                    scale, zero_point = output_details[0]["quantization"]
                    pred = (pred.astype(np.float32) - zero_point) * scale  # re-scale
                pred[..., 0] *= imgsz[1]  # x
                pred[..., 1] *= imgsz[0]  # y
                pred[..., 2] *= imgsz[1]  # w
                pred[..., 3] *= imgsz[0]  # h
                pred = torch.tensor(pred)
                # NMS
                pred = self.non_max_suppression(
                    pred, conf_thres, iou_thres, 0, False, max_det=1
                )
                t2 = time.time()

                north_m, east_m, conf = self.parse_pred(pred)

                if north_m is None:
                    print(f"Detection Done. ({t2 - t0:.3f}s), no target")
                    count += 1
                    if count_sum > 3:
                        pixhawk.is_detect = False
                    if count >= 2:
                        pixhawk.alt_target = (
                            pixhawk.absolute_altitude_m - pixhawk.lidar + 1.5
                        )
                        count = 0
                        count_sum += 1
                else:
                    print(
                        f"Detection Done. ({t2 - t0:.3f}s)"
                        + ", north: "
                        + str(north_m)
                        + "m, east: "
                        + str(east_m)
                        + "m, z: "
                        + str(self.z)
                        + "m, conf: "
                        + str(conf * 100)
                        + "%"
                    )
                    print("detection result: ", north_m, east_m)
                    if pixhawk.num_satellites > 10:
                        pixhawk.lat_target = (
                            geopy.distance.distance(meters=north_m)
                            .destination(
                                (pixhawk.latitude_deg, pixhawk.longitude_deg), bearing=0
                            )
                            .latitude
                        )
                        pixhawk.lng_target = (
                            geopy.distance.distance(meters=east_m)
                            .destination(
                                (pixhawk.latitude_deg, pixhawk.longitude_deg),
                                bearing=90,
                            )
                            .longitude
                        )
                    else:
                        pixhawk.lat_target, pixhawk.lng_target = self.gps_dest_ne(
                            self.lat, self.lng, north_m, east_m
                        )
                    # if len(target_list) < 5:
                    #   target_list.append([lat_target, lng_target])
                    # else:
                    #    target_list = target_list[1:]
                    #    target_list.append([lat_target, lng_target])
                    # pixhawk.lat_target, pixhawk.lng_target = np.mean(np.array(target_list), axis=0)
            else:
                print("no frame input...")
                await asyncio.sleep(1)
            await asyncio.sleep(1)
