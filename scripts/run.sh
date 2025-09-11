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


function prepare_genproductions() {
	custom_msg INFO "Running MG. Please select a process from the available list"
    tag=$1
	
	# Get the list of analyses
	list_processes

	processDir=$(find ${TOPCOMB_INPUTS}/ -name $process -type d)
    analysisDir=$( echo $(dirname $processDir) | awk -F'/' '{print $NF}' )
	
	custom_msg INFO "Generating madgraph feynman diagrams for process ${process}"
	# Prepare the submission folder
	SUBMISSION_DIR=submit_${tag}_${process}
	rm -rf $SUBMISSION_DIR; mkdir -p $SUBMISSION_DIR

	# Prepare the cards and scripts from genproductions
	tempdir=temp_cards_${process}

	pushd $SUBMISSION_DIR
	cp -r $processDir/mgcards $tempdir
	cp -r $TOPCOMB_MAINPATH/templates/index.php . 
	tar -zcvf cards.tgz $tempdir

}

function run_diagrams() {
    prepare_genproductions diagrams

	cp $TOPCOMB_MAINPATH/templates/generate_diagrams.sh .
 	sed -i "s|__PROCNAME__|$process|g" generate_diagrams.sh
 	sed -i "s|__ANALYSIS_NAME__|$analysisDir|g" generate_diagrams.sh
 	sed -i "s|__CARDSDIR__|$tempdir|g" generate_diagrams.sh
 	sed -i "s|__OUTPATH__|$TOPCOMB_OUTPATH|g" generate_diagrams.sh
 	sed -i "s|__SINGULARITY_IMAGE__|$SINGULARITY_IMAGE_GRIDPACK|g" generate_diagrams.sh
 	sed -i "s|__GENPRODUCTIONS_GRIDPACK__|$GENPRODUCTIONS_GRIDPACK|g" generate_diagrams.sh
 	sed -i "s|__BRANCH_GRIDPACK__|$BRANCH_GRIDPACK|g" generate_diagrams.sh
	chmod +x generate_diagrams.sh

	# Now copy the jds
	cp $TOPCOMB_MAINPATH/templates/template_submit.jds generate_diagrams.jds
 	sed -i "s|__SCRIPTNAME__|generate_diagrams.sh|g" generate_diagrams.jds
 	sed -i "s|__PROCNAME__|${process}_genFD|g" generate_diagrams.jds
 	sed -i "s|__NCORES__|1|g" generate_diagrams.jds
	popd

	# Prompt the command to submit the job
	custom_msg WARN ">> Use the following command to submit the job"
	custom_msg NC "cd $SUBMISSION_DIR/ ; condor_submit generate_diagrams.jds; cd -"
	custom_msg WARN "-------------------------------------------- "

}

function run_gridpack() {
    prepare_genproductions gridpack
	
	cp $TOPCOMB_MAINPATH/templates/run_gridpack_batch.sh .
 	sed -i "s|__PROCNAME__|$process|g" run_gridpack_batch.sh
 	sed -i "s|__ANALYSIS_NAME__|$analysisDir|g" run_gridpack_batch.sh
 	sed -i "s|__CARDSDIR__|$tempdir|g" run_gridpack_batch.sh
 	sed -i "s|__OUTPATH__|$TOPCOMB_OUTPATH|g" run_gridpack_batch.sh
 	sed -i "s|__SINGULARITY_IMAGE__|$SINGULARITY_IMAGE_GRIDPACK|g" run_gridpack_batch.sh
 	sed -i "s|__GENPRODUCTIONS_GRIDPACK__|$GENPRODUCTIONS_GRIDPACK|g" run_gridpack_batch.sh
 	sed -i "s|__BRANCH_GRIDPACK__|$BRANCH_GRIDPACK|g" run_gridpack_batch.sh
	chmod +x run_gridpack_batch.sh

	# Now copy the jds
	cp $TOPCOMB_MAINPATH/templates/template_submit.jds run_gridpack_batch.jds
 	sed -i "s|__SCRIPTNAME__|run_gridpack_batch.sh|g" run_gridpack_batch.jds
 	sed -i "s|__PROCNAME__|${process}_runGridpack|g" run_gridpack_batch.jds
 	sed -i "s|__NCORES__|8|g" run_gridpack_batch.jds

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
    #if [[ $process == "*Quit*" ]]; then quit_setup; fi
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

select mode in  Diagrams Gridpack Nanogen Quit; do
	case $mode in
		Diagrams)
			run_diagrams
			break
			;;
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


