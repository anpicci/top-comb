inputFile=$1
cp ${inputFile} ${inputFile/.eps/_temp.eps}
sed -i 's/STIXGeneral/STIXGeneraL/g' ${inputFile/.eps/_temp.eps}
ps2pdf -dEmbedAllFontsasdf=true -dEPSCrop ${inputFile/.eps/_temp.eps} ${inputFile/.eps/_temp.pdf}
mv ${inputFile/.eps/_temp.pdf} ${inputFile/.eps/.pdf}
#rm ${inputFile/.eps/_temp.eps}
