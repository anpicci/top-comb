"""
plotting_tools
--------------

Plotting helper routines used by the `replot` workflow.

Notes
- prepare_stacks reads the 'grouping' section from the datasets YAML to
  decide which readers are combined into each stack. Unreferenced readers
  are treated as overlays.
- All functions assume ROOT is available and that readers expose a
  get_histo(rfile) method returning a ROOT.TH1-like object.
"""

import sys
from pathlib import Path

from copy import deepcopy
from utils import get_logger
from plotting import Plotter1D
from .loaders import load_module_from_path
from .readers import build_histogram_readers, load_histograms_for_readers


logger = get_logger(__name__)

from settings import TopCombSettings
settings = TopCombSettings().model_dump()
outpath = settings["topcomb_outpath"]


BASE_SPAMS = [
    {"text": "__LUMI__ (13.0 TeV)", "x0": .73, "y0": .963, "x1": .755, "y1": .99, "textsize": 22},
    {"text": r"#splitline{#scale[1.2]{#bf{CMS}}}{}", "x0": .2, "y0": .870, "x1": .35, "y1": .885, "textsize": 22},
    {"text": "__REGION_LABEL__", "x0": .2, "y0": .83, "x1": .35, "y1": .81, "textsize": 22},
    {"text": "__SUBREGION_LABEL__", "x0": .2, "y0": .75, "x1": .35, "y1": .77, "textsize": 22},
]

# ------------------------------------------------------------
# Histogram utilities
# ------------------------------------------------------------
def prepare_histograms(readers, rfile):
    """
    Prepare and return all histograms from the given readers.
    """
    histos = []
    labels = []
    for name, reader in readers.items():
        h = reader.get_histo(rfile)
        histos.append(h)
        labels.append(reader.get_label())
        
    return histos, labels

def get_ratio(num, den):
    """Safe ratio histogram: num / den."""
    num = num.Clone(f"{num.GetName()}_ratio")
    den = den.Clone(f"{den.GetName()}_ratio")

    num.SetDirectory(0)
    den.SetDirectory(0)

    # Remove denominator errors
    for i in range(1, den.GetNbinsX() + 1):
        den.SetBinError(i, 0)

    num.Divide(den)
    num.SetFillStyle(3444)

    return num

def write_yields(readers, rfile, outdir, plotname):
    """Write bin yields to a text file."""
    outfile = Path(outdir) / f"{plotname}_perBin.txt"
    with outfile.open("w") as f:
        for name, reader in readers.items():
            if name == "data":
                continue

            h = reader.get_histo(rfile)
            values = [
                f"{h.GetBinContent(i):8.2f} +/- {h.GetBinError(i):8.2f}"
                for i in range(1, h.GetNbinsX() + 1)
            ]

            f.write(f"{name:10s}\t" + "\t".join(values) + "\n")

        f.write("-" * 120 + "\n\n")


# ------------------------------------------------------------
# Replotting
# ------------------------------------------------------------
def replot( analysis_name, metadata ):
    """Regenerate all plots."""

    reinterpret_meta = metadata["reinterpretation"]

    readers = build_histogram_readers(reinterpret_meta["samples"]["datasets"])
    outbase = Path( outpath )

    flowmeta = reinterpret_meta["flow"]
    flowname = flowmeta["name"]

    # Collect plot targets
    plot_targets = []
    for target in flowmeta["targets"]:
        if target["type"] != "plots":
            continue

        plots_module = load_module_from_path("plots", target["plotfile"])
        pm = target["plotmodule"]

        if isinstance(pm, list):
            for m in pm:
                plot_targets.extend(getattr(plots_module, m))
        else:
            plot_targets.extend(getattr(plots_module, pm))

    # Process each subflow
    for sub in flowmeta["subflows"]:
        subname = sub["name"]
        subflow_label = sub['label'] 
        subflow_sublabel = sub['sublabel']

        inpath = outbase / f"{analysis_name}/{flowname}/{subname}"
        logger.info(f"Remaking plots in {inpath}")

        if not inpath.exists():
            logger.warning(f"Folder {inpath} missing; skipped.")
            continue

        for plotcfg in plot_targets:
            rfile = inpath / f"{plotcfg.name}.root"

            if not rfile.exists():
                logger.warning(f"Missing: {rfile}")
                continue

            current = load_histograms_for_readers(dict(readers), str(rfile))
            all_histos, labels = prepare_histograms(current, str(rfile))
            den = all_histos[0].Clone("den_ratio")
            ratio_total = get_ratio(den, den)
            ratio_overlays = [get_ratio(h, den) for h in all_histos]

            spams = []
            for spam in BASE_SPAMS:
                temp_spam = deepcopy(spam)
                temp_spam["text"] = temp_spam["text"]\
                    .replace("__REGION_LABEL__", subflow_label)\
                    .replace("__SUBREGION_LABEL__", subflow_sublabel)\
                    .replace("__LUMI__", "138.0")
                spams.append( temp_spam )

            # Convert the attributes of plotcfg into a dictionary 
            # so that it can be parsed into the auxiliar plotter.
            custom_params = {
                "xTitle" : getattr(plotcfg, "xTitle", ""),
                "yTitle" : getattr(plotcfg, "yTitle", ""),
                "logy"   : getattr(plotcfg, "logy", False),
                "annotations" : getattr(plotcfg, "annotations", []),
                "lines"  : getattr(plotcfg, "lines", []),
                "xBinLabels" : getattr(plotcfg, "xBinLabels", []),
            }

            Plotter1D.plot(
                outfolder = inpath,
                name = plotcfg.name,
                hists = all_histos,
                ratios = [ ratio_total ] + ratio_overlays,
                funcs = [],
                graphs = [],
                labels = labels,
                dict_customs = custom_params,
                spams = spams,
            )

            write_yields(current, str(rfile), inpath, plotcfg.name)

    logger.info("Plots regenerated.")

if __name__ == "__main__":
    sys.argv.insert( 0, "../" )
    replot( "configs/ttgamma.yaml" )