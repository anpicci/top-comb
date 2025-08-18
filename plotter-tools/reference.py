""" 
Script to remake plots produced by CMGRDF 
"""
import os, sys, re
import argparse
from copy import deepcopy
import ROOT as r
from collections import OrderedDict
r.gStyle.SetOptStat(0)
r.gROOT.SetBatch(1)
r.gStyle.SetPadTickX(1)
r.gStyle.SetPadTickY(1)

def add_parsing_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fd', '-f', dest = "fd", help = "Path to fitDiagnostics")
    parser.add_argument('--inputFolder', '-i', dest = "inputFolder", help = "Path to folder with postfit distributions")
    parser.add_argument('--outname', '-o', dest = "outname", default = "plots", help = "plots")
    parser.add_argument('--plot-only-this', '-p', dest = "plot_this", default = "", help = "Plot only this variable")
    parser.add_argument('--year', '-y', dest = "year", default = "all", help = "To select the luminosity value.")
    parser.add_argument('--preliminary', dest = "preliminary", default = False, action = "store_true", help = "To select the label.")
    return parser.parse_args()

def color_msg(msg, color = "none", indentlevel=0):
    """ Prints a message with ANSI coding so it can be printout with colors """
    codes = {
        "none" : "0m",
        "green" : "1;32m",
        "red" : "1;31m",
        "blue" : "1;34m",
        "yellow" : "1;33m"
    }

    if indentlevel == 0: indentSymbol=">> "
    if indentlevel == 1: indentSymbol="+ "
    if indentlevel == 2: indentSymbol="* "

    indent = indentlevel*" " + indentSymbol
    print("\033[%s%s%s \033[0m"%(codes[color], indent, msg))
    return

def integrate(histograms):
    """ Reads a dictionary and integrates histograms according to keys """
    summed = {}
    for proc, histos in histograms.items():
        # Grab the first one
        h0 = deepcopy( histos[0].Clone( "{0}_SUM".format( proc )) )

        # Go summing up the rest
        for h in histos[1:]:
            h0.Add( h )

        summed[proc] = h0
    return summed

