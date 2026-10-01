import math


from decidebench.charts import frontier_scatter

SUMM = {"tev": {"cost_task": 1e-5, "p50": 173.0, "acc": 0.90},
        "jev": {"cost_task": 2e-5, "p50": 459.0, "acc": 0.972},
        "arize-qwen2": {"cost_task": 8.1e-4, "p50": 2883.0, "acc": 0.99},
        "llama-70b-self": {"cost_task": 1.7e-3, "p50": 2477.0, "acc": 0.992},
        "random": {"cost_task": 0.0, "p50": 0.0, "acc": 0.45}}


def test_latency_scatter_draws_frontier_through_undominated_points_only():
    html, h = frontier_scatter("latency-vs-accuracy", "Latency vs accuracy", SUMM, {"tev", "jev", "llama-70b-self", "random"},
                               lambda v: v["p50"], "Median latency per call (log scale)", 100, 10000,
                               (100, 1000, 10000), lambda ms: f"{ms:,} ms", lambda ms: f"{ms:,.0f} ms")
    assert html.count("<polyline") == 1
    assert "Random 45.0%" in html
    assert h > 0 and "<svg" in html


def test_label_placement_avoids_overlaps_and_stays_on_canvas():
    from decidebench.charts import label_boxes, place_labels

    points = {"a": (700, 152), "b": (712, 160), "c": (690, 168), "d": (730, 150), "e": (705, 180),
              "f": (760, 158), "g": (820, 172)}
    texts = {p: (f"Model {p.upper()} name", "", 13) for p in points}
    bounds = (0, 76, 880, 500)
    placed = place_labels(points, texts, preferred={}, bounds=bounds)
    boxes = label_boxes(points, texts, placed)
    names = list(boxes)
    for i, p in enumerate(names):
        x0, y0, x1, y1 = boxes[p]
        assert bounds[0] <= x0 and x1 <= bounds[2] and bounds[1] <= y0 and y1 <= bounds[3], p
        for q in names[i + 1:]:
            u0, v0, u1, v1 = boxes[q]
            assert x1 <= u0 or u1 <= x0 or y1 <= v0 or v1 <= y0, (p, q)


def test_crowded_scatter_labels_every_point():
    from decidebench.charts import frontier_scatter

    summ = {"tev": {"cost_task": 1e-5, "p50": 175.0, "acc": 0.90}, "jev": {"cost_task": 2e-5, "p50": 459.0, "acc": 0.9725},
            "deepseek": {"cost_task": 6.9e-5, "p50": 2501.0, "acc": 0.985},
            "glm-flash": {"cost_task": 7.2e-5, "p50": 615.0, "acc": 0.985},
            "gpt-oss-120b-self": {"cost_task": 1.04e-4, "p50": 1045.0, "acc": 0.98},
            "deepseek-41": {"cost_task": 1.72e-4, "p50": 404.0, "acc": 0.985},
            "tev-together": {"cost_task": 7.82e-4, "p50": 841.0, "acc": 0.9925},
            "arize-qwen2": {"cost_task": 8.09e-4, "p50": 2883.0, "acc": 0.99}, "llama-70b-self": {"cost_task": 1.7e-3, "p50": 2477.0, "acc": 0.9925}}
    html, _ = frontier_scatter("c", "t", summ, {"tev", "jev"}, lambda v: v["cost_task"] * 1e6, "Cost (log scale)", 5, 5000,
                               (10, 100, 1000), str, str)
    for name in ("TEV (self-hosted)", "JEV", "DeepSeek-V4-Flash", "GLM-5.3-Flash", "gpt-oss-120b (self-hosted)", "DeepSeek-V4.1-Flash",
                 "TEV (Together)", "Qwen2-1.5B (Arize)", "Llama-3.3-70B (self-hosted)"):
        assert f">{name}</text>" in html, name


def test_entries_below_the_accuracy_axis_are_listed_not_drawn():
    from decidebench.charts import frontier_scatter

    summ = {"tev": {"cost_task": 1e-5, "p50": 175.0, "acc": 0.90},
            "arize-qwen2": {"cost_task": 2.4e-5, "p50": 198.0, "acc": 0.52}}
    html, _ = frontier_scatter("c", "t", summ, {"tev"}, lambda v: v["cost_task"] * 1e6, "Cost (log scale)", 5, 5000,
                               (10, 100, 1000), str, str)
    assert html.count("<circle") == 2
    assert "Below the 85% axis: Qwen2-1.5B (Arize) 52.0%." in html


