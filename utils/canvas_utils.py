# Simple macros to create canvases and for plotting stuff
import ROOT as r
from copy import deepcopy
import numpy as np

def new_1d_canvas( name, plot ):
    """ Creates a template canvas """

    x_size = 600
    y_size = 600
    if getattr( plot, "do_superwide", False ):
        x_size = 1200

    # --------------- Prepare the basic canvas
    c = r.TCanvas(name, "",  x_size, y_size)
    topSpamSize     = 1.1
    c.SetTopMargin(c.GetTopMargin() * topSpamSize)
    c.Divide(1,2)
    
    # --- First pad
    p1 = c.GetPad(1)
    p1.SetPad(0, 0.25, 1, 1)
    p1.SetTopMargin(0.055)
    p1.SetBottomMargin(0.025)
    p1.SetLeftMargin(0.16)
    p1.SetRightMargin(0.03)

    # --- Second pad
    p2 = c.GetPad(2)
    p2.SetPad(0, 0, 1, 0.25)
    p2.SetTopMargin(0.06)
    p2.SetBottomMargin(0.42)
    p2.SetLeftMargin(0.16)
    p2.SetRightMargin(0.03)

    if getattr( plot, "verticalLabels", False ):
        # Better to make some space in the bottom panel
        p1.SetTopMargin(0.065)
        p1.SetPad(0, 0.35, 1, 1)
        p2.SetPad(0, 0.0, 1, 0.35)
        p2.SetBottomMargin(0.62)

    return c, p1, p2

def get_upper_axis( plot, refhistos ):
    """ Get a histogram for plotting a reasonable upper pad axis """

    haxis = deepcopy( refhistos[0].Clone(f"upperaxis_{plot.name}") )
    haxis.SetTitle("")

    # empty it
    for ibin in range(1, 1+haxis.GetNbinsX()):
        haxis.SetBinContent( ibin, 0 )
        haxis.SetBinError( ibin, 0 )

    maximum = 0 
    for ref in refhistos:
        if isinstance(ref, r.TH1D):
            maximum = max(maximum, ref.GetMaximum())  
        else:
            maximum = max(ref.GetY())  


    alt_max = getattr( plot, "fixYaxis", 0 )
    if alt_max == 0:
        if maximum <= 0:
            return 1.0  # default safe value

        if maximum >= 1.0:
            # Work in log10 space for smooth scaling
            log_max = np.log10(maximum)

            # Map log_max to exponent:
            # - At log10(max) = -3 (0.001) → exponent ~1.5
            # - At log10(max) = 0  (1)    → exponent ~1.3
            # - At log10(max) = 2  (100)  → exponent ~1.1
            # - At log10(max) = 4  (10000)→ exponent ~1.0
            exponent = np.interp(
                log_max,
                [-3, 0, 2, 4, 6],     # log10(max)
                [2.5, 1.6, 1.2, 1.25, 1.10]  # exponent values
            )

            maximum = maximum ** exponent 
            print("maximum: ", maximum )
        else:
            maximum *= 1.8
    else:
        maximum = alt_max
    

    haxis.SetMaximum( maximum )
    if getattr(plot, "fixYaxismin", False):
        haxis.SetMinimum( plot.fixYaxismin )

    haxis.GetXaxis().SetTitleFont(43)
    haxis.GetYaxis().SetTitleFont(43)
    haxis.GetXaxis().SetLabelFont(43)
    haxis.GetYaxis().SetLabelFont(43)
    haxis.GetXaxis().SetLabelSize(0)
    haxis.GetYaxis().SetLabelSize(24)   
    haxis.GetXaxis().SetTitleSize(26)
    haxis.GetYaxis().SetTitleSize(26)
    haxis.GetYaxis().SetTitleOffset(1.8)

    xmin = haxis.GetBinCenter(1)
    xmax = haxis.GetBinCenter( haxis.GetNbinsX() + 1)
    units_per_bin = abs(xmax - xmin)/haxis.GetNbinsX()
    unit = getattr(plot, "unit", "")
    ytitle = getattr( plot, "yTitle", "Events / {0:3.1f} {1}".format( units_per_bin, getattr(plot, "unit", "units") ))
    haxis.GetYaxis().SetTitle( ytitle )

    haxis.GetYaxis().SetMaxDigits(4)

    return haxis