def get_histograms( inputFile, shapedir, year = "all" ):
    """ Grab all histograms from fitDiagnostics and split them by channels """
    rfile = r.TFile.Open( inputFile )

    # Get all the interesting keys from the file. This essentially fetches years and channels
    channels = filter( lambda key: shapedir in key.GetName() and key.GetName() != shapedir, rfile.GetListOfKeys() ) 

    # Start building histograms. Format will be:
    # { 
    #  "proc" : [channel0, channel1, channel2, ...]
    # }

    shapes = {}
    # Get all the histograms
    for key in channels:
        channel = rfile.Get( key.GetName() )
        channel.cd()
        for proc_key in channel.GetListOfKeys():
            # These are handled differently because we have to make sure we use the ones produced by combine,
            # since those are the ones that have been propagated using the covariance matrix.

            if proc_key.GetName() in ["TotalProcs"]:
                    h = channel.Get( "TotalProcs" )
                    #print( channel.GetName(), "Bin content: {0} +/- {1}".format(h.GetBinContent(1), h.GetBinError(1)))

            if proc_key.GetName() in ["data_obs", "TotalBkg", "TotalSig", "TotalProcs"]: continue 
            if proc_key.GetName() not in shapes:
                shapes[ proc_key.GetName() ] = [ channel.Get( proc_key.GetName() ) ]
            else:
                shapes[ proc_key.GetName() ].append( channel.Get( proc_key.GetName() ) )
            
            
            #if channel.Get( proc_key.GetName() ).GetBinContent(ibin) > 0.1: 
            #print( "   ", channel.GetName(), "{2} - Bin content: {0:2f} +/- {1:2f}".format(channel.Get( proc_key.GetName() ).GetBinContent(1), channel.Get( proc_key.GetName()).GetBinError(1), proc_key.GetName()))
                

    # Now integrate all histograms into one
    summed = integrate( shapes )

    # Now use the prefit/postfit directories to fetch the total and data histograms
    shapes_summedByCombine = rfile.Get( shapedir )
    shapes_summedByCombine.cd()

    # Data comes in histogram, we want to convert it into a TGraph
    data_h = deepcopy( shapes_summedByCombine.Get( "data_obs" ).Clone("data_obs_COMBINE") )
    data_h.SetBinErrorOption(r.TH1.kPoisson)

    """
    for i in range(1, 1+data_h.GetNbinsX()):
        print(i, data_h.GetBinErrorUp(i), data_h.GetBinErrorLow(i), data_h.GetBinError(i))
        #if data_h.GetBinContent( i ) == 0: # this is only applied to mll_3l_ee and mll_3l_mm
            #data_h.SetBinError( i, 1.84102164458 )
    """
    data_gr = r.TGraphErrors( data_h.GetNbinsX() )

    #"""
    alpha = 1 - 0.6827
    data_gr.SetName(" data_obs_COMBINE_gr" )

    for ibin in range(1, 1+data_h.GetNbinsX() ):
        data_gr.SetPoint(ibin-1, data_h.GetBinCenter(ibin), data_h.GetBinContent(ibin) )
       
        if data_h.GetBinContent(ibin) < 1.0:
            data_gr.SetPointError(ibin-1, 0, data_h.GetBinError(ibin) )
        else:
            data_gr.SetPointError(ibin-1, 0, data_h.GetBinErrorUp(ibin))
            """
            N = data_gr.GetY()[ ibin - 1  ]
            L = 0 if N == 0 else r.Math.gamma_quantile( alpha/2, N, 1. ) 
            U = r.Math.gamma_quantile( alpha/2, N+1, 1 )
            data_gr.SetPointError( ibin-1, 0, U - N )
            print( ibin , N, U, U - N, data_gr.GetErrorYlow(ibin-1), data_gr.GetErrorYhigh(ibin-1) )
            """
    #"""

    summed["data_obs"]  = data_gr
    summed["total"] = deepcopy( shapes_summedByCombine.Get( "TotalProcs" ).Clone("totalProcs_COMBINE") )
    
    
    #print( "total", "Bin content: {0} +/- {1}".format(summed["total"].GetBinContent(1), summed["total"].GetBinError(1)))
    return shapes, summed 

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


def new_canvas( name ):
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

def draw_stack( hstack, cfgplot ):
    """ Modify parameters of the hstack """
    hstack.Draw("hist")

    if cfgplot.force_y_max == None:
        hstack.GetYaxis().SetRangeUser( 0, max( hstack.GetMaximum(), data.GetMaximum() )*cfgplot.ScaleUpperY )
        hstack.SetMaximum( max( hstack.GetMaximum(), data.GetMaximum() )*cfgplot.ScaleUpperY )
    else:
        hstack.GetYaxis().SetRangeUser( 0, cfgplot.force_y_max )
        hstack.SetMaximum( cfgplot.force_y_max )

    if cfgplot.rangex != None:
        hstack.GetXaxis().SetRangeUser( cfgplot.rangex[0], cfgplot.rangex[1] )
    
    hstack.GetXaxis().SetTitleFont(43)
    hstack.GetYaxis().SetTitleFont(43)
    hstack.GetXaxis().SetLabelFont(43)
    hstack.GetYaxis().SetLabelFont(43)
    
    
    hstack.GetXaxis().SetLabelSize(0)
    hstack.GetYaxis().SetLabelSize(24)   
    hstack.GetXaxis().SetTitleSize(26)
    hstack.GetYaxis().SetTitleSize(26)

    hstack.GetYaxis().SetTitleOffset(1.8)

    # Now for the title y:
    if cfgplot.unit == None:
        hstack.GetYaxis().SetTitle( cfgplot.titleY )
    else:
        # Get the binning
        
        xmin = hstack.GetHistogram().GetBinCenter(1)
        xmax = hstack.GetHistogram().GetBinCenter( hstack.GetHistogram().GetNbinsX() + 1)
        units_per_bin = abs(xmax - xmin)/hstack.GetHistogram().GetNbinsX()
        
        hstack.GetYaxis().SetTitle( "Events / {0:3.1f} {1}".format( units_per_bin, cfgplot.unit) )
    
    hstack.GetYaxis().SetMaxDigits(4)

