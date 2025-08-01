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

	custom_msg INFO "Running gridpack. Please select an analysis from the available list"
	listAnalyses=$(find ${TOPCOMB_ANALYSES} -type d -name "mgcards" | awk -F '/' '{print $(NF-1)}'  )

	select analysis in ${listAnalyses/$TOPCOMB_ANALYSES/}; do
		break
	done


	listProcesses=$(find ${TOPCOMB_ANALYSES}/${analysis}/mgcards -mindepth 1 -type d | awk -F '/' '{print $NF}'  )
	custom_msg WARN "Analysis $analysis has the following processes: " 
	select process in ${listProcesses/$TOPCOMB_ANALYSES}; do
		break
	done

	custom_msg INFO "Generating gridpack for process ${process}"

	tempdir=temp_cards_${process}

	# Now actually run the gridpack_generation.sh script	
	pushd $TOPCOMB_GENPRODUCTIONS/bin/MadGraph5_aMCatNLO

	# Clean from previous run
	rm -rf $tempdir
	cp -r $TOPCOMB_ANALYSES/$analysis/mgcards/$process/ $tempdir

	# Do a few checks
	check_cards_before_gridpack $tempdir

	# Run the script
	./submit_condor_gridpack_generation.sh $process $tempdir ${process}_workdir 
	popd
		
}



# Print a welcome message
custom_msg GOOD "Running the workflow for the EFT combination"
custom_msg NC "Please select which step of the setup you would like to run: "

select mode in  Gridpack  Quit; do
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


