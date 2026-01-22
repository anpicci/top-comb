import ROOT
import os
from utils import get_logger
from plotting.custom_plot_parameters import CustomPlotParameters
logger = get_logger(__name__)

class PlotterBase:
    """Generic plotting workflow — subclasses customize drawing behavior."""
    config = None  # subclasses must define

    @classmethod
    def plot(cls, outfolder, dict_customs, name, **kwargs):
        """General plot routine; subclass defines how to draw main/extra pads."""

        # Main plot
        canvas = cls()._draw( 
            name = name, 
            plot_customizations = CustomPlotParameters.from_dict( 
                dict_customs
            ), 
            **kwargs 
        )        
        
        # Save
        cls().save_canvas(canvas, outfolder, name )

    @classmethod
    def _draw(hists, **kwargs):
        """Subclasses implement: draw main histogram(s)."""
        raise NotImplementedError


    def doSpam(self, text,x1,y1,x2,y2,align=12,fill=False,textSize=0.033,_noDelete=[], color = 1):
        cmsprel = ROOT.TPaveText(x1,y1,x2,y2,"NDC")
        cmsprel.SetTextSize(textSize)
        cmsprel.SetFillColor(0)
        cmsprel.SetFillStyle(1001 if fill else 0)
        cmsprel.SetLineStyle(2)
        cmsprel.SetLineColor(0)
        cmsprel.SetFillColor( color )
        cmsprel.SetLineWidth(0)
        cmsprel.SetTextAlign(align)
        cmsprel.SetTextFont(43)
        cmsprel.AddText(text)
        cmsprel.Draw("same")
        _noDelete.append( cmsprel ); 
        return cmsprel

    def print_spam( self, spams ):
        for metaspam in spams:
            self.doSpam(
                metaspam["text"],
                metaspam["x0"],
                metaspam["y0"],
                metaspam["x1"],
                metaspam["y1"],
                textSize = metaspam["textsize"],
                color = 1
            )

    def save_canvas(self, canvas, outfolder, output_name):
        #canvas.Update()
        for ext in [".png", ".eps"]:
            canvas.SaveAs( os.path.join( outfolder, output_name + ext) )

        base_outfolder = str(outfolder).split("/")[:-1]
        # Now run the scripts to make the plots readable from html
        os.system( f"utils/eps_to_pdf_for_latex.sh {outfolder}/{output_name}.eps")
        #os.system( "find %s -type d -exec cp -n utils/index.php {} \\;"%base_outfolder)