def draw_data( data ):

    """ Draws the data TGraph """
    data.Draw("pe0 same")
    data.SetLineColor(1)
    data.SetFillColor(0)
    data.SetMarkerColor(1)
    data.SetMarkerStyle(20)

def draw_unc( total ):
    """ Draws the uncertainty band """
    total.Draw("e2 same")
    total.SetFillStyle(3444)
    total.SetFillColor(r.kGray+2)
    total.SetMarkerStyle(0)
    total.SetMarkerColor(920)
    total.SetLineWidth(0)

def draw_ratio( ratio, cfgplot ):
    """ Draws the ratio distributions """
    htotalNoErr = deepcopy(total.Clone("ratiounc"))
    htotalErr = deepcopy(total.Clone("ratiouncErr"))

    for ibin in range(1, htotalNoErr.GetNbinsX()+1):
        htotalNoErr.SetBinError(ibin, 0)
        ratio.SetPoint(ibin-1, ratio.GetX()[ibin-1], summed["data_obs"].GetY()[ibin-1] / htotalNoErr.GetBinContent(ibin) ) 
        ratio.SetPointError(ibin-1, 0, summed["data_obs"].GetErrorY(ibin-1) / htotalNoErr.GetBinContent(ibin) ) 
        print("Ratio (ibin: {0}) = ".format(ibin), ratio.GetErrorY(ibin-1))
    htotalErr.Divide(htotalNoErr)

    htotalErr.GetYaxis().SetRangeUser( cfgplot.ymin_ratio, cfgplot.ymax_ratio )
    if cfgplot.rangex != None:
        htotalErr.GetXaxis().SetRangeUser( cfgplot.rangex[0], cfgplot.rangex[1] )

    if cfgplot.binlabels != []:
        for ibin in range(1, 1+htotalErr.GetNbinsX() ):
            htotalErr.GetXaxis().SetBinLabel( ibin, cfgplot.binlabels[ibin-1] )
    
    htotalErr.GetYaxis().SetTitleFont(43)
    htotalErr.GetXaxis().SetTitleFont(43)
    htotalErr.GetXaxis().SetLabelFont(43)
    htotalErr.GetYaxis().SetLabelFont(43)
    
    htotalErr.GetXaxis().SetLabelSize(26) # change
    htotalErr.GetYaxis().SetLabelSize(26) # change 
    htotalErr.GetXaxis().SetTitleSize(24)
    htotalErr.GetYaxis().SetTitleSize(26)

    htotalErr.GetYaxis().SetTitleOffset(1.8)
    htotalErr.GetXaxis().SetTitleOffset(4.3)
    htotalErr.GetXaxis().SetLabelOffset(0.01)

    

    htotalErr.SetTitle("")
    htotalErr.GetYaxis().SetTitle("Data / Pred.     ")
    htotalErr.GetXaxis().SetTitle(cfgplot.titleX)
    
    htotalErr.GetYaxis().SetNdivisions(503)
    htotalErr.GetXaxis().SetNdivisions(410)
    htotalErr.GetYaxis().CenterTitle(True)

    return htotalErr, ratio  

groups_per_region = {
    "srwz" : OrderedDict(),
    "crzz" : OrderedDict(),
    "crtt" : OrderedDict(),
    "crconv" : OrderedDict(),
}