def test_entries_below_the_axis_are_listed_by_accuracy():
    from decidebench.charts import frontier_scatter

    summ = {"tev": {"cost_task": 1e-5, "p50": 175.0, "acc": 0.90},
            "julia-1": {"cost_task": 3e-6, "p50": 58.0, "acc": 0.35},
            "jeff-800m": {"cost_task": 1e-5, "p50": 43.0, "acc": 0.71},
            "jeff-gemma4": {"cost_task": 1.6e-5, "p50": 76.0, "acc": 0.81}}
    html, _ = frontier_scatter("c", "t", summ, {"tev"}, lambda v: v["cost_task"] * 1e6, "Cost (log scale)", 1, 5000,
                               (10, 100, 1000), str, str)
    assert "Below the 85% axis: Jeff-Gemma4 81.0%, Jeff-0.8B 71.0%, Julia-1 35.0%." in html


def test_labels_avoid_obstacles_such_as_the_frontier_line():
    from decidebench.charts import label_boxes, place_labels

    points = {"a": (400, 200)}
    texts = {"a": ("Some label", "", 13)}
    line = [(x, 204, x + 4, 208) for x in range(300, 600, 4)]
    placed = place_labels(points, texts, preferred={}, bounds=(0, 0, 880, 500), obstacles=line)
    box = label_boxes(points, texts, placed)["a"]
    assert not any(box[0] < o[2] and o[0] < box[2] and box[1] < o[3] and o[1] < box[3] for o in line)


def test_label_boxes_are_padded():
    from decidebench.charts import label_boxes

    (x0, _, x1, _) = label_boxes({"a": (100, 100)}, {"a": ("MiniMax-M3", "", 13)}, {"a": (12, 4, "start")})["a"]
    assert x1 - x0 >= len("MiniMax-M3") * 13 * 0.62 + 8


def test_latency_view_hides_entries_timed_on_local_hardware():
    import math

    from decidebench.charts import latency_view

    summ = {"jev": {"p50": 175.0, "acc": 0.9}, "clm": {"p50": 50.0, "acc": 0.95}}
    view = latency_view(summ)
    assert view["jev"]["p50"] == 175.0 and math.isnan(view["clm"]["p50"])
    assert summ["clm"]["p50"] == 50.0


def test_footer_notes_wrap_to_one_line_each():
    import re

    from decidebench.charts import W, frontier_scatter

    summ = {"tev": {"cost_task": 1e-5, "p50": 175.0, "acc": 0.90},
            "arize-qwen2": {"cost_task": 2.4e-5, "p50": 198.0, "acc": 0.52},
            "clm": {"cost_task": float("nan"), "p50": 192.0, "acc": 0.40},
            "qwen3-8b": {"cost_task": float("nan"), "p50": 771.0, "acc": 0.85},
            "random": {"cost_task": 0.0, "p50": 0.0, "acc": 0.22}}
    html, h = frontier_scatter("c", "t", summ, {"tev"}, lambda v: v["cost_task"] * 1e6, "Cost (log scale)", 5, 5000,
                               (10, 100, 1000), str, str)
    footer = [m for m in re.findall(r'>([^<]*)</text>', html) if m.startswith(("Off scale", "Below", "Not plotted", "Dashed"))]
    assert len(footer) >= 3
    assert all(112 + len(line) * 12 * 0.52 <= W for line in footer), footer
    assert h > 528 - 76


def test_long_footer_notes_wrap_within_the_canvas():
    import re

    from decidebench.charts import W, frontier_scatter

    nan = float("nan")
    summ = {"jev": {"cost_task": 2e-5, "p50": 459.0, "acc": 0.97}}
    summ |= {p: {"cost_task": 1e-4, "p50": nan, "acc": 0.9} for p in ("tev", "clm", "laya-typed", "decider-2b", "kev-4b", "qwen3-8b")}
    html, _ = frontier_scatter("l", "t", summ, {"jev"}, lambda v: v["p50"], "Latency (log scale)", 100, 10000,
                               (100, 1000, 10000), str, str)
    lines = [m for m in re.findall(r'<text x="112"[^>]*>([^<]*)</text>', html) if not m.isdigit()]
    assert all(112 + len(line) * 12 * 0.55 <= W - 16 for line in lines), lines
    joined = " ".join(lines)
    for name in ("TEV (self-hosted)", "CLM-v0.1-8B", "Laya typed-decisions", "Decider-2B", "Kev-4B", "Qwen3-8B"):
        assert name in joined, name


def _segment_hits_box(a, b, box, steps=40):
    return any(box[0] < a[0] + (b[0] - a[0]) * t / steps < box[2] and box[1] < a[1] + (b[1] - a[1]) * t / steps < box[3]
               for t in range(steps + 1))


