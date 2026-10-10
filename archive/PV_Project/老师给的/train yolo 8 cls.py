from ultralytics import YOLO

def main():
    # === CONFIGURATION ===
    dataset_dir = r"D:\YOLO-SPHMapper\Classifiers\YOLO8\Dataset"
    model_architecture = 'D:\YOLO-SPHMapper\Classifiers\YOLO8\yolo8m-cls.pt'

    # === TRAINING PARAMETERS ===
    epochs = 100               # Number of training epochs
    batch = 16              # Batch size (adjust based on your GPU memory)
    imgsz = 64                # Image size for classification
    device = 0                # Use GPU (set to 0 or "cuda:0")
    project = "D:\YOLO-SPHMapper\Classifiers\YOLO8\Dust Classifier"
    name = "batch 16"      # Subfolder name for this experiment
    pretrained = True         # Use pretrained backbone

    # === INIT & TRAIN MODEL ===
    model = YOLO(model_architecture)

    model.train(
        data=dataset_dir,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        pretrained=pretrained
    )

    print("✅ Training complete.")

# Required for Windows multiprocessing
if __name__ == '__main__':
    main()
