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

function setup_cmgrdf() {
	custom_msg INFO "Setting up environment for reinterpretation"
	custom_msg NC "This is based in the CMGRDF framework."

	# Check the module has been installed
}

# Print a welcome message
custom_msg GOOD "Running the setup for the EFT combination"
custom_msg NC "Please select which step of the setup you would like to run: "

select mode in  Reinterpretation Quit; do
	case $mode in
		Reinterpretation)
			setup_cmgrdf
			break
			;;
		Quit)
			custom_msg WARN "Quitting setup script..."
			break
			;;
	esac
done


