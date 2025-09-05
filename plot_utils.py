import copy

import numpy as np
import matplotlib.pyplot as plt


def draw_pie(
        values,
        labels,
        ax=None,
        title=None,
        colors_map=None,
        autopct_threshold=0.05,
        startangle=90,
        counterclock=False,
        pctdistance=0.72,
        radius=1,
        inner_radius=0.5,
        label_radius=1.2,
        label_line_radius=1,
        label_vertical_aligned=True,
        label_horizontal_distance=0.3,
        label_ensure_gap=0,
        text_fontsize=9,
        show=True,
        **kwargs):
    
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

    color_cycle = plt.rcParams['axes.prop_cycle'].by_key().get('color', [])
    cmap = dict(colors_map or {})
    for i, k in enumerate(labels):
        if k not in cmap:
            cmap[k] = color_cycle[i % len(color_cycle)] if color_cycle else '#aaaaaa'

    wedges, texts, autotexts = ax.pie(
        values,
        colors=[cmap[k] for k in labels],
        autopct=lambda p: f'{p:.1f}%' if p >= (autopct_threshold * 100) else '',
        startangle=startangle,
        counterclock=counterclock,
        pctdistance=pctdistance,
        radius=radius,
        textprops={'fontsize': text_fontsize},
        wedgeprops={'width': 1 - inner_radius},
        **kwargs
    )

    line_height = abs(
        ax.transData.inverted().transform((0, text_fontsize * ax.figure.dpi / 72.0))[1] -
        ax.transData.inverted().transform((0, 0))[1]
    )

    kw = dict(arrowprops=dict(arrowstyle="-"), zorder=0, va="center")

    wedge_lable_locs = []

    for i, p in enumerate(wedges):
        l = {'label': labels[i]}
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        l['y'] = label_line_radius * np.sin(np.deg2rad(ang))
        l['x'] = label_line_radius * np.cos(np.deg2rad(ang))
        l['tx'] = label_radius * (
            np.sign(l['x']) if label_vertical_aligned else l['x']) + label_horizontal_distance * np.sign(l['x'])
        l['ty'] = label_radius * l['y']
        l['th'] = len(labels[i].splitlines()) * line_height
        right = np.sign(l['x']) >= 0
        l['horizontalalignment'] = "right" if right else "left"
        lkw = copy.deepcopy(kw)
        lkw["arrowprops"].update({"connectionstyle": f"angle,angleA=0,angleB={ang}"})
        # lkw["arrowprops"].update({"connectionstyle": f"arc,angleA={180 if right else 0},angleB={ang},armA=30,armB=30"})
        # lkw["arrowprops"].update({"connectionstyle": f"bar,angle={-90 if right else 90},fraction=-0.3"})
        l['kw'] = lkw
        wedge_lable_locs.append(l)

    # iterate over all labels and adjust their positioning to avoid collisions

    def adjust_quarter(items, direction=1, gap=0.08):
        if not items:
            return
        # Adjust each quarter starting from the center
        items.sort(key=lambda d: d['ty'], reverse=(direction < 0))

        last_item_border = 0
        for i in items:
            cur_h2 = (gap + i['th']) / 2.
            # assume vertical centering of the label
            min_pos = last_item_border + cur_h2

            if i['ty'] * direction < min_pos:
                i['ty'] = min_pos * direction

            last_item_border = (i['ty'] * direction) + cur_h2

    def adjust_half(items, gap=label_ensure_gap):
        upper = [l for l in items if l['ty'] >= 0]
        lower = [l for l in items if l['ty'] < 0]
        adjust_quarter(upper, 1, gap=gap)
        adjust_quarter(lower, -1, gap=gap)

    left = [l for l in wedge_lable_locs if l['tx'] < 0]
    right = [l for l in wedge_lable_locs if l['tx'] >= 0]
    adjust_half(left)
    adjust_half(right)

    for l in wedge_lable_locs:
        ax.annotate(l['label'], xy=(l['x'], l['y']), xytext=(l['tx'], l['ty']),
                    horizontalalignment=l['horizontalalignment'], **l['kw'])

    if title:
        ax.set_title(title)
    
    if show:
        plt.show()
    
    return ax
