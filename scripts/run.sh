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

	popd
	# Prompt the command to submit the job
	custom_msg WARN ">> Use the following command to submit the job"
	custom_msg NC "cd $SUBMISSION_DIR/ ; condor_submit run_gridpack_batch.jds; cd -"
	custom_msg WARN "-------------------------------------------- "

}

function run_nanogen() {
	custom_msg INFO "Running nanogen. Please select a process from the available list"
	
	# Get the list of analyses
	list_processes

	analysisDir=$(find ${TOPCOMB_INPUTS}/ -name $process -type d)
	
	custom_msg INFO "Generating nanogen for process ${process}"

	# Prompt the command to submit the job
	custom_msg WARN ">> Use the following command to submit the job"
	custom_msg WARN "NOTE: modify the contents of the json if you want to change anything on the generation side."
	custom_msg NC "python3 tmg-tools/top-gendqm/run_validation.py --parse_from_json ${analysisDir/$PWD/\.}/nanogen_config.json "
	custom_msg WARN "-------------------------------------------- "

}

# Print a welcome message
custom_msg GOOD "Running the workflow for the EFT combination"
custom_msg NC "Please select which step of the setup you would like to run: "

select mode in  Gridpack Nanogen Quit; do
	case $mode in
		Gridpack)
			run_gridpack
			break
			;;
		Nanogen)
			run_nanogen
			break
			;;
		Quit)
			quit_setup	
			break
			;;
	esac
done


