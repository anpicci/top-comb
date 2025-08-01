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

	echo -e " >> ${COLOR} ${MSG} ${ENDCOLOR}"
}

function quit_setup() {
	custom_msg WARN "Quitting setup script..."
	exit 0
}

function run_gridpack() {

	custom_msg INFO "Running gridpack. Please select from the available list"

	list=$(find ${TOPCOMB_MG_CARDS}/ -mindepth 1 -maxdepth 1 -type d)
	echo $list
	select process_folder in $list; do
		break
	done

	procname=$(echo $process_folder | awk -F '/' '{print $NF}')
	custom_msg INFO "Generating gridpack for process ${procname}"

	tempdir=temp_cards_${procname}


	# Now actually run the gridpack_generation.sh script	
	pushd $TOPCOMB_GENPRODUCTIONS/bin/MadGraph5_aMCatNLO

	# Clean from previous run
	rm -rf $tempdir
	cp -r $process_folder $tempdir

	# Run the script
	./submit_condor_gridpack_generation.sh $procname $tempdir ${procname}_workdir 
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


