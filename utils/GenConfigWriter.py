import os
import re
import json
import random
import numpy as np
from copy import deepcopy
from datetime import datetime

import utils.auxiliars as aux


class GenConfigWriter:
    """Class for reading metadata and writing gen configuration files such as cards, fragments, etc."""

    def __init__(self, name):
        self.name = name

    def setup(self, settings, metadata, operators_meta, outdir):
        """Initialize and prepare all configuration files."""
        mgcards_dir = os.path.join(outdir, "mgcards")
        aux.create_dir(mgcards_dir)

        # Related to MG cards
        self.prepare_proc_card(metadata, mgcards_dir)
        self.prepare_run_card(settings, metadata, mgcards_dir)
        self.prepare_extramodels(metadata, mgcards_dir)
        operators = aux.get_operators(operators_meta)
        self.prepare_restrict_card(settings, metadata, mgcards_dir, operators)
        self.prepare_reweightcards(settings, metadata, mgcards_dir, operators, operators_meta["algo"])

        # Fragment
        self.prepare_fragment( settings, metadata, outdir )

        # Scripts
        self.prepare_submission_nanogen_file(settings, metadata, outdir)
        self.create_gridpack_submit( settings, metadata, outdir )

    @staticmethod
    def write_text(outfile: str, text: str):
        """Write text to a file."""
        with open(outfile, "w") as out:
            out.write(text)

    # -------------------------------------------------------------------------
    # Madgraph card preparation methods
    # -------------------------------------------------------------------------
    def prepare_proc_card(self, metadata, outdir):
        """Prepare the process card from metadata."""
        procname = metadata["procname"]
        full_card = [
            f"import model {metadata['model']}",
            "",
            *metadata["process"],
            "",
            f"output {procname} -nojpeg",
        ]
        self.write_text(os.path.join(outdir, f"{procname}_proc_card.dat"), "\n".join(full_card))

    def prepare_extramodels(self, metadata, outdir):
        """Prepare the extramodels card."""
        procname = metadata["procname"]
        modelname = metadata["load_extramodels"]
        self.write_text(os.path.join(outdir, f"{procname}_extramodels.dat"), modelname)

    def prepare_run_card(self, settings, metadata, outdir):
        """Prepare the run card from a template."""
        procname = metadata["procname"]
        template_name = metadata["template_run_card"]["name"]
        text = aux.open_template(settings, template_name)
        self.write_text(os.path.join(outdir, f"{procname}_run_card.dat"), text)

    def prepare_restrict_card(self, settings, metadata, outdir, operators):
        """Prepare the restrict card, modifying EFT operator values."""
        procname = metadata["procname"]
        template_name = metadata["template_restrict_card"]["name"]
        restrict_name = metadata["template_restrict_card"]["restrict_name"]
        text = aux.open_template(settings, template_name)

        val = 0.1
        if operators:
            for op in np.array(operators)[:, 0]:
                match = re.search(f"(.*{op}.*)", text)
                if match:
                    line = match.group(0)
                    new_val = f"{val:3.6f}e-01"
                    text = text.replace(line, line.replace("0.000000e+00", new_val))
                    val += 0.1
                    if val == 1.0:  # MadGraph bug workaround
                        val += 0.1

        outfile = os.path.join(outdir, f"{procname}_restrict_{restrict_name}.dat")
        self.write_text(outfile, text)

    def prepare_customizecards(self, settings, metadata, outdir, operators):
        """Prepare the customizecards file."""
        procname = metadata["procname"]
        template_name = metadata["template_customizecards"]["name"]
        extra_opts = metadata["template_customizecards"]["extraopts"]

        text = aux.open_template(settings, template_name)
        text += "\n\n# EFT operators\n"

        # EFT operator values
        for op in np.array(operators)[:, 0] if operators else []:
            val = random.uniform(-0.999999, 0.999999)
            val = val if val != 0.0 else random.uniform(-0.999999, 0.999999)
            text += f"set param_card {op} {val}\n"

        # User options
        if extra_opts:
            text += "\n\n# User settings\n"
            text += "\n".join(extra_opts)

        outfile = os.path.join(outdir, f"{procname}_customizecards.dat")
        self.write_text(outfile, text)

    def prepare_reweightcards(self, settings, metadata, outdir, operators, algorithm):
        """Prepare the reweight card and a markdown mapping."""
        procname = metadata["procname"]
        date_str = datetime.now().strftime("%A %d. %B %Y")

        # Header
        text = (
            f"# Reweight card created on {date_str}\n"
            "change rwgt_dir rwgt\n"
            "launch --rwgt_name=dummy # Dummy to initialize rwgt_1.\n\n"
        )

        # Reweight points
        rwgt_points = []
        for algo in algorithm.split("-"):
            rwgt_points += aux.get_rwgt_points(algo, operators)

        if rwgt_points:
            sm = deepcopy(rwgt_points[-1])
            sm[:, 1] = "0.0"
            rwgt_points.append(sm)

        # Build reweight card
        for rwgt_point in rwgt_points:
            rwgt_name = aux.get_rwgt_name(rwgt_point)
            text += f"launch --rwgt_name={rwgt_name}\n"
            for param, value in rwgt_point:
                text += f"set {param} {float(value):3.4f}\n"
            text += "\n"

        rwgt_outfile = os.path.join(outdir, f"{procname}_reweight_card.dat")
        self.write_text(rwgt_outfile, text)

        # Markdown summary
        operator_names = [op[0] for op in operators]
        md_lines = [
            f"# Configuration card created on {date_str}",
            "Below is a mapping showing the reweighting points found in the NanoAOD.",
            "Note: only non-zero couplings are shown.",
            f"The full list of couplings considered: {operator_names}.",
            "",
            "| Coupling values | Index in LHEReweightWeight |",
            "| :--------------- | :-------------------------- |",
        ]

        for idx, rwgt_point in enumerate(rwgt_points):
            nonzero = [f"{p}={v}" for p, v in rwgt_point if float(v) != 0.0]
            line = "SM" if not nonzero else ", ".join(nonzero)
            md_lines.append(f"| {line} | {idx} |")

        md_text = "\n".join(md_lines)
        mddir = os.path.dirname(outdir)
        self.write_text(os.path.join(mddir, "README.md"), md_text)

    # -------------------------------------------------------------------------
    # Fragment & submission configuration
    # -------------------------------------------------------------------------
    def prepare_fragment( self, settings, metadata, outdir ):
        """Modify a PS template and save it to the analysis folder."""
        procname = metadata["procname"]
        fragment_meta = metadata["fragment"]

        text = aux.open_template( settings, fragment_meta["name"])

        gridpacks_base = os.path.join(settings.get("topcomb_outpath"), self.name, procname)
        gridpack_path = os.path.join(gridpacks_base, "gridpack", f"{procname}.tar.xz")

        params = ["# Process specific settings"] + fragment_meta["process_parameters"]
        placeholder_match = re.search(r"^(?P<indent>\s*)\{PROCESS_PARAMETERS\}", text, flags=re.MULTILINE)
        indent = placeholder_match.group("indent") if placeholder_match else ""
        formatted_params = (",\n" + indent).join(params)

        text = text.format(GRIDPACK=gridpack_path, PROCESS_PARAMETERS=formatted_params)
        self.write_text(os.path.join(outdir, "fragment.py"), text)

    def prepare_submission_nanogen_file(self, settings, metadata, outdir):
        """Prepare a configuration file for tmg-tools/top-gendqm."""
        procname = metadata["procname"]
        topcomb_out = settings.get("topcomb_outpath")

        data = {
            "mode": "nanogen",
            "processes": {procname: f"file:{outdir}/fragment.py"},
            "nevents": {procname: 1e6},
            "memory": {procname: 32000},
            "njobs": {procname: 5000},
            "xsec": {procname: 1},
            "isGS": {procname: 0},
            "campaign": "RunIISummer20UL18",
            "outpath": os.path.join(topcomb_out, f"{self.name}/{procname}/nanogen/"),
            "submit_dir": f"submit_nanogen_{procname}",
            "tag": procname,
            "routines": [],
        }

        with open(os.path.join(outdir, "nanogen_config.json"), "w") as outfile:
            json.dump(data, outfile, indent=4)

    def create_gridpack_submit( self, settings, metadata, outdir ):
        procname = metadata["procname"]

        # Edit the bash script
        bash_text = aux.open_template( settings, f"{settings.get('topcomb_mainpath')}/templates/run_gridpack_batch.sh" )
        substitutions = {
            "__PROCNAME__": procname,
            "__ANALYSIS_NAME__": self.name,
            "__OUTPATH__": settings.get("topcomb_outpath"),
            "__SINGULARITY_IMAGE__": settings.get("singularity_image_gridpack"),
            "__GENPRODUCTIONS_GRIDPACK__": settings.get("genproductions_gridpack"),
            "__BRANCH_GRIDPACK__": settings.get("branch_gridpack"),
        }

        for key, val in substitutions.items():
            bash_text = bash_text.replace(key, val)
 

        outfile = os.path.join(outdir, f"run_gridpack_batch.sh")
        self.write_text(outfile, bash_text)

        # Edit the JDS script
        jds_text = aux.open_template( settings, f"{settings.get('topcomb_mainpath')}/templates/template_submit.jds" )
        substitutions = {
            "__SCRIPTNAME__" : "run_gridpack_batch.sh",
            "__PROCNAME__" : f"{procname}_runGridpack",
            "__NCORES__" : "8"
        }
        for key, val in substitutions.items():
            jds_text = jds_text.replace(key, val)

        outfile = os.path.join(outdir, f"run_gridpack_batch.jds")
        self.write_text(outfile, jds_text)
