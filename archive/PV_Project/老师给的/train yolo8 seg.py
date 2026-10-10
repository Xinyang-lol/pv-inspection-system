from ultralytics import YOLO

if __name__ == "__main__":

    # Load a model
    model = YOLO("D:\YOLO-SPHMapper\Segmentators\YOLO8\yolov8m-seg.pt")

    #Use the model
    results = model.train(data="D:\YOLO-SPHMapper\Segmentators\YOLO8\data.yaml", epochs=150, batch=8, imgsz=640)