# ---- SRWZ     
#groups_per_region["srwz"]["VVV"]        = { "processes" : ["prompt_VVV"], "color" : r.TColor.GetColor(169,107,87) }
#groups_per_region["srwz"]["tZq"]        = { "processes" : ["prompt_TZQ"], "color" : r.TColor.GetColor(150,74,139), }
#groups_per_region["srwz"]["Nonprompt"]  = { "processes" : ["fakes"], "color" : r.TColor.GetColor(113,117,129) }
groups_per_region["srwz"]["Other"]       = { "processes" : ["fakes", "prompt_TZQ", "prompt_VVV"],  "color" : r.TColor.GetColor(148,164,162)  }
groups_per_region["srwz"]["ttX"]         = { "processes" : ["prompt_TTX"], "color" : r.TColor.GetColor(131,45,182), "special_name" : "t#bar{t}X" }
groups_per_region["srwz"]["X#gamma"]    = { "processes" : ["convs"], "color" : r.TColor.GetColor(231,99,0) }
groups_per_region["srwz"]["ZZ"]          = { "processes" : ["prompt_ggZZ", "prompt_ZZ"],           "color" : r.TColor.GetColor(63,144,218), "special_name" : "ZZ" }
groups_per_region["srwz"]["WZ"]          = { "processes" : ["prompt_WZ", "prompt_WZ_nonfiducial"], "color" : r.TColor.GetColor(255,169,14) }   

# ---- CRZZ     
#groups_per_region["crzz"]["VVV"]        = { "processes" : ["prompt_VVV"], "color" : r.TColor.GetColor(169,107,87) }
#groups_per_region["crzz"]["tZq"]        = { "processes" : ["prompt_TZQ"], "color" : r.TColor.GetColor(150,74,139), }
#groups_per_region["crzz"]["Nonprompt"]  = { "processes" : ["fakes"], "color" : r.TColor.GetColor(113,117,129) }
#groups_per_region["crzz"]["ttX"]         = { "processes" : ["prompt_TTX"], "color" : r.TColor.GetColor(131,45,182), "special_name" : "t#bar{t}X" }
#groups_per_region["crzz"]["X#gamma"]    = { "processes" : ["convs"], "color" : r.TColor.GetColor(231,99,0) }
groups_per_region["crzz"]["Other"]       = { "processes" : ["fakes", "prompt_TZQ", "prompt_VVV", "prompt_TTX", "convs", "prompt_WZ", "prompt_WZ_nonfiducial"],  "color" : r.TColor.GetColor(148,164,162)  }
groups_per_region["crzz"]["ggZZ"]        = { "processes" : ["prompt_ggZZ"], "color" : r.TColor.GetColor(146,218,221), "special_name" : "gg#rightarrowZZ" }
groups_per_region["crzz"]["qqZZ"]        = { "processes" : ["prompt_ZZ"], "color" : r.TColor.GetColor(63,144,218), "special_name" : "qq#rightarrowZZ" }
#groups_per_region["crzz"]["WZ"]          = { "processes" : ["prompt_WZ", "prompt_WZ_nonfiducial"], "color" : r.TColor.GetColor(255,169,14) }   

# ---- CRTT     
#groups_per_region["crtt"]["VVV"]         = { "processes" : ["prompt_VVV"], "color" : r.TColor.GetColor(169,107,87) }
#groups_per_region["crtt"]["X#gamma"]    = { "processes" : ["convs"], "color" : r.TColor.GetColor(231,99,0) }
#groups_per_region["crtt"]["ZZ"]          = { "processes" : ["prompt_ggZZ", "prompt_ZZ"],           "color" : r.TColor.GetColor(63,144,218), "special_name" : "ZZ" }
groups_per_region["crtt"]["Other"]       = { "processes" : ["prompt_VVV", "convs", "prompt_ggZZ", "prompt_ZZ"],  "color" : r.TColor.GetColor(148,164,162)  }
groups_per_region["crtt"]["Non-prompt"]   = { "processes" : ["fakes"], "color" : r.TColor.GetColor(113,117,129) }
groups_per_region["crtt"]["tZq"]         = { "processes" : ["prompt_TZQ"], "color" : r.TColor.GetColor(150,74,139)}
groups_per_region["crtt"]["ttX"]         = { "processes" : ["prompt_TTX"], "color" : r.TColor.GetColor(131,45,182), "special_name" : "t#bar{t}X" }
groups_per_region["crtt"]["WZ"]          = { "processes" : ["prompt_WZ", "prompt_WZ_nonfiducial"], "color" : r.TColor.GetColor(255,169,14) }  

