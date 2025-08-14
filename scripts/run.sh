# Scripts for setting up the environment

source scripts/utils.sh

function check_cards_before_gridpack() {

	# Just some extremely handcrafted checks to look before submitting the gridpack
	custom_msg WARN "You are about to generate a gridpack with the following content:"

	custom_msg NC "---------------"

	custom_msg WARN "Process card:"
	custom_msg NC "+++++++++++++++"
	cat $1/*proc_card.dat

	custom_msg WARN "Relevant run parameters"
	custom_msg NC "+++++++++++++++"
	custom_msg NC "ebeam = $(grep ebeam1 $1/*run_card.dat | tr -d ':blank:' | awk -F '=' '{print $1}')"
	custom_msg NC "xqcut = $(grep 'minimum kt' $1/*run_card.dat | tr -d ':blank:' | awk -F '=' '{print $1}') (only relevant for merged samples)"

}

function run_gridpack() {
	custom_msg INFO "Running gridpack. Please select a process from the available list"
	
	# Get the list of analyses
	list_processes

	analysisDir=$(find ${TOPCOMB_INPUTS}/ -name $process -type d)
	
	custom_msg INFO "Generating gridpack for process ${process}"
	# Prepare the submission folder
	SUBMISSION_DIR=submit_gridpack_${process}
	rm -rf $SUBMISSION_DIR; mkdir -p $SUBMISSION_DIR

	# Prepare the cards and scripts from genproductions
	tempdir=temp_cards_${process}

	pushd $SUBMISSION_DIR
	cp -r $analysisDir/mgcards $tempdir
	tar -zcvf cards.tgz $tempdir
	check_cards_before_gridpack $tempdir


	cp $TOPCOMB_MAINPATH/templates/run_gridpack_batch.sh .
 	sed -i "s|__PROCNAME__|$process|g" run_gridpack_batch.sh
 	sed -i "s|__CARDSDIR__|$tempdir|g" run_gridpack_batch.sh
 	sed -i "s|__OUTPATH__|$TOPCOMB_OUTPATH|g" run_gridpack_batch.sh
 	sed -i "s|__SINGULARITY_IMAGE__|$SINGULARITY_IMAGE_GRIDPACK|g" run_gridpack_batch.sh
 	sed -i "s|__GENPRODUCTIONS_GRIDPACK__|$GENPRODUCTIONS_GRIDPACK|g" run_gridpack_batch.sh
 	sed -i "s|__BRANCH_GRIDPACK__|$BRANCH_GRIDPACK|g" run_gridpack_batch.sh
	chmod +x run_gridpack_batch.sh

	# Now copy the jds
	cp $TOPCOMB_MAINPATH/templates/run_gridpack_batch.jds .
 	sed -i "s|__PROCNAME__|$process|g" run_gridpack_batch.jds
	condor_submit run_gridpack_batch.jds

	popd
}


# Print a welcome message
custom_msg GOOD "Running the workflow for the EFT combination"
custom_msg NC "Please select which step of the setup you would like to run: "

select mode in  Gridpack Generate Quit; do
	case $mode in
		Gridpack)
			run_gridpack
			break
			;;
		Quit)
			quit_setup	
			break
			;;
	esac
done


