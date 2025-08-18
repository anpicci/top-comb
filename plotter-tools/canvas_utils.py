# Simple macros to create canvases and for plotting stuff
import ROOT as r
from copy import deepcopy

def new_1d_canvas( name ):
    """ Creates a template canvas """
    # --------------- Prepare the basic canvas
    c = r.TCanvas(name, "",  600, 600)
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
    return c, p1, p2

def get_upper_axis( plot, refhistos ):
    """ Get a histogram for plotting a reasonable upper pad axis """
    haxis = deepcopy( refhistos[0].Clone(f"upperaxis_{plot.name}") )
    haxis.SetTitle("")

    # empty it
    for ibin in range(1, 1+haxis.GetNbinsX()):
        haxis.SetBinContent( ibin, 0 )
        haxis.SetBinError( ibin, 0 )

    maximum = max( [ ref.GetMaximum() for ref in refhistos ] )*1.2
    haxis.SetMaximum( maximum )

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
    haxis.GetYaxis().SetTitle( "Events / {0:3.1f} {1}".format( units_per_bin, plot.unit) )
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


    haxis.GetYaxis().SetRangeUser( 0.5, 1.5 )

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
    haxis.GetXaxis().SetTitleOffset(4.3)
    haxis.GetXaxis().SetLabelOffset(0.01)
    haxis.SetTitle("")
    haxis.GetYaxis().SetTitle("EFT/SM.")
    haxis.GetXaxis().SetTitle(plot.xTitle)
    
    haxis.GetYaxis().SetNdivisions(503)
    haxis.GetXaxis().SetNdivisions(410)
    haxis.GetYaxis().CenterTitle(True)

    return haxis  



def get_legend( plot, entries ):
    """ Fixed format for a one column legend """

    ncolumns = getattr(plot, "leg_ncolumns", 1)
    leg_textsize = getattr(plot, "legendTextSize", 0.05616)
    corner = getattr(plot, "corner", "TR")
    nentries = len(entries)
    height = (.20 +  leg_textsize * max(nentries - 3, 0))
    legendWidth = 0.2*(1 + 1.05*ncolumns)

    # fix position: taken from CMGRDF plotter
    if corner == "TR":
        (x1, y1, x2, y2) = (.85 - legendWidth, .9 - height, .90, .91)
    elif corner == "TC":
        (x1, y1, x2, y2) = (.5, .9 - height, .55 + legendWidth, .91)
    elif corner == "TL":
        (x1, y1, x2, y2) = (.2, .9 - height, .25 + legendWidth, .91)
    elif corner == "BR":
        (x1, y1, x2, y2) = (.85 - legendWidth, .16 + height, .90, .15)
    elif corner == "BC":
        (x1, y1, x2, y2) = (.5, .16 + height, .5 + legendWidth, .15)
    elif corner == "BL":
        (x1, y1, x2, y2) = (.2, .16 + height, .2 + legendWidth, .15)
    else:
        raise RuntimeError("Unsupported legend placement %r" % corner)
 
    legend = r.TLegend(x1, y1, x2, y2)
    legend.SetBorderSize(0)
    legend.SetFillColor(0)
    legend.SetShadowColor(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize( leg_textsize )
    legend.SetNColumns( ncolumns )

    return legend 

def doSpam(text,x1,y1,x2,y2,align=12,fill=False,textSize=0.033,_noDelete={}):
  cmsprel = r.TPaveText(x1,y1,x2,y2,"NDC");
  cmsprel.SetTextSize(textSize);
  cmsprel.SetFillColor(0);
  cmsprel.SetFillStyle(1001 if fill else 0);
  cmsprel.SetLineStyle(2);
  cmsprel.SetLineColor(0);
  cmsprel.SetLineWidth(0);
  cmsprel.SetTextAlign(align);
  cmsprel.SetTextFont(43);
  cmsprel.AddText(text);
  cmsprel.Draw("same");
  _noDelete[text] = cmsprel; ## so it doesn't get deleted by PyROOT                                                                                                                    
  return cmsprel