# ---- CRXG     
#groups_per_region["crconv"]["VVV"]       = { "processes" : ["prompt_VVV"], "color" : r.TColor.GetColor(169,107,87) }
#groups_per_region["crconv"]["tZq"]       = { "processes" : ["prompt_TZQ"], "color" : r.TColor.GetColor(150,74,139), }
#groups_per_region["crconv"]["Nonprompt"] = { "processes" : ["fakes"], "color" : r.TColor.GetColor(113,117,129) }
#groups_per_region["crconv"]["ttX"]        = { "processes" : ["prompt_TTX"], "color" : r.TColor.GetColor(131,45,182), "special_name" : "t#bar{t}X" }
groups_per_region["crconv"]["Other"]      = { "processes" : ["fakes", "prompt_TZQ", "prompt_VVV", "prompt_TTX"],  "color" : r.TColor.GetColor(148,164,162)  }
groups_per_region["crconv"]["X#gamma"]   = { "processes" : ["convs"], "color" : r.TColor.GetColor(231,99,0) }
groups_per_region["crconv"]["ZZ"]         = { "processes" : ["prompt_ggZZ", "prompt_ZZ"],           "color" : r.TColor.GetColor(63,144,218), "special_name" : "ZZ" }
groups_per_region["crconv"]["WZ"]         = { "processes" : ["prompt_WZ", "prompt_WZ_nonfiducial"], "color" : r.TColor.GetColor(255,169,14) }   


region_labels = {
    "srwz" : "WZ SR",
    "crzz" : "ZZ CR",
    "crtt" : "t#bar{t}Z CR",
    "crconv" : "X#gamma CR"
}