CROWD = {"jev": (304, 172), "tev": (412, 276), "arize-qwen2": (724, 144), "deepseek": (492, 140),
         "glm-flash": (488, 152), "gpt-oss-120b-self": (512, 188), "deepseek-41": (576, 152), "tev-together": (720, 156),
         "llama-70b-self": (680, 212), "qwen3-8b": (432, 320)}


def _merged(crowd, sub="98.0% · $32"):
    from decidebench.charts import SHORT, merge_close, short

    points, names = merge_close(crowd, {p: SHORT.get(p) or short(p) for p in crowd}, keep=("jev", "tev"))
    return points, {p: (names[p], sub, 16) if p in ("jev", "tev") else (names[p], "", 13) for p in points}


def test_merge_close_stacks_near_coincident_names_top_to_bottom():
    from decidebench.charts import merge_close

    points, names = merge_close({"a": (100, 110), "b": (104, 102), "c": (300, 100), "jev": (106, 104)},
                                {"a": "A", "b": "B", "c": "C", "jev": "JEV"}, keep=("jev",))
    assert names == {"b": "B\nA", "c": "C", "jev": "JEV"}
    assert points["b"] == (102, 106) and points["c"] == (300, 100)


def test_labels_keep_clear_of_other_points():
    from decidebench.charts import PLACE, label_boxes, place_labels

    crowd, texts = _merged(CROWD)
    boxes = label_boxes(crowd, texts, place_labels(crowd, texts, preferred=PLACE, bounds=(8, 84, 872, 456)))
    for p, box in boxes.items():
        for q, (x, y) in crowd.items():
            if q != p:
                assert not (box[0] - 6 < x < box[2] + 6 and box[1] - 6 < y < box[3] + 6), (p, q)


def test_leaders_do_not_cross_other_labels():
    from decidebench.charts import PLACE, label_boxes, leader, place_labels

    crowd, texts = _merged(CROWD)
    placed = place_labels(crowd, texts, preferred=PLACE, bounds=(8, 84, 872, 456))
    boxes = label_boxes(crowd, texts, placed)
    for p, (x, y) in crowd.items():
        end = leader(x, y, placed[p], boxes[p])
        if end is None:
            continue
        for q, box in boxes.items():
            if q != p:
                assert not _segment_hits_box((x, y), end, box), (p, q)


def _gap(box, x, y):
    return math.hypot(max(box[0] - x, 0, x - box[2]), max(box[1] - y, 0, y - box[3]))


LATENCY_CROWD = {"jev": (408, 172), "arize-qwen2": (640, 144), "deepseek": (564, 140),
                 "glm-flash": (404, 152), "gpt-oss-120b-self": (392, 188), "deepseek-41": (308, 152),
                 "tev-together": (408, 156), "llama-70b-self": (408, 212),}


def test_labels_without_a_leader_sit_nearer_their_own_point_than_any_other():
    from decidebench.charts import PLACE, label_boxes, leader, place_labels

    for crowd, texts in (_merged(CROWD), _merged(LATENCY_CROWD, "98.0% · 678 ms")):
        placed = place_labels(crowd, texts, preferred=PLACE, bounds=(8, 84, 872, 456))
        boxes = label_boxes(crowd, texts, placed)
        for p, box in boxes.items():
            own = _gap(box, *crowd[p])
            assert own <= 100, (p, own)
            if leader(*crowd[p], placed[p], box) is not None:
                continue
            for q, (x, y) in crowd.items():
                if q != p:
                    assert own < _gap(box, x, y), (p, q)


def test_a_label_is_clearly_nearer_its_own_point_than_a_neighbours():
    from decidebench.charts import PLACE, label_boxes, leader, place_labels

    crowd = {"deepseek": (564, 140), "deepseek-41": (308, 152), "glm-flash": (404, 152), "jev": (400, 172),
             "tev-together": (216, 272)}
    texts = {p: (n, "", 13) for p, n in (("deepseek", "DeepSeek-V4-Flash"), ("deepseek-41", "DeepSeek-V4.1-Flash"),
                                          ("glm-flash", "GLM-5.3-Flash"), ("tev-together", "TEV (Together)"))}
    texts["jev"] = ("JEV", "98.0% · 639 ms", 16)
    placed = place_labels(crowd, texts, preferred=PLACE, bounds=(8, 84, 872, 456))
    boxes = label_boxes(crowd, texts, placed)
    for p, box in boxes.items():
        if leader(*crowd[p], placed[p], box) is not None:
            continue
        own = _gap(box, *crowd[p])
        for q, (x, y) in crowd.items():
            if q != p:
                assert _gap(box, x, y) >= own + 8, (p, q)