def get_lower_axis( plot, refhistos ):
    """ Get a histogram for plotting a reasonable upper pad axis """
    haxis = deepcopy( refhistos[0].Clone(f"upperaxis_{plot.name}") )
    haxis.SetTitle("")

    # empty it
    for ibin in range(1, 1+haxis.GetNbinsX()):
        haxis.SetBinContent( ibin, 0 )
        haxis.SetBinError( ibin, 0 )

    ratio = getattr( plot, "RatioRange", (0.50, 1.5) )
    haxis.GetYaxis().SetRangeUser( ratio[0], ratio[1] )
    if getattr(plot, "xBinLabels", None):
        for ibin in range(1, 1 + haxis.GetNbinsX() ):
            haxis.GetXaxis().SetBinLabel( ibin, plot.xBinLabels[ibin-1] )
    
    haxis.GetYaxis().SetTitleFont(43)
    haxis.GetXaxis().SetTitleFont(43)
    haxis.GetXaxis().SetLabelFont(43)
    haxis.GetYaxis().SetLabelFont(43)
    haxis.GetXaxis().SetLabelSize(24)
    haxis.GetYaxis().SetLabelSize(24)   
    haxis.GetXaxis().SetTitleSize(24)
    haxis.GetYaxis().SetTitleSize(22)
    haxis.GetYaxis().SetTitleOffset(1.8)
    haxis.GetXaxis().SetTitleOffset(1.1)
    haxis.GetXaxis().SetLabelOffset(0.01)
    haxis.GetYaxis().SetTitle("Data / Pred. ")
    xTitle = getattr(plot, "xTitle", "Title")

    if getattr(plot, "unit", False ):
        xTitle += "~(\mathrm{%s})"%(plot.unit)

    haxis.GetXaxis().SetTitle( xTitle )

    if getattr(plot, "verticalLabels", False):
        haxis.GetXaxis().LabelsOption( "v" )
        haxis.GetXaxis().SetLabelSize(18)
        haxis.GetXaxis().SetLabelOffset(0.06)
        haxis.GetXaxis().SetTitleOffset(1.8)
        

    haxis.GetYaxis().SetNdivisions(503)
    haxis.GetXaxis().SetNdivisions(410)
    haxis.GetYaxis().CenterTitle(True)

    return haxis  



def get_legend( plot, nentries ):
    """ Fixed format for a one column legend """
    corner = plot.getOpt("legend", "TR")
    legendTextSize = 0.046 
    legendColumns = 2 
    leg = r.TLegend(0.42, 0.72, 0.96, 0.905)
    leg.SetFillColorAlpha(0, 0)
    leg.SetShadowColor(0)
    leg.SetLineWidth(0)
    leg.SetTextFont(42)
    leg.SetTextSize(legendTextSize)
    leg.SetNColumns(legendColumns)
    return leg 

import ROOT

def draw_lines_on_hist(hist, plot):
    """
    Draw lines
    """

    lines = []
    
    line_props = getattr( plot, "lines", [] )
    for props in line_props:
        print(props)
        coords_type = props.get("coords", "axis")

        # convertir bin → coordenadas si hace falta
        xaxis = hist.GetXaxis()
        yaxis = hist.GetYaxis()

        def bin_to_x(bin_idx):
            return xaxis.GetBinLowEdge(bin_idx)
        
        def bin_to_y(bin_idx):
            return yaxis.GetBinLowEdge(bin_idx)

        x1 = bin_to_x(props["x1"])
        y1 = bin_to_y(props["y1"])
        x2 = bin_to_x(props["x2"])
        y2 = bin_to_y(props["y2"])

        line = ROOT.TLine(x1, y1, x2, y2)
        line.SetLineColor(props.get("color", ROOT.kBlack))
        line.SetLineStyle(props.get("style", 1))
        line.SetLineWidth(props.get("width", 1))

        lines.append(line)

    return lines


def doSpam(text,x1,y1,x2,y2,align=12,fill=False,textSize=0.033,_noDelete=[]):
  cmsprel = r.TPaveText(x1,y1,x2,y2,"NDC")
  cmsprel.SetTextSize(textSize)
  cmsprel.SetFillColor(0)
  cmsprel.SetFillStyle(1001 if fill else 0)
  cmsprel.SetLineStyle(2)
  cmsprel.SetLineColor(0)
  cmsprel.SetLineWidth(0)
  cmsprel.SetTextAlign(align)
  cmsprel.SetTextFont(43)
  cmsprel.AddText(text)
  cmsprel.Draw("same")
  _noDelete.append( cmsprel ); 
  return cmsprel