if __name__ == "__main__":
    
    lumis = {
        "2022" : 8.0,
        "2022EE" : 26.7,
        "all" : 34.7
    }
    # 1. First step, grab all histograms from input cards
    opts = add_parsing_options()
    
    fd = opts.fd
    inputFolder = opts.inputFolder
    outname = opts.outname
    plot_this = opts.plot_this
    year = opts.year 
    prel = opts.preliminary

    if prel:
        from plot_configs_preliminary import plots
    else:
        from plot_configs import plots
    color_msg("Producing postfit plots from {0}".format( inputFolder ), color = "green", indentlevel = 0)

    # Get a list of variables:
    variables = os.listdir( inputFolder )
    regions = region_labels.keys()

    for reg in regions:
        if reg != "crzz": continue
        for variable in variables:
            if variable != "lepW_pt": continue
            inputFile = os.path.join( inputFolder, variable, reg, "wz_OUT.root" )
            if not os.path.isfile( inputFile ):
                color_msg("Skipping {0} in {1} because {2} does not exist.".format( variable, reg, inputFile ), color = "yellow", indentlevel = 1)
                continue
    
            # Get the plot configs

            if plot_this != "" and variable != plot_this: continue
            cfgplot = deepcopy(plots[ variable ])
            cfgplot.modify( reg )


            for shapedir in [ "prefit", "postfit" ]:
                entries_legend = []

                color_msg( "Making plots for {0}: {1}".format( shapedir, inputFile ), color = "green" )

                # Get histograms from the cards
                shapes, summed = get_histograms( 
                    inputFile = inputFile, 
                    shapedir = shapedir, 
                    year = year
                )

                c, p1, p2 = new_canvas( "canvas_{0}".format( shapedir ) )
                
                

                # Now we have to group them further for the plot
                hstack = r.THStack()
                groups = groups_per_region[reg]
                for group, group_info in groups.items():
                    # Get a subset dictionary with th          = e processes and sum them
                    color_msg( "Process {0}".format( group ), color = "none", indentlevel = 1 )

                    sub_dict = { group : [ summed[proc] for proc in group_info["processes"] if proc in summed ] }
                    
                    if sub_dict[group] == []: 
                        color_msg( "Skipping process {0} because it has 0 entries".format( group ), color = "yellow", indentlevel = 2 )
                        continue
                    summed_group = integrate( sub_dict )

                    # apply some very basic cosmetics
                    summed_group[group].SetFillColor( group_info["color"].GetNumber() )
                    summed_group[group].SetMarkerSize(0)
                    summed_group[group].SetLineWidth(1)
                    summed_group[group].SetLineColor(1)
                    summed_group[group].GetXaxis().SetLabelSize(0)
                    summed_group[group].SetLineWidth(0)

                    # Now update the histogram dictionary
                    for proc in group_info["processes"]: 
                        if proc in group_info:
                            summed.pop( proc ) 
                    summed[group] = deepcopy( summed_group[group].Clone("{0}_forStack".format( group ) ) )

                    # Finally, stack them
                    hstack.Add( summed[group] )


                    entries_legend.append( (summed[group], group if "special_name" not in group_info else group_info["special_name"], "f") )

                # Get the data, uncertainty and ratio distributions
                data  = summed["data_obs"]
                total = summed["total"]
                entries_legend.append( (summed["total"], "Uncertainty", "ef") )
                entries_legend.append( (summed["data_obs"], "Data", "pe") )
                #for ibin in range(1, 1+summed[group].GetNbinsX() ):
                    #print( "content bin {0} -- Predict: {1} Data: {2} Ratio data/predict: {3}".format( ibin, summed["total"].GetBinContent(ibin), summed["data_obs"].GetY()[ibin-1], summed["data_obs"].GetY()[ibin-1]/summed["total"].GetBinContent(ibin) ) ) 

                #print("Integrals: data: {0}, MC: {1}, signal: {2}, fakes: {3}".format( sum(data.GetY()), total.Integral(), summed["WZ"].Integral(), summed["Other"].Integral() ) ) 
                legend = cfgplot.get_legend( entries_legend )
                entries_legend.reverse()
                for entry in entries_legend:
                    #if entry[0].Integral() < 10: continue
                    legend.AddEntry( entry[0], entry[1], entry[2] )

                
                # Now start drawing stuff
                # ------------- Upper pad
                p1.cd()
                draw_stack( hstack, cfgplot )
                draw_data( data )
                draw_unc( total )
                legend.Draw("same")

                # Draw labels
                
                for spam, metaspam in cfgplot.spams.items():

                    text = metaspam["text"]
                    text = text.replace( "__FITLABEL__", "Prefit" if shapedir == "prefit" else "Postfit" )
                    text = text.replace( "__REGIONLABEL__", region_labels[reg])
                    text = text.replace( "__LUMI__", "{0}".format(lumis[year]))
                    doSpam( text, metaspam["x0"], metaspam["y0"], metaspam["x1"], metaspam["y1"], textSize = metaspam["textsize"])


                p2.cd()
                ratio = deepcopy( data.Clone( "axis_{0}".format(variable) ) )
                htotalErr, ratio = draw_ratio( ratio, cfgplot )
                htotalErr.GetXaxis().SetTickLength(0.24 * (p2.GetWh() * p2.GetAbsHNDC()) / (p1.GetWh() * p1.GetAbsHNDC()))

                #print("Total ratio: {0}".format( sum(ratio.GetY())/len(ratio.GetY()) ) ) 
                # For some reason root deletes these 
                htotalErr.Draw("e2")
                ratio.Draw("pe0 same")  
                


            
                if not os.path.exists( outname + "/{0}".format(year) ):
                    os.system("mkdir -p {0}".format( outname + "/{0}".format(year) ))
                
                c.SaveAs( os.path.join( outname + "/{0}".format(year), "{0}_{1}_{2}.png".format( reg, variable, shapedir)) )
                c.SaveAs( os.path.join( outname + "/{0}".format(year), "{0}_{1}_{2}.eps".format( reg, variable, shapedir)) )
                c.SaveAs( os.path.join( outname + "/{0}".format(year), "{0}_{1}_{2}.pdf".format( reg, variable, shapedir)) )
        
