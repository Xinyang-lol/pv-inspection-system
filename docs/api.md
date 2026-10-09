# HTTP 接口说明

接口定义来自 `backend/app.py`，分析与汇总实现位于 `backend/services/pipeline.py`。

服务默认地址为 `http://127.0.0.1:5000`。

## 状态与看板

```bash
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/dashboard
curl http://127.0.0.1:5000/api/samples
```

- `/api/health` 返回 `ok` 以及推理模块的状态信息。
- `/api/dashboard` 返回推理模块构建的看板数据；前端读取 `status`、`overview`、`samples`、`recent_records`、`recommendations`、`charts`。
- `/api/samples` 返回 `{"samples": [...]}`。

## 上传分析

```bash
curl -X POST -F "image=@/path/to/panel.jpg" http://127.0.0.1:5000/api/analyze
```

Windows PowerShell 请使用 `curl.exe`，例如：

```powershell
curl.exe -X POST -F "image=@C:/images/panel.jpg" http://127.0.0.1:5000/api/analyze
```

请求类型为 `multipart/form-data`，每次上传一张图片，字段名为 `image`。

| 情况 | 状态码 | 已定义的响应 |
| --- | --- | --- |
| 缺少 `image` 字段 | 400 | `{"error": "请上传图像文件，字段名为 image。"}` |
| 文件名为空 | 400 | `{"error": "未收到有效图像文件。"}` |
| 正常上传 | 由处理结果决定 | `pipeline.analyze()` 的返回值 |

分析成功响应包含 `analysis` 和 `dashboard`；`analysis.result` 包含 `summary`、`panels`、`detections`、`runtime_ms` 等字段，`analysis.history_entry.result_image_url` 给出标注图 URL。原入口没有对所有损坏图片或推理异常提供统一 JSON 错误处理。

## 示例与结果图

```bash
curl -X POST http://127.0.0.1:5000/api/analyze-sample/dust-heavy
curl http://127.0.0.1:5000/api/sample-files/dust-heavy.png
curl http://127.0.0.1:5000/api/results/result.png
```

示例 ID 必须来自 `/api/samples`。示例缺失返回 404；示例图片和结果图路由返回对应文件，不存在或目录范围不符时返回 404。`result.png` 只是文件名占位示例，实际结果文件名由分析模块生成。

## 重置

```bash
curl -X POST http://127.0.0.1:5000/api/reset
```

清除分析历史并重置看板统计和耗时；已生成的上传文件与结果图仍保留在 `backend/runtime/`。
