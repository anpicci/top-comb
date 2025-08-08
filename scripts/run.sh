# Scripts for setting up the environment

# Set of colors for prompts
function custom_msg() {
	ERROR="\e[31m" # red
	GOOD="\e[32m" # green 
	INFO="\e[34m" # blue
	WARN="\e[93m" # yellow
	ENDCOLOR="\e[0m"

	MSG_TYPE=$1
	case $MSG_TYPE in
		ERROR) COLOR=$ERROR;;
		GOOD) COLOR=$GOOD;;
		INFO) COLOR=$INFO;;
		WARN) COLOR=$WARN;;
		*) COLOR=$ENDCOLOR;;
	esac
	MSG=$2

	echo -e "${COLOR} ${MSG} ${ENDCOLOR}"
}

function quit_setup() {
	custom_msg WARN "Quitting setup script..."
	exit 0
}

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
	
	listProcesses=$(find ${TOPCOMB_ANALYSES}/${analysis} -mindepth 2 -maxdepth 2 -type d | awk -F '/' '{print $NF}'  )
	select process in ${listProcesses/$TOPCOMB_ANALYSES}; do
		break
	done

	analysisDir=$(find ${TOPCOMB_ANALYSES}/ -name $process -type d)
	
	custom_msg INFO "Generating gridpack for process ${process}"
	# Prepare the submission folder
	SUBMISSION_DIR=submit_gridpack_${process}
	rm -rf $SUBMISSION_DIR; mkdir -p $SUBMISSION_DIR

	# Prepare the cards and scripts from genproductions
	tempdir=temp_cards_${process}

	pushd $SUBMISSION_DIR
	cp -r $analysisDir/mgcards $tempdir
	check_cards_before_gridpack $tempdir


	cp $TOPCOMB_MAINPATH/templates/run_gridpack_batch.sh .
 	sed -i "s|__PROCNAME__|$process|g" run_gridpack_batch.sh
 	sed -i "s|__CARDSDIR__|$tempdir|g" run_gridpack_batch.sh
 	sed -i "s|__OUTPATH__|$TOPCOMB_OUTPATH|g" run_gridpack_batch.sh
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
		Generate)
			run_generation
			break
			;;
		Quit)
			quit_setup	
			break
			;;
	esac
done


