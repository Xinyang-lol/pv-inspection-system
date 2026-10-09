$(window).on("load", function () {
    $(".loading").fadeOut();
});

(function () {
    var charts = {};
    var selectedFiles = [];
    var sampleRegistry = {};
    var defaultHint = "默认支持 JPG / PNG，后端会自动切换真实推理或演示模式。";
    var DEFAULT_API_BASE = "http://127.0.0.1:5000";
    var API_BASE = resolveApiBase();

    function normalizeApiBase(value) {
        return String(value || "").trim().replace(/\/+$/, "");
    }

    function resolveApiBase() {
        var queryApiBase = "";
        try {
            queryApiBase = normalizeApiBase(new URLSearchParams(window.location.search).get("api"));
        } catch (error) {
            queryApiBase = "";
        }

        if (queryApiBase) {
            return queryApiBase;
        }

        if (window.location.protocol.indexOf("http") === 0 && window.location.port === "5000") {
            return "";
        }

        if (
            window.location.protocol.indexOf("http") === 0 &&
            window.location.hostname &&
            window.location.hostname !== "localhost" &&
            window.location.hostname !== "127.0.0.1"
        ) {
            return window.location.protocol + "//" + window.location.hostname + ":5000";
        }

        return DEFAULT_API_BASE;
    }

    function apiUrl(path) {
        return API_BASE ? API_BASE + path : path;
    }

    function assetUrl(path) {
        if (!path) {
            return "";
        }
        if (/^https?:\/\//i.test(path)) {
            return path;
        }
        return apiUrl(path);
    }

    function pageModeLabel() {
        if (window.location.protocol === "file:") {
            return "本地文件预览";
        }
        if (API_BASE) {
            return "VS Code / 静态预览";
        }
        return "Flask 直连";
    }

    function updateConnectionState(connected, message) {
        $("#pageMode").text(pageModeLabel());
        $("#apiBaseLabel").text(API_BASE ? API_BASE : window.location.origin + "/api");
        $("#apiStatus").text(message || (connected ? "已连接" : "未连接"));
        $("#apiStatus").css("color", connected ? "#9df0b0" : "#ff9d9d");
    }

    function updateUploadState(label, color) {
        $("#uploadState").text(label);
        $("#uploadState").css("color", color || "#fff");
    }

    function setAnalysisNote(message, isError) {
        var note = $("#analysisNote");
        note.text(message);
        note.css("color", isError ? "#ff9d9d" : "rgba(255,255,255,.72)");
    }

    function setRootFont() {
        var width = $(window).width();
        var fontSize = Math.max(42, Math.min(96, width / 20));
        $("html").css({ fontSize: fontSize + "px" });
    }

    function setClock() {
        var now = new Date();
        var text = [
            now.getFullYear(),
            pad(now.getMonth() + 1),
            pad(now.getDate())
        ].join("/") + " " + [pad(now.getHours()), pad(now.getMinutes()), pad(now.getSeconds())].join(":");
        $("#showTime").text(text);
    }

    function pad(value) {
        return value < 10 ? "0" + value : value;
    }

    function setHint(message, isError) {
        var hint = $("#uploadHint");
        hint.text(message);
        hint.css("color", isError ? "#ff9d9d" : "rgba(255,255,255,.68)");
    }

    function getChart(id) {
        if (!charts[id]) {
            charts[id] = echarts.init(document.getElementById(id));
        }
        return charts[id];
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function safeNumber(value, digits) {
        var number = Number(value || 0);
        return digits !== undefined ? number.toFixed(digits) : number;
    }

    function summarizeSelectedFiles(files) {
        if (!files || !files.length) {
            return "未选择";
        }
        if (files.length === 1) {
            return files[0].name;
        }
        var names = files.slice(0, 2).map(function (file) { return file.name; }).join("、");
        return names + (files.length > 2 ? " 等 " : " ") + files.length + " 张";
    }

    function renderProgress(id, value, color) {
        var chart = getChart(id);
        var numeric = Math.max(0, Math.min(100, Number(value || 0)));
        chart.setOption({
            title: {
                text: numeric.toFixed(1).replace(".0", "") + "%",
                x: "center",
                y: "center",
                textStyle: {
                    fontWeight: "normal",
                    color: "#fff",
                    fontSize: 18
                }
            },
            color: "rgba(255,255,255,.18)",
            series: [{
                type: "pie",
                clockWise: true,
                radius: ["65%", "80%"],
                silent: true,
                label: { show: false },
                labelLine: { show: false },
                hoverAnimation: false,
                data: [{
                    value: numeric,
                    itemStyle: { color: color }
                }, {
                    value: 100 - numeric
                }]
            }]
        });
    }

    function renderOverview(overview, status) {
        var mode = status.runtime_mode || overview.runtime_mode || "demo";
        var badge = $("#modeBadge");
        badge.text(mode.toUpperCase());
        badge.removeClass("status-demo status-ready");
        badge.addClass(mode.indexOf("yolo") === 0 ? "status-ready" : "status-demo");

        $("#riskScore").text(Math.round(Number(overview.risk_score || 0)));
        $("#dominantIssue").text(overview.dominant_issue || "待分析");
        $("#analysisCount").text(overview.analysis_count || 0);
        $("#lastFilename").text(overview.last_filename || "待上传图像");
        $("#dirtyPanels").text(overview.dirty_panels || 0);
        $("#panelCount").text(overview.panel_count || 0);
        $("#totalDefects").text(overview.total_defects || 0);
        $("#avgConfidence").text(safeNumber((overview.avg_confidence || 0) * 100, 1) + "%");
        $("#totalLatency").text(safeNumber(overview.total_latency_ms || 0, 1) + " ms");

        renderProgress("pe01", overview.dust_coverage || 0, "#f3d44f");
        renderProgress("pe02", Math.min(100, Number(overview.crack_strength || overview.crack_length || 0)), "#ea5b64");
        renderProgress("pe03", overview.stain_coverage || 0, "#39c98a");

        if (status.runtime_mode === "demo" && status.demo_reason) {
            setHint("当前为演示模式：" + status.demo_reason, false);
        } else if (!selectedFiles.length) {
            setHint(defaultHint, false);
        }

        if (overview.analysis_count > 0) {
            setAnalysisNote(
                "最近一次分析完成：主异常 " +
                    (overview.dominant_issue || "暂无") +
                    "，风险 " +
                    Math.round(Number(overview.risk_score || 0)) +
                    " 分，耗时 " +
                    safeNumber(overview.total_latency_ms || 0, 1) +
                    " ms。",
                false
            );
        }
    }

    function renderModels(status, overview) {
        var models = status.models || [];
        var hasRuntime = Number(overview.analysis_count || 0) > 0;
        var html = models.map(function (model) {
            var chipClass = model.status === "ready" ? "status-ready" : "status-demo";
            var latencyText = hasRuntime ? safeNumber(model.latency_ms || 0, 1) + "ms" : "待运行";
            var extraText = model.status === "demo" ? "演示模式：未加载真实权重" : "真实推理模式";
            return [
                '<div class="model-item">',
                '<div>',
                '<div class="model-name">' + escapeHtml(model.name) + "</div>",
                '<span class="model-role">' + escapeHtml(model.role) + "</span>",
                '<span class="model-weight" title="' + escapeHtml(model.weights) + '">' + escapeHtml(model.weights) + "</span>",
                "</div>",
                '<div class="model-meta">',
                '<span class="status-chip ' + chipClass + '" title="' + escapeHtml(extraText) + '">' + escapeHtml(model.status.toUpperCase()) + "</span>",
                "<strong>" + latencyText + "</strong>",
                '<span class="model-extra">' + escapeHtml(extraText) + "</span>",
                "</div>",
                "</div>"
            ].join("");
        }).join("");

        $("#modelList").html(html || '<div class="model-item"><div class="model-name">暂无模型信息</div></div>');
    }

    function renderPreview(overview) {
        var imageUrl = overview.last_image_url;
        if (imageUrl) {
            $("#resultPreview").attr("src", assetUrl(imageUrl) + "?t=" + Date.now()).show();
            $("#previewPlaceholder").hide();
        } else {
            $("#resultPreview").hide();
            $("#previewPlaceholder").show();
        }
    }

    function renderRecentRecords(records) {
        if (!records || !records.length) {
            $("#recordTable").html('<tr><td colspan="4">暂无分析记录</td></tr>');
            return;
        }

        var html = records.map(function (item) {
            return [
                "<tr>",
                "<td>" + escapeHtml(item.timestamp.replace("T", " ")) + "</td>",
                "<td>" + escapeHtml(item.filename) + "</td>",
                "<td>" + escapeHtml(item.dominant_issue) + "</td>",
                "<td>" + escapeHtml(String(item.risk_score)) + "</td>",
                "</tr>"
            ].join("");
        }).join("");

        $("#recordTable").html(html);
    }

    function renderRecommendations(recommendations) {
        if (!recommendations || !recommendations.length) {
            $("#recommendList").html("<li>暂无建议。</li>");
            return;
        }
        var html = recommendations.map(function (item) {
            return "<li>" + escapeHtml(item) + "</li>";
        }).join("");
        $("#recommendList").html(html);
    }

    function renderSamples(samples) {
        sampleRegistry = {};
        if (!samples || !samples.length) {
            $("#sampleGrid").html('<div class="sample-card sample-empty">当前没有可用示例图</div>');
            return;
        }

        var html = samples.map(function (item) {
            sampleRegistry[item.id] = item;
            return [
                '<div class="sample-card" data-sample-id="' + escapeHtml(item.id) + '">',
                '<img src="' + escapeHtml(assetUrl(item.image_url)) + '" alt="' + escapeHtml(item.name) + '" />',
                '<span class="sample-card-tag">' + (item.ready ? "可分析" : "未就绪") + "</span>",
                '<div class="sample-card-body">',
                '<div class="sample-card-title">' + escapeHtml(item.name) + "</div>",
                '<div class="sample-card-desc">' + escapeHtml(item.summary) + "</div>",
                "</div>",
                "</div>"
            ].join("");
        }).join("");

        $("#sampleGrid").html(html);
    }

    function renderPanelRanking(data) {
        var items = data && data.length ? data : [{ name: "暂无数据", risk: 0 }];
        var chart = getChart("panelRankingChart");
        chart.setOption({
            grid: { left: "3%", right: "8%", top: "6%", bottom: "4%", containLabel: true },
            tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
            xAxis: {
                type: "value",
                max: 100,
                axisLine: { lineStyle: { color: "rgba(255,255,255,.15)" } },
                splitLine: { lineStyle: { color: "rgba(255,255,255,.08)" } },
                axisLabel: { color: "rgba(255,255,255,.65)" }
            },
            yAxis: {
                type: "category",
                inverse: true,
                data: items.map(function (item) { return item.name; }),
                axisLine: { show: false },
                axisTick: { show: false },
                axisLabel: { color: "rgba(255,255,255,.78)" }
            },
            series: [{
                type: "bar",
                data: items.map(function (item) { return item.risk; }),
                barWidth: 14,
                showBackground: true,
                backgroundStyle: { color: "rgba(255,255,255,.06)" },
                label: {
                    show: true,
                    position: "right",
                    color: "#fff",
                    formatter: "{c}"
                },
                itemStyle: {
                    borderRadius: 20,
                    color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                        { offset: 0, color: "#00c6ff" },
                        { offset: 1, color: "#00ff95" }
                    ])
                }
            }]
        });
    }

    function renderRuntimeChart(runtime) {
        var chart = getChart("runtimeChart");
        var labels = runtime.labels || ["面板分割", "缺陷识别", "结果绘制"];
        var values = runtime.values || [0, 0, 0];
        var hasRuntime = values.some(function (value) { return Number(value) > 0; });
        var chartValues = hasRuntime ? values : [];
        var chartLabels = hasRuntime ? labels : [];
        chart.setOption({
            title: hasRuntime ? { show: false } : {
                text: "尚未执行分析",
                left: "center",
                top: "42%",
                textStyle: { color: "rgba(255,255,255,.62)", fontSize: 16 }
            },
            grid: { left: "6%", right: "4%", top: "14%", bottom: "10%", containLabel: true },
            tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
            xAxis: {
                type: "category",
                data: chartLabels,
                axisLine: { lineStyle: { color: "rgba(255,255,255,.12)" } },
                axisLabel: { color: "rgba(255,255,255,.7)", interval: 0 }
            },
            yAxis: {
                type: "value",
                axisLine: { show: false },
                splitLine: { lineStyle: { color: "rgba(255,255,255,.08)" } },
                axisLabel: {
                    color: "rgba(255,255,255,.65)",
                    formatter: "{value} ms"
                }
            },
            series: [{
                type: "bar",
                data: chartValues,
                barWidth: "35%",
                label: {
                    show: hasRuntime,
                    position: "top",
                    color: "#fff",
                    formatter: function (params) {
                        return safeNumber(params.value || 0, 1) + " ms";
                    }
                },
                itemStyle: {
                    borderRadius: [8, 8, 0, 0],
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: "#f8d44a" },
                        { offset: 1, color: "#ff7d42" }
                    ])
                }
            }]
        });
    }

    function renderTrendChart(trend) {
        var chart = getChart("trendChart");
        var items = trend && trend.length ? trend : [{
            label: "暂无数据",
            timestamp: "",
            filename: "",
            risk_score: 0,
            total_defects: 0
        }];
        chart.setOption({
            tooltip: {
                trigger: "axis",
                formatter: function (params) {
                    if (!params || !params.length) {
                        return "";
                    }
                    var item = items[params[0].dataIndex] || {};
                    return [
                        escapeHtml(item.label || ""),
                        item.filename ? "文件：" + escapeHtml(item.filename) : "",
                        "风险指数：" + safeNumber(item.risk_score || 0, 1),
                        "缺陷数量：" + safeNumber(item.total_defects || 0, 0)
                    ].filter(Boolean).join("<br/>");
                }
            },
            legend: {
                data: ["风险指数", "缺陷数量"],
                right: "center",
                top: 0,
                textStyle: { color: "#fff" }
            },
            grid: { left: "5%", right: "5%", top: "16%", bottom: "12%", containLabel: true },
            xAxis: {
                type: "category",
                data: items.map(function (item) {
                    return item.label || (item.image_index ? "第 " + item.image_index + " 张" : item.timestamp);
                }),
                axisLine: { lineStyle: { color: "rgba(255,255,255,.12)" } },
                axisLabel: { color: "rgba(255,255,255,.68)" }
            },
            yAxis: [{
                type: "value",
                axisLine: { show: false },
                splitLine: { lineStyle: { color: "rgba(255,255,255,.08)" } },
                axisLabel: { color: "rgba(255,255,255,.68)" }
            }, {
                type: "value",
                axisLine: { show: false },
                splitLine: { show: false },
                axisLabel: { color: "rgba(255,255,255,.68)" }
            }],
            series: [{
                name: "风险指数",
                type: "line",
                smooth: true,
                symbolSize: 8,
                data: items.map(function (item) { return item.risk_score; }),
                lineStyle: { width: 3, color: "#f8d34c" },
                itemStyle: { color: "#f8d34c" },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: "rgba(248,211,76,.35)" },
                        { offset: 1, color: "rgba(248,211,76,0)" }
                    ])
                }
            }, {
                name: "缺陷数量",
                type: "line",
                smooth: true,
                yAxisIndex: 1,
                symbolSize: 8,
                data: items.map(function (item) { return item.total_defects; }),
                lineStyle: { width: 3, color: "#46d6ff" },
                itemStyle: { color: "#46d6ff" },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: "rgba(70,214,255,.24)" },
                        { offset: 1, color: "rgba(70,214,255,0)" }
                    ])
                }
            }]
        });
    }

    function renderDefectTypeChart(items) {
        var chart = getChart("defectTypeChart");
        var data = items && items.length ? items : [{ name: "暂无数据", value: 0 }];
        chart.setOption({
            tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
            legend: {
                bottom: 0,
                textStyle: { color: "rgba(255,255,255,.72)" }
            },
            color: ["#f5d44a", "#ef5b63", "#35d48f", "#4d9fff"],
            series: [{
                type: "pie",
                radius: ["36%", "68%"],
                center: ["50%", "46%"],
                roseType: "radius",
                label: {
                    color: "#fff",
                    formatter: "{b}\n{c}"
                },
                labelLine: {
                    lineStyle: { color: "rgba(255,255,255,.4)" }
                },
                data: data
            }]
        });
    }

    function renderSeverityChart(items) {
        var chart = getChart("severityChart");
        var data = items && items.length ? items : [
            { name: "低", value: 0 },
            { name: "中", value: 0 },
            { name: "高", value: 0 }
        ];
        var total = data.reduce(function (sum, item) { return sum + Number(item.value || 0); }, 0);
        chart.setOption({
            title: {
                text: String(total),
                subtext: "缺陷总数",
                left: "center",
                top: "38%",
                textStyle: { color: "#fff", fontSize: 24 },
                subtextStyle: { color: "rgba(255,255,255,.65)", fontSize: 14 }
            },
            tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
            color: ["#49d98f", "#f5d44a", "#f0626b"],
            series: [{
                type: "pie",
                radius: ["48%", "70%"],
                center: ["50%", "50%"],
                label: {
                    color: "#fff",
                    formatter: "{b}\n{c}"
                },
                labelLine: {
                    lineStyle: { color: "rgba(255,255,255,.35)" }
                },
                data: data
            }]
        });
    }

    function renderCharts(chartsPayload) {
        renderPanelRanking(chartsPayload.panel_ranking || []);
        renderRuntimeChart(chartsPayload.runtime || {});
        renderTrendChart(chartsPayload.trend || []);
        renderDefectTypeChart(chartsPayload.defect_types || []);
        renderSeverityChart(chartsPayload.severity || []);
    }

    function renderDashboard(payload) {
        var status = payload.status || {};
        var overview = payload.overview || {};
        updateConnectionState(true, "已连接");
        renderOverview(overview, status);
        renderModels(status, overview);
        renderSamples(payload.samples || []);
        renderPreview(overview);
        renderRecentRecords(payload.recent_records || []);
        renderRecommendations(payload.recommendations || []);
        renderCharts(payload.charts || {});
    }

    async function fetchDashboard() {
        try {
            var response = await fetch(apiUrl("/api/dashboard"));
            if (!response.ok) {
                throw new Error("dashboard request failed");
            }
            var data = await response.json();
            renderDashboard(data);
        } catch (error) {
            updateConnectionState(false, "无法访问");
            setHint("仪表盘加载失败，请确认后端 Flask 服务已启动。", true);
            if (API_BASE) {
                setAnalysisNote("当前页面正在尝试访问 " + API_BASE + "。如果地址不对，可在 URL 后追加 ?api=http://实际后端地址:5000 覆盖默认值。", true);
            } else {
                setAnalysisNote("页面已从 Flask 打开，但接口仍失败，请检查后端是否异常退出。", true);
            }
        }
    }

    async function analyzeImage() {
        if (!selectedFiles.length) {
            setHint("请先选择一张或多张待分析的光伏板图像。", true);
            return;
        }

        var files = selectedFiles.slice();
        var button = $("#analyzeButton");
        button.prop("disabled", true).text("分析中...");
        setHint("已进入批量分析队列，后端会按选择顺序逐张分析。", false);

        try {
            for (var index = 0; index < files.length; index += 1) {
                var file = files[index];
                var progressText = files.length > 1 ? "第 " + (index + 1) + " / " + files.length + " 张" : "当前图像";
                updateUploadState("分析中 " + progressText, "#f8d44a");
                setAnalysisNote("正在上传并分析 " + progressText + "：" + file.name, false);

                var formData = new FormData();
                formData.append("image", file);
                var response = await fetch(apiUrl("/api/analyze"), {
                    method: "POST",
                    body: formData
                });

                var data = await response.json();
                if (!response.ok) {
                    throw new Error((data.error || "分析失败") + "：" + file.name);
                }

                renderDashboard(data.dashboard);
                if (data.analysis && data.analysis.result && data.analysis.result.summary) {
                    var summary = data.analysis.result.summary;
                    setAnalysisNote(
                        "完成 " +
                            progressText +
                            "：" +
                            file.name +
                            "。识别到 " +
                            (summary.total_defects || 0) +
                            " 个缺陷，异常组件 " +
                            (summary.dirty_panels || 0) +
                            " 个，风险 " +
                            Math.round(Number(summary.risk_score || 0)) +
                            " 分。",
                        false
                    );
                }
            }

            updateUploadState(files.length > 1 ? "批量完成" : "分析成功", "#9df0b0");
            setHint("分析完成：已累计 " + files.length + " 张图像到巡检趋势和最近记录。", false);
        } catch (error) {
            updateUploadState("分析失败", "#ff9d9d");
            setHint("分析失败：" + error.message, true);
            setAnalysisNote("批量分析中断：" + error.message, true);
        } finally {
            button.prop("disabled", false).text("开始分析");
        }
    }

    async function analyzeSample(sampleId) {
        var sample = sampleRegistry[sampleId];
        if (!sample || !sample.ready) {
            setHint("该示例样本当前不可用。", true);
            return;
        }

        selectedFiles = [];
        $("#imageInput").val("");
        $("#analyzeButton").prop("disabled", true).text("分析中...");
        setHint("正在分析示例样本：" + sample.name, false);
        updateUploadState("示例分析中", "#f8d44a");
        setAnalysisNote("正在运行示例样本：" + sample.name, false);

        try {
            var response = await fetch(apiUrl("/api/analyze-sample/" + encodeURIComponent(sampleId)), {
                method: "POST"
            });
            var data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "示例分析失败");
            }

            renderDashboard(data.dashboard);
            updateUploadState("示例完成", "#9df0b0");
            setHint("示例分析完成：" + sample.name, false);
        } catch (error) {
            updateUploadState("示例失败", "#ff9d9d");
            setHint("示例分析失败：" + error.message, true);
            setAnalysisNote("示例分析失败：" + error.message, true);
        } finally {
            $("#analyzeButton").prop("disabled", false).text("开始分析");
        }
    }

    async function resetDashboard() {
        var button = $("#resetDashboardButton");
        button.prop("disabled", true).text("恢复中...");

        try {
            var response = await fetch(apiUrl("/api/reset"), {
                method: "POST"
            });
            var data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "重置失败");
            }

            selectedFiles = [];
            $("#imageInput").val("");
            $("#selectedFileName").text("未选择");
            updateUploadState("待上传", "#fff");
            renderDashboard(data);
            setHint(defaultHint, false);
            setAnalysisNote("页面已恢复默认状态，等待上传图片。", false);
        } catch (error) {
            setHint("恢复默认状态失败：" + error.message, true);
            setAnalysisNote("后端未能完成重置：" + error.message, true);
        } finally {
            button.prop("disabled", false).text("恢复默认状态");
        }
    }

    function bindEvents() {
        $("#imageInput").on("change", function (event) {
            selectedFiles = Array.prototype.slice.call(event.target.files || []);
            if (selectedFiles.length) {
                $("#selectedFileName").text(summarizeSelectedFiles(selectedFiles));
                updateUploadState("已选择，待上传", "#9df0b0");
                setHint("已选择 " + selectedFiles.length + " 张图像，点击“开始分析”后将按顺序逐张提交后端。", false);
                setAnalysisNote("本地预览显示第一张；批量分析结果会全部累计到巡检趋势。", false);
                $("#resultPreview").attr("src", URL.createObjectURL(selectedFiles[0])).show();
                $("#previewPlaceholder").hide();
            } else {
                $("#selectedFileName").text("未选择");
                updateUploadState("待上传", "#fff");
                setHint(defaultHint, false);
                setAnalysisNote("这里会显示本地预览、上传成功状态以及后端返回的检测摘要。", false);
            }
        });

        $("#analyzeButton").on("click", analyzeImage);
        $("#resetDashboardButton").on("click", resetDashboard);

        $("#sampleGrid").on("click", ".sample-card[data-sample-id]", function () {
            analyzeSample($(this).attr("data-sample-id"));
        });

        $(window).on("resize", function () {
            setRootFont();
            Object.keys(charts).forEach(function (key) {
                charts[key].resize();
            });
        });
    }

    $(function () {
        setRootFont();
        setClock();
        setInterval(setClock, 1000);
        updateConnectionState(false, "检查中");
        bindEvents();
        fetchDashboard();
    });
})();
