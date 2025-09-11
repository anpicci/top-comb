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
	custom_msg WARN "Quitting..."
	exit 0
}

function list_processes() {
	# Simple function to provide the list of available analyses

	listProcesses=$(find ${TOPCOMB_INPUTS}/${analysis} -mindepth 2 -maxdepth 2 -type d | awk -F '/' '{print $NF}'  )
	select process in ${listProcesses/$TOPCOMB_INPUTS} Quit; do
        case $process in
            Quit)
                quit_setup
                break
                ;;
            *)
		        break
                ;;

        esac

	done

}
