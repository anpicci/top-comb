#!/usr/bin/env python3
"""
Simple snippet to remake plots from CMGRDF json outputs.
"""
import sys
import argparse
import glob

sys.path.insert(0, __file__.rsplit("/", 2)[0])  # toplevel path
from utils import (
    get_logger,
    load_config,
    read_json_histograms,
)

from plotting import Plotter1D

logger = get_logger(__name__)


def get_legend_labels(stylings, histograms):
    labels = []
    for histkey, hist in histograms.items():
        if histkey in stylings['legend']:
            legend_name = stylings['legend'][histkey]["label"]
        else:
            legend_name = histkey
        labels.append(legend_name)
    return labels

def get_axes_customizations(stylings, histkey):
    if histkey in stylings['axes']:
        return stylings['axes'][histkey]
    return {}

def get_basic_annotations(stylings, region):
    annotations = [
        {"text": "__LUMI__ (__COM__)", "x0": .73, "y0": .963, "x1": .755, "y1": .99, "textsize": 22},
        {"text": r"#splitline{#scale[1.2]{#bf{CMS}}}{}", "x0": .2, "y0": .870, "x1": .35, "y1": .885, "textsize": 22},
        {"text": "__REGION_LABEL__", "x0": .2, "y0": .83, "x1": .35, "y1": .81, "textsize": 22},
    ]
    if "lumi" in stylings.get("annotations"):
        lumi_text = stylings["annotations"]["lumi"] or "XX.X fb^{-1}"
        com_text = stylings["annotations"]["com"] or "13 TeV"
        annotations[0]["text"] = annotations[0]["text"].replace("__LUMI__", str(lumi_text))
        annotations[0]["text"] = annotations[0]["text"].replace("__COM__", com_text)

    if "region_labels" in stylings.get("annotations"):
        if region in stylings.get("annotations").get("region_labels"):
            region_label = stylings["annotations"]["region_labels"][region] or ""
            annotations[2]["text"] = annotations[2]["text"].replace("__REGION_LABEL__", region_label)
    return annotations

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main parser for the top-comb.py script.")
    parser.add_argument("-s", "--style", default=None, type=str, help="Yaml file with style settings.")
    args = parser.parse_args()

    stylings = load_config(args.style)
    logistics = stylings.get("logistics", {})
    inpath = logistics.get("inpath")
    channels = logistics.get("channels")

    for ch in channels:
        jsonfiles = glob.glob(f"{inpath}/{ch}/*.json")
        for json_file in jsonfiles:
            plot_name = json_file.split("/")[-1].replace(".json", "")
            logger.info(f"Processing {json_file}...")
            histograms = read_json_histograms(json_file)

            labels = get_legend_labels(stylings, histograms)
            hist_list = list(histograms.values())

            custom_params = {
                **get_axes_customizations(stylings, plot_name),
                "annotations": [
                    *get_basic_annotations(stylings, ch)
                ],
            }

            Plotter1D.plot(
                outfolder=f"{inpath}/{ch}",
                name=plot_name,
                hists=hist_list,
                ratios=[],
                funcs=[],
                graphs=[],
                labels=labels,
                dict_customs=custom_params,
                spams=[],
            )
